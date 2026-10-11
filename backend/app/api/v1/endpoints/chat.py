"""Member chat: server-built parameterized queries of the published frame only."""
import re
import duckdb
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.schemas import ChatRequest, ChatResponse
from app.services.auth_service import require_member, require_csrf
from app.services.trade_service import scoped_frame
from app.services.duckdb_service import duckdb_service
from app.services.ai_service import ai_service
from app.services.exchange_rate_service import exchange_rate_service
from app.api.v1.endpoints.analytics import validated_rate

router = APIRouter(dependencies=[Depends(require_member)])
MONTH_MAP = {
    'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
    'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
    'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
    'november': 11, 'nov': 11, 'december': 12, 'dec': 12,
    'មករា': 1, 'កុម្ភៈ': 2, 'មីនា': 3, 'មេសា': 4, 'ឧសភា': 5, 'មិថុនា': 6,
    'កក្កដា': 7, 'សីហា': 8, 'កញ្ញា': 9, 'តុលា': 10, 'វិច្ឆិកា': 11, 'ធ្នូ': 12,
}
STOP_WORDS = {'the', 'and', 'all', 'for', 'with', 'from', 'show', 'total', 'value', 'volume',
              'weight', 'revenue', 'country', 'countries', 'product', 'products', 'commodity',
              'commodities', 'export', 'exports', 'trade', 'data', 'list', 'price', 'year',
              'month', 'compare', 'between', 'which', 'what', 'how', 'much', 'many', 'are'}


