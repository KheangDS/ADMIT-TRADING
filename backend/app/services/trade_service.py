"""Transactional staging, naming review, revision creation and publication scope."""
from pathlib import Path
from hashlib import sha256
from decimal import Decimal
from uuid import uuid4
import re
import os
import json
import gzip
import base64
import pandas as pd
from fastapi import HTTPException
from sqlalchemy import select, update, func, delete
from sqlalchemy.exc import IntegrityError
from app.config import settings
from app.models.trade import (TradeRegistry, TradeHead, TradeImport, TradeRevision,
                              TradeRow, TradePublication)
from app.models.schemas import (
    DashboardPayload,
    KpiMetric,
    AiMeaning,
    ChartConfig,
    Hs4CategorySummary,
    Hs8CommoditySummary,
    MarketShareItem,
    CommodityListItem,
    ExchangeRateInfo
)
from app.services.auth_service import audit
from app.services.etl_service import parse_import, month_bound, label, hs_code
from app.services.hs_product_service import (
    HS4_MAP, HS8_MAPPING, COUNTRY_MAP,
    get_hs8_product_info,
    get_country_info,
    get_hs4_official_name,
    clean_hs_code
)


def registry_entry(entry):
    return {key: getattr(entry, key) for key in ('kind', 'code', 'name_en', 'name_km', 'parent_code', 'iso3', 'aliases')}


def get_head(db, lock=False):
    head = db.get(TradeHead, 1)
    if head is None:
        try:
            with db.begin_nested():
                db.add(TradeHead(id=1, generation=0, registry_generation=0))
                db.flush()
        except IntegrityError:
            pass
    statement = select(TradeHead).where(TradeHead.id == 1).execution_options(populate_existing=True)
    if lock:
        statement = statement.with_for_update()
    head = db.scalar(statement)
    if lock:
        generation = head.generation
        changed = db.execute(update(TradeHead).where(TradeHead.id == 1, TradeHead.generation == generation)
                             .values(generation=generation + 1).execution_options(synchronize_session=False))
        if changed.rowcount != 1:
            raise HTTPException(409, 'Concurrent trade change; review and retry')
        db.refresh(head)
    return head


def get_registry(db):
    snapshot = {'hs4': {}, 'hs8': {}, 'country': {}}
    for entry in db.scalars(select(TradeRegistry).order_by(TradeRegistry.kind, TradeRegistry.code)):
        snapshot[entry.kind][entry.code] = registry_entry(entry)
    return snapshot


def country_lookup(registry):
    lookup = {}
    for code, entry in registry['country'].items():
        for alias in [code, entry['name_en'], entry['name_km'], *(entry.get('aliases') or [])]:
            normalized = label(alias)
            if normalized in lookup and lookup[normalized] != code:
                raise HTTPException(409, 'Ambiguous country alias in registry')
            lookup[normalized] = code
    return lookup


def unknown_country_code(incoming):
    return 'country-' + sha256(label(incoming).encode('utf-8')).hexdigest()[:32]


def seed_reviewed_registry(db, actor=None):
    """Explicit callable; only the existing reviewed static entries, no fallbacks."""
    head = get_head(db, lock=True)
    additions = []
    for code, info in HS4_MAP.items():
        additions.append(dict(kind='hs4', code=code, name_en=info['title_en'], name_km=info['title_km'], aliases=[]))
    for code, info in HS8_MAPPING.items():
        if code[:4] in HS4_MAP and re.search(r'[\u1780-\u17ff]', info['name_kh']):
            additions.append(dict(kind='hs8', code=code, name_en=info['name_en'], name_km=info['name_kh'], parent_code=code[:4], aliases=[]))
    countries = {}
    for alias, info in COUNTRY_MAP.items():
        entry = countries.setdefault(info['ISO'], dict(kind='country', code=info['ISO'], name_en=info['EN'],
                                    name_km=info['Canonical_KH'], iso3=info['ISO'], aliases=[]))
        if alias not in entry['aliases']:
            entry['aliases'].append(alias)
    additions.extend(countries.values())
    count = 0
    for entry in additions:
        if db.get(TradeRegistry, (entry['kind'], entry['code'])) is None:
            db.add(TradeRegistry(**entry))
            count += 1
    if count:
        head.registry_generation += 1
        audit(db, actor, 'trade.registry.seed', 'trade_registry', 'reviewed-static', {'count': count})
    db.flush()
    return count


