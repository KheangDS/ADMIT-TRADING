"""Private receipt generation. Missing optional font support fails the job, not approval."""
import hashlib
import os
import threading
from pathlib import Path
from uuid import uuid4
from xml.sax.saxutils import escape

from app.config import settings
from app.services.membership_service import amount_text, iso

_font_lock = threading.Lock()


class ReceiptFontUnavailable(Exception):
    pass


def private_directory(kind):
    root = Path(settings.STORAGE_PATH).expanduser().resolve()
    directory = root / kind
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    return directory


def private_path(kind, name):
    if not name or Path(name).name != name or name in {".", ".."}:
        raise ValueError("Invalid private storage name")
    return private_directory(kind) / name


def receipt_path(receipt):
    return private_path("receipts", receipt.storage_name)


def _font(text):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    needs_khmer = any('\u1780' <= char <= '\u17ff' for char in text)
    if not needs_khmer:
        return "Helvetica", False
    bundled_siemreap = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "KhmerOSSiemreap.ttf"
    bundled_noto = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "NotoSansKhmer.ttf"
    bundled = bundled_siemreap if bundled_siemreap.is_file() else bundled_noto
    configured = getattr(settings, "RECEIPT_FONT_PATH", "") or (str(bundled) if bundled.is_file() else "")
    if not configured:
        if needs_khmer:
            raise ReceiptFontUnavailable("Missing Khmer font (Khmer OS Siemreap / Noto Sans Khmer) for receipt rendering")
        return "Helvetica", False
    try:
        with _font_lock:
            name = "ReceiptUnicode" + hashlib.sha256(str(configured).encode()).hexdigest()[:12]
            if name not in pdfmetrics.getRegisteredFontNames():
                import uharfbuzz  # noqa: F401 - required for correct Khmer shaping
                pdfmetrics.registerFont(TTFont(name, str(configured), shapable=True))
        return name, True
    except Exception as exc:
        raise ReceiptFontUnavailable("Receipt font cannot be loaded or shaped") from exc


def generate_receipt(receipt):
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    font, shaping = _font(receipt.user_name)
    name = f"{receipt.id}.pdf"
    target = private_path("receipts", name)
    temporary = target.with_name(f"{uuid4()}.tmp")
    style = ParagraphStyle("Receipt", fontName="Helvetica", fontSize=11, leading=18, textColor=colors.black)
    name_style = ParagraphStyle("ReceiptName", parent=style, shaping=int(shaping))
    fields = ["AgriTrade verified payment receipt", f"Receipt: {receipt.number}", f"Payment UUID: {receipt.payment_id}",
              f"Account holder: {receipt.user_name}", f"Amount: {amount_text(receipt.amount, receipt.currency)} {receipt.currency}",
              f"Verified payment time (UTC): {iso(receipt.paid_at)}", f"Approval time (UTC): {iso(receipt.approved_at)}",
              f"Membership expiry (UTC): {iso(receipt.expires_at)}", "Manual bank verification completed by an administrator."]
    try:
        SimpleDocTemplate(str(temporary), pagesize=(210 * mm, 297 * mm), title=receipt.number).build(
            [item for index, field in enumerate(fields) for item in (
                Paragraph("Account holder: <font name=\"" + font + "\">" + escape(receipt.user_name) + "</font>", name_style)
                if index == 3 else Paragraph(escape(field), style), Spacer(1, 4 * mm))])
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return name
