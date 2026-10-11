"""
AgriTrade - National Bank of Cambodia (NBC) KHQR / Bakong / ABA PayWay QR Service
Encodes dynamic and static EMVCo KHQR payloads with CRC16-CCITT checksums
and produces crisp high-resolution QR codes in Data-URI and PNG formats.
"""
from decimal import Decimal
import io
import base64
import qrcode
from app.config import settings


def crc16_ccitt(data: str) -> str:
    """Compute standard CRC16-CCITT (polynomial 0x1021, init 0xFFFF)."""
    crc = 0xFFFF
    for ch in data.encode("utf-8"):
        crc ^= (ch << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def tlv(tag: str, val: str) -> str:
    """Format an EMVCo Tag-Length-Value string with 2-digit byte length."""
    encoded = val.encode("utf-8")
    return f"{tag}{len(encoded):02d}{val}"


def generate_khqr_string(
    amount: Decimal | float | int | str | None = None,
    currency: str = "USD",
    bill_number: str | None = None,
    merchant_name: str | None = None,
    merchant_id: str | None = None,
    bakong_account: str | None = None,
    bank_name: str | None = None,
    city: str | None = None,
    mcc: str | None = None,
    payway_ref: str | None = None,
) -> str:
    """
    Generate an EMVCo KHQR payload compliant with NBC / Bakong / ABA specifications.
    
    If amount > 0, generates a Dynamic QR (Point of Initiation = '12') with Tag 54.
    If amount is None or 0, generates a Static QR (Point of Initiation = '11').
    """
    name = (merchant_name or settings.KHQR_MERCHANT_NAME or "").strip().upper()
    m_id = (merchant_id or settings.KHQR_MERCHANT_ID or "").strip()
    bakong_acc = (bakong_account or settings.KHQR_BAKONG_ACCOUNT or "").strip()
    bank = (bank_name or settings.KHQR_BANK_NAME or "Bakong").strip()
    merchant_city = (city or settings.KHQR_CITY or "PHNOM PENH").strip().upper()
    cat_code = (mcc or settings.KHQR_MCC or "5999").strip()
    payway = (payway_ref or settings.KHQR_PAYWAY_REF or "").strip()

    if not name or not m_id or not bakong_acc:
        raise ValueError("KHQR credentials not configured in .env (KHQR_MERCHANT_NAME, KHQR_MERCHANT_ID, KHQR_BAKONG_ACCOUNT)")
    
    curr = currency.upper().strip()
    if curr not in {"USD", "KHR"}:
        raise ValueError(f"Unsupported KHQR currency: {currency}")
    currency_code = "840" if curr == "USD" else "116"
    
    numeric_amount: Decimal | None = None
    if amount is not None:
        try:
            numeric_amount = Decimal(str(amount))
            if numeric_amount < 0:
                raise ValueError("Amount must be positive")
        except Exception as e:
            raise ValueError(f"Invalid amount: {amount}") from e

    is_dynamic = numeric_amount is not None and numeric_amount > 0
    init_point = "12" if is_dynamic else "11"
    
    # Tag 30: Merchant Account Information
    tag_30_val = tlv("00", bakong_acc) + tlv("01", m_id) + tlv("02", bank)
    
    # Base payload structure
    payload = (
        tlv("00", "01") +
        tlv("01", init_point) +
        tlv("30", tag_30_val) +
        tlv("52", cat_code) +
        tlv("53", currency_code)
    )
    
    # Tag 54: Transaction Amount (if dynamic)
    if is_dynamic and numeric_amount is not None:
        if curr == "USD":
            amount_str = f"{numeric_amount:.2f}"
        else:
            amount_str = str(int(numeric_amount))
        payload += tlv("54", amount_str)
        
    payload += (
        tlv("58", "KH") +
        tlv("59", name) +
        tlv("60", merchant_city)
    )
    
    # Tag 62: Additional Data Field Template
    tag_62_val = ""
    if bill_number:
        clean_bill = str(bill_number).strip()[:25]
        if clean_bill:
            tag_62_val += tlv("01", clean_bill)
    if payway:
        tag_62_val += tlv("68", payway)
        
    if tag_62_val:
        payload += tlv("62", tag_62_val)
        
    payload += "6304"
    checksum = crc16_ccitt(payload)
    return payload[:-4] + tlv("63", checksum)


def generate_khqr_png_bytes(khqr_string: str) -> bytes:
    """Render the KHQR payload into crisp PNG bytes."""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=3,
        )
        qr.add_data(khqr_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#000000", back_color="#ffffff")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as exc:
        raise RuntimeError(f"Failed to generate QR image: {exc}") from exc


def generate_khqr_data_uri(khqr_string: str) -> str:
    """Render the KHQR payload into a Base64 data:image/png URI for instant frontend display."""
    try:
        raw = generate_khqr_png_bytes(khqr_string)
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception as exc:
        raise RuntimeError(f"Failed to encode QR Data URI: {exc}") from exc


def generate_payment_qr(amount: Decimal | float | int | str | None, currency: str = "USD", bill_number: str | None = None) -> tuple[str, str]:
    """
    Convenience method returning (khqr_payload_string, base64_data_uri).
    """
    try:
        khqr_str = generate_khqr_string(amount=amount, currency=currency, bill_number=bill_number)
        data_uri = generate_khqr_data_uri(khqr_str)
        return khqr_str, data_uri
    except Exception as exc:
        raise RuntimeError(f"KHQR generation failed: {exc}") from exc