def save_registry(db, payload, actor, replace=False):
    head = get_head(db, lock=True)
    data = dict(payload)
    kind, code = data['kind'], data['code']
    if kind not in ('hs4', 'hs8', 'country'):
        raise HTTPException(422, 'Invalid registry kind')
    data['name_en'] = ' '.join(data['name_en'].split())
    data['name_km'] = ' '.join(data['name_km'].split())
    if not data['name_en'] or not data['name_km'] or not re.search(r'[\u1780-\u17ff]', data['name_km']):
        raise HTTPException(422, 'English and Khmer names are required (Khmer must contain Khmer text)')
    if kind in ('hs4', 'hs8'):
        try:
            if hs_code(code, 4 if kind == 'hs4' else 8) != code:
                raise ValueError()
        except ValueError:
            raise HTTPException(422, 'HS codes must have exact digit length')
    elif not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,159}', code):
        raise HTTPException(422, 'Use the server-issued country code for unknown labels')
    parent = data.get('parent_code')
    if kind == 'hs8':
        if parent != code[:4] or db.get(TradeRegistry, ('hs4', parent)) is None:
            raise HTTPException(422, 'HS8 requires its existing HS4 parent')
    elif parent:
        raise HTTPException(422, 'Only HS8 entries have a parent')
    iso3 = data.get('iso3')
    if iso3 and (kind != 'country' or not re.fullmatch('[A-Z]{3}', iso3)):
        raise HTTPException(422, 'ISO3 must be an uppercase three-letter country code')
    aliases = data.get('aliases', [])
    if len(aliases) > 100 or any(len(alias) > 160 for alias in aliases):
        raise HTTPException(422, 'At most 100 aliases, each at most 160 characters')
    if len(data['name_en']) > 300 or len(data['name_km']) > 300:
        raise HTTPException(422, 'Registry names must be at most 300 characters')
    data['aliases'] = list(dict.fromkeys(' '.join(a.split()) for a in aliases if a.strip()))

    if kind == 'country':
        # Check if the submitted code, ISO3, English name, or Khmer name belongs to an already existing registered country
        existing_target_code = None
        for c_code, c_entry in get_registry(db)['country'].items():
            if c_code == code or \
               (iso3 and c_entry.get('iso3') == iso3) or \
               (label(c_entry['name_en']) == label(data['name_en'])) or \
               (label(c_entry['name_km']) == label(data['name_km'])):
                existing_target_code = c_code
                break

        if existing_target_code:
            canonical_entry = db.get(TradeRegistry, ('country', existing_target_code))
            existing_aliases = list(canonical_entry.aliases or [])
            new_aliases = [a for a in data['aliases'] if a not in existing_aliases]

            if not replace or code != existing_target_code or new_aliases:
                for a in new_aliases:
                    existing_aliases.append(a)
                canonical_entry.aliases = existing_aliases

                old_temp = db.get(TradeRegistry, ('country', code))
                if old_temp and old_temp.code != existing_target_code:
                    db.delete(old_temp)

                head.registry_generation += 1
                audit(db, actor, 'trade.registry.alias', 'trade_registry', f'country:{existing_target_code}', {
                    'added_aliases': data['aliases'],
                    'target': existing_target_code
                })
                db.flush()
                return registry_entry(canonical_entry)

    entry = db.get(TradeRegistry, (kind, code))
    if replace and entry is None:
        raise HTTPException(404, 'Registry entry not found')
    if not replace and entry is not None:
        raise HTTPException(409, 'Registry entry already exists')
    proposed = get_registry(db)
    proposed[kind][code] = data
    country_lookup(proposed)  # no aliases silently stealing another canonical key
    if entry is None:
        entry = TradeRegistry(**data)
        db.add(entry)
    else:
        for key, value in data.items():
            setattr(entry, key, value)
    head.registry_generation += 1
    audit(db, actor, 'trade.registry.update' if replace else 'trade.registry.create', 'trade_registry',
          f'{kind}:{code}', data)
    db.flush()
    return registry_entry(entry)


def normalize_rows(rows, registry):
    lookup = country_lookup(registry)
    normalized, unknowns, errors = [], {}, []
    seen, duplicates = {}, 0
    for incoming in rows:
        row = dict(incoming)
        country = lookup.get(label(row['country_label'])) or unknown_country_code(row['country_label'])
        row['country_code'] = country
        for kind, code in (('hs4', row['hs4_code']), ('hs8', row['hs8_code']), ('country', country)):
            entry = registry[kind].get(code)
            if entry is None:
                unknowns[(kind, code)] = {'kind': kind, 'code': code, 'name_en': '', 'name_km': '',
                    'parent_code': row['hs4_code'] if kind == 'hs8' else None, 'iso3': None,
                    'aliases': [row['country_label']] if kind == 'country' else []}
            elif kind == 'hs8' and entry['parent_code'] != row['hs4_code']:
                errors.append({'row': row['source_row'], 'message': 'Registry HS8 parent conflicts with source HS4'})
        key = grain(row)
        if key in seen:
            if amounts(row) == amounts(seen[key]):
                duplicates += 1
            else:
                errors.append({'row': row['source_row'], 'message': f'Conflicting duplicate monthly key (first row {seen[key]["source_row"]})'})
            continue
        seen[key] = row
        normalized.append(row)
    return normalized, list(unknowns.values()), errors, duplicates


def grain(row):
    return (row['year'], row['month'], row['hs8_code'], row['country_code'])


def amounts(row):
    try:
        w = round(Decimal(str(row['weight_kg'])), 4)
    except Exception:
        w = Decimal(str(row['weight_kg']))
    try:
        v = round(Decimal(str(row['val_khr'])), 2)
    except Exception:
        v = Decimal(str(row['val_khr']))
    return (row['hs4_code'], w, v)


def revision_rows(db, revision_id):
    if not revision_id:
        return []
    return [{key: (str(getattr(row, key)) if key in ('weight_kg', 'val_khr') else getattr(row, key))
             for key in ('year', 'month', 'hs4_code', 'hs8_code', 'country_code', 'weight_kg', 'val_khr', 'source_import_id', 'source_row')}
            for row in db.scalars(select(TradeRow).where(TradeRow.revision_id == revision_id))]