def named_in_question(name, question):
    name = str(name).strip().casefold()
    if not name:
        return False
    return bool(re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', question))


def build_scoped_query(frame, question, rate, registry):
    """Intent recognition uses the full revision-pinned registry, even absent rows.

    Every predicate combines; e.g. a commodity/country/year/month question does
    not accidentally lose one dimension. Unknown explicit codes/years yield no rows.
    """
    question = question.casefold()
    conditions, parameters = [], [rate, rate]
    codes8 = re.findall(r'(?<!\d)\d{8}(?!\d)', question)
    numbers4 = re.findall(r'(?<!\d)\d{4}(?!\d)', question)
    explicit_hs4 = re.findall(r'\bhs(?:\s*4)?\s*(?:code\s*)?[:#=-]?\s*(\d{4})(?!\d)', question)
    without_hs = re.sub(r'\bhs(?:\s*4)?\s*(?:code\s*)?[:#=-]?\s*\d{4}(?!\d)', '', question)
    numbers4 = re.findall(r'(?<!\d)\d{4}(?!\d)', without_hs)
    years = [int(value) for value in numbers4 if 1900 <= int(value) <= 2200]
    codes4 = explicit_hs4 + [value for value in numbers4 if not 1900 <= int(value) <= 2200]
    matched_codes = []
    if not codes8 and not codes4:
        terms = {word for word in re.findall(r'[^\W\d_]+', question) if len(word) >= 3 and word not in STOP_WORDS}
        for code, entry in registry['hs8'].items():
            parent = registry['hs4'][entry['parent_code']]
            names = [entry['name_en'], entry['name_km'], parent['name_en'], parent['name_km'],
                     *(entry.get('aliases') or [])]
            words = {word.casefold() for name in names for word in re.findall(r'[^\W\d_]+', str(name)) if len(word) >= 3}
            if any(named_in_question(name, question) for name in names) or terms.intersection(words):
                matched_codes.append(code)
    country_codes = []
    country_names = []
    for code, entry in registry['country'].items():
        names = [code, entry['name_en'], entry['name_km'], *(entry.get('aliases') or [])]
        country_names.extend(names)
        if any(named_in_question(name, question) for name in names):
            country_codes.append(code)
    # Explicit entity syntax must not silently turn an unrecognized entity into
    # an overall total. Free-form questions remain supported for known names.
    for match in re.finditer(r'\b(?:to\s+|from\s+|country(?:\s*[:=]\s*|\s+))(.+?)(?=\s+(?:in|for|during|year|month|hs\d*|\d{4})\b|[?;]|$)', question):
        entity = match.group(1).strip()
        temporal = r'(?:(?:the\s+)?(?:year|month)\s+)?(?:\d{4}(?:-\d{2})?|' + '|'.join(re.escape(name) for name in MONTH_MAP) + r')(?=$|\W)'
        if re.match(temporal, question[match.start(1):]):
            continue  # "from January/year 2024" is a date, not an unknown country.
        if re.match(r'^country\s+(?:in|for|during|by|and|year|month|has|had|is|was|exports?|exported)\b', question[match.start():]):
            continue  # "by country in 2024" requests grouping, not a country named "in".
        # Remove recognized entities, longest first, so a known country cannot
        # conceal an unknown second country in a comparison.
        remainder = entity
        for name in sorted(country_names, key=lambda name: len(str(name)), reverse=True):
            if str(name).strip():
                remainder = re.sub(r'(?<!\w)' + re.escape(str(name).strip().casefold()) + r'(?!\w)', '', remainder)
        remainder = re.sub(r'\b(?:and|or|vs|the)\b|[\s,./&-]', '', remainder)
        if remainder or not any(named_in_question(name, entity) for name in country_names):
            raise HTTPException(422, 'Unknown country; use a reviewed country name or code')
    if re.search(r'\b(?:product|commodity)(?:\s*[:=]\s*|\s+)\S', question) and not (codes8 or codes4 or matched_codes):
        raise HTTPException(422, 'Unknown commodity; use a reviewed name or HS code')
    if re.search(r'\bhs(?:4|8)?(?:\s*[:#=-]\s*|\s+)\S', question) and not (codes8 or codes4):
        raise HTTPException(422, 'Use an explicit four- or eight-digit HS code')

    def in_filter(column, values):
        if values:
            values = list(dict.fromkeys(values))
            conditions.append(column + ' IN (' + ','.join('?' for _ in values) + ')')
            parameters.extend(values)

    in_filter('hs8_code', codes8 or matched_codes)
    in_filter('hs4_code', codes4)
    in_filter('country_code', country_codes)
    in_filter('year', years)
    months = [number for name, number in MONTH_MAP.items() if named_in_question(name, question)]
    # ISO month bounds requested in a question are additional predicates.
    iso_periods = re.findall(r'(?<!\d)(\d{4})-(0[1-9]|1[0-2])(?!\d)', question)
    if iso_periods:
        in_filter('year * 100 + month', [int(year) * 100 + int(month) for year, month in iso_periods])
    else:
        in_filter('month', months)
    quarter = re.search(r'\bq([1-4])\b', question)
    if quarter:
        number = int(quarter.group(1))
        in_filter('month', list(range((number - 1) * 3 + 1, number * 3 + 1)))
    where = ' WHERE ' + ' AND '.join(conditions) if conditions else ''
    grouping = ''
    if any(word in question for word in ('month', 'trend', 'season', 'timeline', 'ខែ')):
        grouping = 'year, month'
    elif any(word in question for word in ('by country', 'countries', 'markets', 'destination', 'ប្រទេស')) or re.search(r'\bcountry\b', question) or country_codes:
        grouping = 'country, country_kh'
    elif not any(word in question for word in ('total', 'overall', 'sum', 'សរុប')):
        grouping = 'hs8_code, product_name, product_name_km'
    # Commodity comparison must remain commodity grouped even when countries match.
    if ('compare' in question or ' vs ' in question) and (codes8 or matched_codes):
        grouping = 'hs8_code, product_name, product_name_km'
    projection = (grouping + ', ') if grouping else ''
    aggregate = ('SUM(weight_kg)/1000 AS volume_ton, SUM(val_khr) AS val_khr, '
                 'SUM(val_khr)/? AS val_usd, SUM(val_khr)/?/NULLIF(SUM(weight_kg),0) AS price_usd_per_kg')
    query = 'SELECT ' + projection + aggregate + ' FROM trade_data' + where
    if grouping:
        query += ' GROUP BY ' + grouping
    query += ' ORDER BY val_usd DESC'
    if any(word in question for word in ('lowest month', 'cheapest', 'lowest price')):
        query = query.replace('ORDER BY val_usd DESC', 'ORDER BY price_usd_per_kg ASC' if 'price' in question or 'cheapest' in question else 'ORDER BY val_usd ASC')
    if any(word in question for word in ('highest price', 'expensive')):
        query = query.replace('ORDER BY val_usd DESC', 'ORDER BY price_usd_per_kg DESC')
    top = re.search(r'\btop\s+(\d+)\b', question)
    limit = min(100, max(1, int(top.group(1)))) if top else 100
    if 'peak' in question or 'highest month' in question or 'lowest month' in question:
        limit = 1
    query += ' LIMIT ?'
    parameters.append(limit)
    return query, parameters


@router.post('/chat', response_model=ChatResponse, dependencies=[Depends(require_csrf)])
def chat_with_dataset(payload: ChatRequest, db: Session = Depends(get_db)):
    if not payload.question.strip() or len(payload.question) > 4000:
        raise HTTPException(422, 'Question must contain 1–4000 characters')
    frame, registry, publication = scoped_frame(db)
    if payload.publication_id is not None and payload.publication_id != publication['id']:
        raise HTTPException(409, {'code': 'publication_changed',
                                 'message': 'Published data changed; refresh charts before asking again'})
    default_rate = exchange_rate_service.get_current_rate_value() if payload.exchange_rate is None else 4000.0
    rate = validated_rate(payload.exchange_rate, default_rate)
    query, parameters = build_scoped_query(frame, payload.question, rate, registry)
    try:
        data = duckdb_service.execute_scoped(frame, query, parameters)
    except (duckdb.Error, ValueError):
        raise HTTPException(500, 'Published query could not be executed; no alternative records were returned')
    # A scalar aggregate without matches returns SQL NULL. It is not a valid zero.
    if data and data[0].get('val_khr') is None:
        data = []
    answer = ai_service.answer_dataset_question(publication['id'], payload.question,
                                                {'publication': publication, 'exchange_rate_khr_usd': rate}, data)
    return ChatResponse(question=payload.question, answer=answer, sql_executed=query, data_points=data)