def merge_rows(existing, incoming, mode, start_month, end_month):
    old = {grain(r): r for r in existing}
    new = {grain(r): r for r in incoming}
    removed = set()
    if mode == 'complete':
        removed = {key for key, row in old.items() if start_month <= f"{row['year']:04d}-{row['month']:02d}" <= end_month and key not in new}
    merged = {key: row for key, row in old.items() if key not in removed}
    merged.update(new)
    preview = {'inserted': len(new.keys() - old.keys()),
               'updated': sum(amounts(new[key]) != amounts(old[key]) for key in new.keys() & old.keys()),
               'removed': len(removed),
               'unchanged': sum(key not in new or amounts(new[key]) == amounts(row) for key, row in old.items() if key not in removed)}
    return list(merged.values()), preview


def _review_token(staged):
    """Bind approval to the exact shared review, not merely the import ID."""
    identity = {key: getattr(staged, key) for key in (
        'id', 'base_revision_id', 'registry_generation', 'preview', 'rows',
        'errors', 'mode', 'start_month', 'end_month', 'column_mapping')}
    return sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def import_view(db, staged, refresh=False):
    head = get_head(db, lock=refresh)
    if refresh:
        staged = db.scalar(select(TradeImport).where(TradeImport.id == staged.id)
                           .with_for_update().execution_options(populate_existing=True))
    registry = get_registry(db)
    rows, unknowns, errors, duplicate_count = normalize_rows(staged.rows, registry)
    if refresh and staged.status != 'committed':
        staged.base_revision_id = head.revision_id
        staged.registry_generation = head.registry_generation
        if staged.errors:
            staged.preview = {'inserted': 0, 'updated': 0, 'removed': 0, 'unchanged': 0}
        else:
            _, staged.preview = merge_rows(revision_rows(db, head.revision_id), rows, staged.mode, staged.start_month, staged.end_month)
        db.flush()
    return {'id': staged.id, 'filename': staged.filename, 'storage_name': staged.storage_name, 'mode': staged.mode, 'status': staged.status,
            'start_month': staged.start_month, 'end_month': staged.end_month, 'row_count': len(rows),
            'duplicate_count': duplicate_count, 'errors': staged.errors + errors, 'unknowns': unknowns,
            'preview': staged.preview, 'column_mapping': staged.column_mapping,
            'created_at': staged.created_at.isoformat(), 'revision_id': staged.revision_id,
            'review_token': _review_token(staged)}


def stage_import(db, contents, filename, mode, start_month=None, end_month=None, actor=None):
    if mode not in ('complete', 'partial'):
        raise HTTPException(422, 'Mode must be complete or partial')
    max_bytes = getattr(settings, 'MAX_UPLOAD_BYTES', 26214400)
    if len(contents) > max_bytes:
        raise HTTPException(413, 'Import exceeds upload limit')
    # An explicit upload may bootstrap reviewed dictionaries; never samples or startup.
    seed_reviewed_registry(db, actor)
    parsed = parse_import(contents, filename, mode, start_month, end_month)
    safe_filename = Path(filename.replace('\\', '/')).name[:255]
    
    # Store compressed payload purely in database during staging (ZERO filesystem writes until commit)
    compressed_b64 = None
    if not parsed['errors']:
        compressed_b64 = base64.b64encode(gzip.compress(contents, compresslevel=9)).decode('ascii')

    staged = TradeImport(filename=safe_filename, storage_name=None, raw_payload=compressed_b64, mode=mode,
                         status='invalid' if parsed['errors'] else 'staged', **parsed)
    # mode validation must not violate the database constraint on an invalid request.
    if mode not in ('complete', 'partial'):
        raise HTTPException(422, 'Mode must be complete or partial')
    db.add(staged)
    db.flush()
    view = import_view(db, staged, refresh=True)
    if view['errors']:
        staged.status = 'invalid'
        staged.raw_payload = None
        view['status'] = 'invalid'
    audit(db, actor, 'trade.import.stage', 'trade_import', staged.id,
          {'filename': safe_filename, 'row_count': view['row_count'], 'mode': mode})
    return view


def discard_import(db, import_id: str, actor=None):
    staged = db.scalar(select(TradeImport).where(TradeImport.id == import_id))
    if staged is None:
        raise HTTPException(404, 'Import not found')
    if staged.status == 'committed':
        raise HTTPException(400, 'Cannot delete a committed import revision')
    filename = staged.filename
    db.delete(staged)
    db.flush()
    audit(db, actor, 'trade.import.discard', 'trade_import', import_id, {'filename': filename})
    return {'deleted': True, 'id': import_id}


def commit_import(db, import_id, review_token: str, actor=None):
    head = get_head(db, lock=True)
    staged = db.scalar(select(TradeImport).where(TradeImport.id == import_id).with_for_update().execution_options(populate_existing=True))
    if staged is None:
        raise HTTPException(404, 'Import not found')
    if not isinstance(review_token, str) or review_token != _review_token(staged):
        raise HTTPException(409, 'Review changed; refresh import review before committing')
    if staged.status == 'committed':
        return import_view(db, staged)
    if staged.base_revision_id != head.revision_id or staged.registry_generation != head.registry_generation:
        raise HTTPException(409, 'Stale preview. Refresh import review before committing')
    registry = get_registry(db)
    incoming, unknowns, conflicts, duplicate_count = normalize_rows(staged.rows, registry)
    if staged.errors or conflicts or staged.status == 'invalid':
        raise HTTPException(409, {'message': 'Invalid import cannot be committed', 'errors': staged.errors + conflicts})
    if unknowns:
        raise HTTPException(409, {'message': 'Resolve bilingual registry names before commit', 'unknowns': unknowns})
    if not incoming:
        raise HTTPException(409, 'Empty replacement is forbidden')
    incoming = [{**row, 'source_import_id': staged.id} for row in incoming]
    merged, preview = merge_rows(revision_rows(db, head.revision_id), incoming, staged.mode, staged.start_month, staged.end_month)
    if preview != staged.preview:
        raise HTTPException(409, 'Preview changed; refresh review')
    revision = TradeRevision(source_import_id=staged.id, row_count=len(merged), registry_snapshot=registry)
    db.add(revision)
    db.flush()
    db.add_all([TradeRow(revision_id=revision.id, **{key: row[key] for key in
                ('year', 'month', 'hs4_code', 'hs8_code', 'country_code', 'weight_kg', 'val_khr', 'source_import_id', 'source_row')}) for row in merged])
    head.revision_id = revision.id
    staged.revision_id, staged.status = revision.id, 'committed'
    staged.preview, staged.duplicate_count = preview, duplicate_count
    
    # Write unique confirmed compressed backup to disk ONLY on explicit commit
    # Format: "originaldatafilename_startdate-enddateofdata"
    storage = Path(settings.STORAGE_PATH) / 'trade-originals'
    storage.mkdir(parents=True, exist_ok=True, mode=0o700)
    stem = Path(staged.filename).stem[:50]
    ext = Path(staged.filename).suffix or '.xlsx'
    if ext == '.gz':
        ext = '.xlsx'
    scope = f"{staged.start_month}-{staged.end_month}" if (staged.start_month and staged.end_month) else "full"
    final_backup_name = f"{stem}_{scope}{ext}.gz"
    
    if staged.raw_payload:
        raw_compressed_bytes = base64.b64decode(staged.raw_payload.encode('ascii'))
        with open(storage / final_backup_name, 'wb') as handle:
            handle.write(raw_compressed_bytes)
        staged.storage_name = final_backup_name
    
    audit(db, actor, 'trade.import.commit', 'trade_revision', revision.id, {'import_id': staged.id, **preview})
    db.flush()
    try:
        from app.services.redis_service import redis_service
        redis_service.invalidate_all_trade_caches()
    except Exception:
        pass
    return import_view(db, staged)


def publication_view(publication, db=None):
    if not publication:
        return None
    data = {key: getattr(publication, key) for key in ('id', 'revision_id', 'start_month', 'end_month')}
    from sqlalchemy.orm import object_session
    session = db or object_session(publication)
    if session is not None and publication.revision_id and publication.start_month and publication.end_month:
        try:
            start = int(publication.start_month.replace('-', ''))
            end = int(publication.end_month.replace('-', ''))
            count = session.scalar(
                select(func.count(TradeRow.id)).where(
                    TradeRow.revision_id == publication.revision_id,
                    TradeRow.year * 100 + TradeRow.month >= start,
                    TradeRow.year * 100 + TradeRow.month <= end
                )
            )
            if count is not None:
                data['row_count'] = count
        except Exception:
            pass
    return data


def current_publication(db):
    head = db.get(TradeHead, 1)
    return db.get(TradePublication, head.publication_id) if head and head.publication_id else None


def publish(db, revision_id, start_month, end_month, actor=None):
    try:
        month_bound(start_month)
        month_bound(end_month)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    if start_month > end_month:
        raise HTTPException(422, 'Invalid reporting range')
    head = get_head(db, lock=True)
    revision = db.get(TradeRevision, revision_id)
    if not revision or revision.status != 'ready':
        raise HTTPException(404, 'Ready revision not found')
    rows = revision_rows(db, revision_id)
    periods = {f"{r['year']:04d}-{r['month']:02d}" for r in rows}
    if start_month not in periods or end_month not in periods:
        raise HTTPException(422, 'Reporting boundaries must have rows in this revision')
    publication = TradePublication(revision_id=revision_id, start_month=start_month, end_month=end_month)
    db.add(publication)
    db.flush()
    head.publication_id = publication.id
    view = publication_view(publication, db=db)
    audit(db, actor, 'trade.publish', 'trade_publication', publication.id, view)
    db.flush()
    try:
        from app.services.redis_service import redis_service
        redis_service.invalidate_all_trade_caches()
    except Exception:
        pass
    return view


def delete_revision(db, revision_id: str, actor=None):
    head = get_head(db, lock=True)
    revision = db.scalar(select(TradeRevision).where(TradeRevision.id == revision_id))
    if revision is None:
        raise HTTPException(404, 'Revision not found')

    # Determine remaining revisions sorted newest to oldest
    remaining_revisions = list(db.scalars(
        select(TradeRevision).where(TradeRevision.id != revision_id).order_by(TradeRevision.created_at.desc())
    ))
    restored_revision = remaining_revisions[0] if remaining_revisions else None

    # Remove stored backup archive on disk if present
    source_import = db.scalar(select(TradeImport).where(TradeImport.id == revision.source_import_id))
    if source_import and source_import.storage_name:
        storage = Path(settings.STORAGE_PATH) / 'trade-originals'
        backup_file = storage / source_import.storage_name
        if backup_file.is_file():
            try:
                backup_file.unlink()
            except Exception:
                pass

    # Update head revision pointer
    if head.revision_id == revision_id:
        head.revision_id = restored_revision.id if restored_revision else None

    # Update head publication pointer if it points to the deleted revision
    current_pub = db.get(TradePublication, head.publication_id) if head.publication_id else None
    if current_pub and current_pub.revision_id == revision_id:
        if restored_revision:
            prev_pub = db.scalar(
                select(TradePublication)
                .where(TradePublication.revision_id == restored_revision.id)
                .order_by(TradePublication.created_at.desc())
            )
            if prev_pub:
                head.publication_id = prev_pub.id
            else:
                bounds = db.execute(
                    select(
                        func.min(TradeRow.year), func.min(TradeRow.month),
                        func.max(TradeRow.year), func.max(TradeRow.month)
                    ).where(TradeRow.revision_id == restored_revision.id)
                ).first()
                if bounds and bounds[0] is not None:
                    s_m = f"{bounds[0]:04d}-{bounds[1]:02d}"
                    e_m = f"{bounds[2]:04d}-{bounds[3]:02d}"
                    auto_pub = TradePublication(revision_id=restored_revision.id, start_month=s_m, end_month=e_m)
                    db.add(auto_pub)
                    db.flush()
                    head.publication_id = auto_pub.id
                else:
                    head.publication_id = None
        else:
            head.publication_id = None

    # Cascade delete records via SQL statements
    db.execute(update(TradeImport).where(TradeImport.revision_id == revision_id).values(revision_id=None))
    db.execute(delete(TradePublication).where(TradePublication.revision_id == revision_id))
    db.execute(delete(TradeRow).where(TradeRow.revision_id == revision_id))
    db.execute(delete(TradeRevision).where(TradeRevision.id == revision_id))
    if source_import:
        db.execute(delete(TradeImport).where(TradeImport.id == source_import.id))

    audit(db, actor, 'trade.revision.delete', 'trade_revision', revision_id, {
        'deleted_row_count': revision.row_count,
        'restored_revision_id': head.revision_id,
        'remaining_revisions_count': len(remaining_revisions)
    })
    db.flush()
    try:
        from app.services.redis_service import redis_service
        redis_service.invalidate_all_trade_caches()
    except Exception:
        pass
    return {
        'deleted': True,
        'revision_id': revision_id,
        'restored_revision_id': head.revision_id,
        'publication': publication_view(current_publication(db), db=db),
        'remaining_count': len(remaining_revisions)
    }



def scoped_frame(db):
    """Filter the authoritative snapshot in SQL BEFORE pandas, aggregates, AI or queries."""
    publication = current_publication(db)
    if publication is None:
        raise HTTPException(404, 'No trade revision has been published')
    revision = db.get(TradeRevision, publication.revision_id)
    start, end = int(publication.start_month.replace('-', '')), int(publication.end_month.replace('-', ''))
    rows = list(db.scalars(select(TradeRow).where(TradeRow.revision_id == publication.revision_id,
                         TradeRow.year * 100 + TradeRow.month >= start,
                         TradeRow.year * 100 + TradeRow.month <= end)))
    if not rows:
        raise HTTPException(404, 'Published reporting period has no rows')
    registry = revision.registry_snapshot
    records = []
    for row in rows:
        country = registry['country'][row.country_code]
        records.append({'year': row.year, 'month': row.month, 'hs8_code': row.hs8_code,
                        'hs4_code': row.hs4_code, 'country': country['name_en'], 'country_code': row.country_code,
                        'country_kh': country['name_km'], 'country_iso3': country.get('iso3') or 'OTH',
                        'hs4_desc': registry['hs4'][row.hs4_code]['name_en'],
                        'product_name': registry['hs8'][row.hs8_code]['name_en'],
                        'product_name_km': registry['hs8'][row.hs8_code]['name_km'],
                        'weight_kg': float(row.weight_kg), 'val_khr': float(row.val_khr)})
    return pd.DataFrame.from_records(records), registry, publication_view(publication, db=db)


def migrate_legacy(db, path, actor=None):
    """Read-only, explicit CLI migration. Stage for review, NEVER publish automatically.

    XLSX/CSV use normal import validation. DuckDB is opened read-only; source remains
    unchanged. Unknowns and duplicate conflicts remain gated through admin review.
    """
    path = Path(path)
    if path.suffix.lower() in ('.csv', '.xlsx'):
        if path.stat().st_size > getattr(settings, 'MAX_UPLOAD_BYTES', 26214400):
            raise HTTPException(413, 'Legacy source exceeds upload limit')
        contents = path.read_bytes()
        return stage_import(db, contents, path.name, 'partial', actor=actor)
    import duckdb
    with duckdb.connect(str(path), read_only=True, config={'enable_external_access': False}) as connection:
        frame = connection.execute('SELECT year,month,hs8_code,hs4_code,hs4_desc,country,weight_kg,val_khr FROM master_trade_data LIMIT 200001').df()
    if len(frame) > 200000:
        raise HTTPException(413, 'Legacy source exceeds import row limit')
    frame.columns = ['Year', 'Month', 'HS8', 'HS4', 'Description', 'Country', 'Weight (kg)', 'Value (KHR)']
    return stage_import(db, frame.to_csv(index=False, float_format='%.6f').encode('utf-8'), path.name + '.csv', 'partial', actor=actor)


def build_dashboard_payload(
    session_id: str,
    metrics: dict,
    exchange_rate: float,
    ai_insights: dict,
    exchange_rate_info: ExchangeRateInfo | None = None
) -> DashboardPayload:
    """Standardizes metrics and generated AI insights into the API Response Payload."""
    total_val_usd = metrics['total_val_usd']
    total_weight_ton = metrics['total_weight_ton']
    total_transactions = int(metrics.get('total_transactions', 0))
    active_countries_count = len(metrics.get('available_countries', []))
    total_hs8_count = len(metrics.get('commodity_list', []))
    
    # 1. Summary KPIs
    summary_kpis = [
        KpiMetric(
            label="Revenue (USD)",
            value=f"${total_val_usd/1e6:,.2f}M USD",
            numeric_val=total_val_usd,
            unit="USD",
            description="Total agricultural export revenue"
        ),
        KpiMetric(
            label="Total Transactions",
            value=f"{total_transactions:,} Records",
            numeric_val=float(total_transactions),
            unit="Records",
            description="Total trade customs declarations recorded"
        ),
        KpiMetric(
            label="Export Volume",
            value=f"{total_weight_ton:,.2f} Tonnes",
            numeric_val=total_weight_ton,
            unit="Tonnes",
            description="Total agricultural export weight"
        ),
        KpiMetric(
            label="Destination Markets",
            value=f"{active_countries_count} Countries",
            numeric_val=float(active_countries_count),
            unit="Markets",
            description="Active international trading partners"
        ),
        KpiMetric(
            label="Total Commodities",
            value=f"{total_hs8_count} Commodities",
            numeric_val=float(total_hs8_count),
            unit="Commodities",
            description="Active 8-digit tariff line products"
        )
    ]
    
    # 2. HS8 Commodities (Primary Level)
    hs8_list = []
    for item in metrics.get('hs8_commodities', metrics.get('hs8_summary', [])):
        code = clean_hs_code(item.get('hs8_code', ''), 8)
        hs4 = clean_hs_code(item.get('hs4_code', ''), 4)
        info = get_hs8_product_info(code) if code else {}
        name_en = item.get('name_en') or item.get('product_name') or info.get('name_en') or f"HS {code}"
        name_km = item.get('name_km') or item.get('name_kh') or info.get('name_kh') or name_en
        cat_en = item.get('category_en') or info.get('category_en') or 'Other Agricultural'
        cat_km = item.get('category_km') or item.get('category_kh') or info.get('category_kh') or 'កសិផលផ្សេងៗ'
        val_usd = float(item.get('val_usd', 0.0) or 0.0)
        val_khr = float(item.get('val_khr', val_usd * exchange_rate) or 0.0)
        weight_ton = float(item.get('weight_ton', 0.0) or 0.0)
        weight_kg = float(item.get('weight_kg', 0.0) or (weight_ton * 1000.0))
        unit_price = item.get('unit_price_usd_per_kg')
        if unit_price is None:
            unit_price = (val_usd / weight_kg) if weight_kg > 0 else 0.0

        hs8_list.append(
            Hs8CommoditySummary(
                hs8_code=code,
                hs4_code=hs4,
                name_en=name_en,
                name_km=name_km,
                category_en=cat_en,
                category_km=cat_km,
                weight_tonnes=round(weight_ton, 6),
                weight_kg=round(weight_kg, 2),
                val_usd=round(val_usd, 2),
                val_khr=round(val_khr, 2),
                revenue_share_pct=round(item.get('revenue_share_pct', 0.0), 2),
                volume_share_pct=round(item.get('volume_share_pct', 0.0), 2),
                unit_price_usd_per_kg=round(unit_price, 3)
            )
        )

    # 3. HS4 Categories (Macro Level Reference)
    hs4_list = []
    for item in metrics.get('hs4_summary', []):
        code = clean_hs_code(item.get('hs4_code', ''), 4)
        t_en, t_km, d_en, d_km = get_hs4_official_name(code, item.get('hs4_desc', ''))
        val_usd = float(item.get('val_usd', 0.0) or 0.0)
        val_khr = float(item.get('val_khr', val_usd * exchange_rate) or 0.0)
        weight_ton = float(item.get('weight_ton', 0.0) or 0.0)
        weight_kg = float(item.get('weight_kg', 0.0) or (weight_ton * 1000.0))
        
        hs4_list.append(
            Hs4CategorySummary(
                hs4_code=code,
                hs4_desc=item.get('hs4_official_title') or t_en,
                official_title=item.get('hs4_official_title') or t_en,
                title_en=item.get('hs4_title_en') or t_en,
                title_km=item.get('hs4_title_km') or t_km,
                full_desc_en=item.get('hs4_full_desc_en') or d_en,
                full_desc_km=item.get('hs4_full_desc_km') or d_km,
                weight_tonnes=round(weight_ton, 6),
                weight_kg=round(weight_kg, 2),
                val_usd=round(val_usd, 2),
                val_khr=round(val_khr, 2),
                revenue_share_pct=round(item.get('revenue_share_pct', 0.0), 2),
                volume_share_pct=round(item.get('volume_share_pct', 0.0), 2),
                unit_price_usd_per_kg=0.0
            )
        )

    # 4. Market Share Table Data
    market_share_table = []
    for item in metrics.get('country_summary', []):
        raw_c = item.get('country', 'Other')
        c_info = get_country_info(raw_c)
        c_en = item.get('country_en') or c_info.get('EN') or raw_c
        c_kh = item.get('country_kh') or c_info.get('Canonical_KH') or raw_c
        c_iso = item.get('country_iso3') or c_info.get('ISO') or 'OTH'
        val_usd = float(item.get('val_usd', 0.0) or 0.0)
        val_khr = float(item.get('val_khr', val_usd * exchange_rate) or 0.0)
        weight_ton = float(item.get('weight_ton', 0.0) or 0.0)
        weight_kg = float(item.get('weight_kg', 0.0) or (weight_ton * 1000.0))
        rev_share = float(item.get('revenue_share_pct', item.get('share_pct', 0.0)) or 0.0)
        vol_share = float(item.get('volume_share_pct', 0.0) or 0.0)
        unit_price = item.get('unit_price_usd_per_kg')
        if unit_price is None:
            unit_price = (val_usd / weight_kg) if weight_kg > 0 else 0.0

        market_share_table.append(
            MarketShareItem(
                country=c_en,
                country_en=c_en,
                country_kh=c_kh,
                country_iso3=c_iso,
                val_usd=round(val_usd, 2),
                val_khr=round(val_khr, 2),
                weight_ton=round(weight_ton, 6),
                weight_kg=round(weight_kg, 2),
                revenue_share_pct=round(rev_share, 2),
                volume_share_pct=round(vol_share, 2),
                unit_price_usd_per_kg=round(unit_price, 3)
            )
        )
    
    # 5. Charts Configuration
    commodity_chart_data = []
    for item in metrics.get('commodity_multi', metrics.get('hs8_commodities', [])):
        code = clean_hs_code(item.get('hs8_code', ''), 8)
        hs4 = clean_hs_code(item.get('hs4_code', ''), 4)
        info = get_hs8_product_info(code) if code else {}
        name_en = item.get('name_en') or item.get('product_name') or info.get('name_en') or f"HS {code}"
        name_km = item.get('name_km') or item.get('name_kh') or info.get('name_kh') or name_en
        cat_en = item.get('category_en') or info.get('category_en') or 'Other Agricultural'
        cat_km = item.get('category_km') or item.get('category_kh') or info.get('category_kh') or 'កសិផលផ្សេងៗ'
        val_usd = float(item.get('val_usd', 0.0) or 0.0)
        weight_ton = float(item.get('weight_ton', 0.0) or 0.0)
        weight_kg = float(item.get('weight_kg', 0.0) or (weight_ton * 1000.0))
        unit_price = item.get('unit_price_usd_per_kg')
        if unit_price is None:
            unit_price = (val_usd / weight_kg) if weight_kg > 0 else 0.0

        commodity_chart_data.append({
            'name': name_en,
            'name_km': name_km,
            'hs8_code': code,
            'hs4_code': hs4,
            'category_en': cat_en,
            'category_km': cat_km,
            'year': int(item['year']) if 'year' in item and pd.notna(item['year']) else None,
            'country': item.get('country', 'ALL'),
            'value': round(val_usd / 1e6, 3),
            'val_usd': round(val_usd, 2),
            'weight_ton': round(weight_ton, 6),
            'weight_kg': round(weight_kg, 2),
            'unit_price_usd_per_kg': round(unit_price, 3),
            'revenue_share_pct': round(item.get('revenue_share_pct', 0.0), 2),
            'volume_share_pct': round(item.get('volume_share_pct', 0.0), 2),
            'label': name_en
        })

    country_chart_data = []
    for item in metrics.get('country_multi', metrics.get('country_summary', [])):
        raw_c = item.get('country', 'Other')
        c_info = get_country_info(raw_c)
        c_en = item.get('country_en') or c_info.get('EN') or raw_c
        c_kh = item.get('country_kh') or c_info.get('Canonical_KH') or raw_c
        c_iso = item.get('country_iso3') or c_info.get('ISO') or 'OTH'
        val_usd = float(item.get('val_usd', 0.0) or 0.0)
        val_khr = float(item.get('val_khr', val_usd * exchange_rate) or 0.0)
        weight_ton = float(item.get('weight_ton', 0.0) or 0.0)
        weight_kg = float(item.get('weight_kg', 0.0) or (weight_ton * 1000.0))
        rev_share = float(item.get('revenue_share_pct', item.get('share_pct', 0.0)) or 0.0)
        vol_share = float(item.get('volume_share_pct', 0.0) or 0.0)

        country_chart_data.append({
            'name': c_en,
            'country': c_en,
            'country_kh': c_kh,
            'iso3': c_iso,
            'hs8_code': clean_hs_code(item.get('hs8_code', ''), 8),
            'hs4_code': item.get('hs4_code'),
            'year': item.get('year'),
            'value': round(val_usd / 1e6, 3),
            'val_usd': round(val_usd, 2),
            'val_khr': round(val_khr, 2),
            'weight_ton': round(weight_ton, 6),
            'weight_kg': round(weight_kg, 2),
            'revenue_share_pct': round(rev_share, 2),
            'volume_share_pct': round(vol_share, 2)
        })

    market_share_table_data = []
    for item in metrics.get('country_multi', metrics.get('country_summary', [])):
        raw_c = item.get('country', 'Other')
        c_info = get_country_info(raw_c)
        c_en = item.get('country_en') or c_info.get('EN') or raw_c
        c_kh = item.get('country_kh') or c_info.get('Canonical_KH') or raw_c
        c_iso = item.get('country_iso3') or c_info.get('ISO') or 'OTH'
        val_usd = float(item.get('val_usd', 0.0) or 0.0)
        val_khr = float(item.get('val_khr', val_usd * exchange_rate) or 0.0)
        weight_ton = float(item.get('weight_ton', 0.0) or 0.0)
        weight_kg = float(item.get('weight_kg', 0.0) or (weight_ton * 1000.0))
        rev_share = float(item.get('revenue_share_pct', item.get('share_pct', 0.0)) or 0.0)
        vol_share = float(item.get('volume_share_pct', 0.0) or 0.0)
        unit_price = item.get('unit_price_usd_per_kg')
        if unit_price is None:
            unit_price = (val_usd / weight_kg) if weight_kg > 0 else 0.0

        market_share_table_data.append({
            'country': c_en,
            'country_en': c_en,
            'country_kh': c_kh,
            'country_iso3': c_iso,
            'hs8_code': clean_hs_code(item.get('hs8_code', ''), 8),
            'year': int(item['year']) if 'year' in item and pd.notna(item['year']) else None,
            'hs4_code': item.get('hs4_code'),
            'val_usd': round(val_usd, 2),
            'val_million_usd': round(val_usd / 1e6, 3),
            'val_khr': round(val_khr, 2),
            'weight_ton': round(weight_ton, 6),
            'weight_kg': round(weight_kg, 2),
            'revenue_share_pct': round(rev_share, 2),
            'volume_share_pct': round(vol_share, 2),
            'unit_price_usd_per_kg': round(unit_price, 3)
        })

    seasonality_chart_data = [
        {
            'name': item.get('yyyy_mm', ''),
            'yyyy_mm': item.get('yyyy_mm', ''),
            'hs8_code': clean_hs_code(item.get('hs8_code', ''), 8),
            'hs4_code': item.get('hs4_code'),
            'country': item.get('country'),
            'year': item.get('year'),
            'weight_kton': round(float(item.get('weight_kton', 0.0) or 0.0), 6),
            'val_million_usd': round(float(item.get('val_million_usd', 0.0) or 0.0), 4),
            'val_usd': round(float(item.get('val_usd', 0.0) or 0.0), 2),
            'weight_ton': round(float(item.get('weight_ton', item.get('weight_kg', 0.0)/1000.0) or 0.0), 6),
            'weight_kg': round(float(item.get('weight_kg', 0.0) or 0.0), 2)
        } 
        for item in metrics.get('monthly_multi', metrics.get('monthly_summary', []))
    ]
    
    level1_charts = [
        ChartConfig(
            chart_id="chart_commodity_share",
            chart_type="DONUT",
            title="Commodities Export Volume & Revenue",
            data=commodity_chart_data,
            ai_meaning=AiMeaning(**ai_insights.get('commodity_bar_meaning', {
                'explanation': 'This donut chart visualizes the export volume and revenue contribution across major 8-digit HS8 agricultural commodities.',
                'key_takeaway': 'Leading agricultural commodities account for the majority of export volume and revenue.',
                'action': 'Expand local processing facilities to convert raw crop volumes into high-value processed products.'
            }))
        ),
        ChartConfig(
            chart_id="chart_market_share",
            chart_type="HORIZONTAL_BAR",
            title="Top Destination Countries Revenue ($M USD)",
            data=country_chart_data,
            ai_meaning=AiMeaning(**ai_insights.get('country_donut_meaning', {
                'explanation': 'This horizontal bar chart displays export revenue ranking across destination partner countries.',
                'key_takeaway': 'Regional buyers absorb the vast majority of exported agricultural value.',
                'action': 'Negotiate direct export corridors to diversify destination markets.'
            }))
        ),
        ChartConfig(
            chart_id="chart_market_share_table",
            chart_type="TABLE",
            title="Top 10 Market Share",
            data=market_share_table_data,
            ai_meaning=AiMeaning(**ai_insights.get('market_share_table_meaning', ai_insights.get('price_jump_meaning', {
                'explanation': 'This table summarizes market share across top destination countries by volume and revenue.',
                'key_takeaway': 'The top two regional partners account for the largest shares of total agricultural exports.',
                'action': 'Expand direct market linkages with international buyers to capture higher export margins.'
            })))
        ),
        ChartConfig(
            chart_id="chart_seasonality",
            chart_type="LINE",
            title="Volume and Revenue by Months",
            data=seasonality_chart_data,
            ai_meaning=AiMeaning(**ai_insights.get('seasonality_line_meaning', {
                'explanation': 'This dual-axis time-series chart tracks monthly export volume and revenue across the reporting timeline.',
                'key_takeaway': 'Export performance peaks sharply during Q1 harvest seasons before tapering in Q3/Q4.',
                'action': 'Invest in cold-chain and warehousing infrastructure to stabilize supply and prices year-round.'
            }))
        )
    ]
    
    return DashboardPayload(
        session_id=session_id,
        is_valid_trade_data=True,
        exchange_rate=exchange_rate,
        exchange_rate_info=exchange_rate_info,
        begin_date=metrics.get('begin_date'),
        end_date=metrics.get('end_date'),
        available_years=metrics.get('available_years', []),
        available_countries=metrics.get('available_countries', []),
        summary_kpis=summary_kpis,
        hs8_commodities=hs8_list,
        hs4_categories=hs4_list,
        market_share_table=market_share_table,
        level1_charts=level1_charts,
        hhi_risk_score=round(metrics['hhi_score'], 1),
        is_high_risk=metrics['is_high_risk'],
        executive_strategy=ai_insights.get('executive_strategy', []),
        commodity_details=metrics.get('commodity_details', {}),
        commodity_list=[CommodityListItem(**item) for item in metrics.get('commodity_list', [])],
    )

