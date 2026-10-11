"""ADMIT TRADING Email Service — Resend HTTP adapter with universal email client support.

Never log headers, credentials, payloads or response bodies.
"""
import base64
import html
from pathlib import Path

import httpx

from app.config import settings
from app.services.membership_service import amount_text, iso


class EmailDeliveryError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _get_resend_credentials() -> tuple[str, str]:
    key = getattr(settings, "RESEND_API_KEY", "")
    sender = getattr(settings, "RESEND_FROM_EMAIL", "")
    if not key or not sender:
        raise EmailDeliveryError("email_not_configured")
    return key, sender


def _get_logo_attachment() -> dict | None:
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "images" / "admit-trading.png"
    if logo_path.is_file():
        try:
            return {
                "filename": "admit-trading.png",
                "content": base64.b64encode(logo_path.read_bytes()).decode("ascii"),
                "content_id": "admit_logo"
            }
        except Exception:
            return None
    return None


# ==============================================================================
# 1. PAYMENT RECEIPT EMAIL TEMPLATES
# ==============================================================================

def build_receipt_text(receipt, portal_url: str | None = None) -> str:
    """Plain-text alternative for text-only email clients and spam filter compliance."""
    url = portal_url or getattr(settings, "FRONTEND_URL", "") or getattr(settings, "ADMIN_URL", "") or "https://admit-trading.gov.kh"
    amount = f"{amount_text(receipt.amount, receipt.currency)} {receipt.currency}"
    return (
        "=======================================================\n"
        "ADMIT TRADING — PAYMENT RECEIPT & MEMBERSHIP ACTIVE\n"
        "=======================================================\n\n"
        f"Hello {receipt.user_name},\n\n"
        "Your payment has been successfully verified by the administration team.\n"
        "Your full access to the ADMIT TRADING market analytics and customs data\n"
        "is now active.\n\n"
        "-------------------------------------------------------\n"
        "TRANSACTION DETAILS:\n"
        "-------------------------------------------------------\n"
        f"Receipt Number:       {receipt.number}\n"
        f"Payment ID:           {receipt.payment_id}\n"
        f"Account Holder:       {receipt.user_name}\n"
        f"Account Email:        {receipt.user_email}\n"
        f"Amount Verified:      {amount}\n"
        f"Payment Verified:     {iso(receipt.paid_at)} (UTC)\n"
        f"Approved Time:        {iso(receipt.approved_at)} (UTC)\n"
        f"Membership Expiry:    {iso(receipt.expires_at)} (UTC)\n\n"
        f"Access Member Portal: {url}\n\n"
        "-------------------------------------------------------\n"
        "Official Bank & Admin Verification: This electronic receipt is\n"
        "permanently recorded in the ADMIT TRADING customs audit ledger.\n\n"
        "ADMIT TRADING Intelligence System\n"
        "Phnom Penh, Kingdom of Cambodia\n"
        "=======================================================\n"
    )


def build_receipt_html(receipt, portal_url: str | None = None) -> str:
    """Universal HTML email receipt compatible with Gmail, Outlook, Apple Mail, and mobile clients."""
    url = portal_url or getattr(settings, "FRONTEND_URL", "") or getattr(settings, "ADMIN_URL", "") or "https://admit-trading.gov.kh"
    amount = f"{amount_text(receipt.amount, receipt.currency)} {receipt.currency}"
    user_name_esc = html.escape(str(receipt.user_name or "Valued Member"))
    user_email_esc = html.escape(str(receipt.user_email or ""))
    receipt_num_esc = html.escape(str(receipt.number or ""))
    payment_id_esc = html.escape(str(receipt.payment_id or ""))
    paid_at_esc = html.escape(iso(receipt.paid_at))
    approved_at_esc = html.escape(iso(receipt.approved_at))
    expires_at_esc = html.escape(iso(receipt.expires_at))

    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="x-apple-disable-message-reformatting" />
  <title>ADMIT TRADING Payment Receipt</title>
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
  <style type="text/css">
    body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
    table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
    img {{ -ms-interpolation-mode: bicubic; border: 0; outline: none; text-decoration: none; }}
    body {{ margin: 0; padding: 0; width: 100% !important; min-width: 100%; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
    .email-container {{ max-width: 600px !important; margin: 0 auto !important; }}
    @media only screen and (max-width: 600px) {{
      .mobile-padding {{ padding-left: 20px !important; padding-right: 20px !important; }}
      .mobile-center {{ text-align: center !important; }}
      .receipt-row-label {{ display: block !important; width: 100% !important; padding-bottom: 2px !important; }}
      .receipt-row-value {{ display: block !important; width: 100% !important; text-align: left !important; }}
    }}
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; -webkit-font-smoothing: antialiased;">
  <div style="display: none; font-size: 1px; color: #f1f5f9; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
    Your payment of {amount} has been verified. Your ADMIT TRADING subscription is active.
    &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy; &#847; &zwnj; &nbsp; &#8199; &shy;
  </div>

  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 30px 10px;">
    <tr>
      <td align="center">
        <!--[if mso]>
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="600" align="center">
        <tr><td>
        <![endif]-->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="email-container" style="max-width: 600px; background-color: #ffffff; border-radius: 20px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08);">
          <tr>
            <td height="6" style="background: linear-gradient(90deg, #0284c7 0%, #0d9488 50%, #10b981 100%); font-size: 0px; line-height: 0px;">&nbsp;</td>
          </tr>
          <tr>
            <td style="padding: 28px 36px 20px 36px;" class="mobile-padding">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="left" valign="middle">
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                      <tr>
                        <td valign="middle" style="padding-right: 12px;">
                          <img src="cid:admit_logo" alt="ADMIT TRADING" width="140" style="display: block; width: 140px; max-width: 140px; height: auto; border: 0;" />
                        </td>
                        <td valign="middle">
                          <span style="font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 0.5px; text-transform: uppercase; display: block; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            Trade Intelligence
                          </span>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td align="right" valign="middle" class="mobile-center" style="padding-top: 5px;">
                    <span style="display: inline-block; background-color: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46; font-size: 11px; font-weight: 800; padding: 6px 12px; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.5px;">
                      &#9679; Verified Active
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding: 0 36px;" class="mobile-padding">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td height="1" style="background-color: #f1f5f9; font-size: 0px; line-height: 0px;">&nbsp;</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding: 28px 36px 20px 36px;" class="mobile-padding">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="margin-bottom: 16px;">
                <tr>
                  <td align="center" style="background-color: #d1fae5; width: 44px; height: 44px; border-radius: 50%; text-align: center; line-height: 44px; color: #059669; font-size: 22px; font-weight: bold;">
                    &#10003;
                  </td>
                </tr>
              </table>
              <h1 style="margin: 0 0 10px 0; font-size: 22px; font-weight: 900; color: #0f172a; letter-spacing: -0.5px; line-height: 1.3;">
                Payment Verified &amp; Access Activated
              </h1>
              <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #475569;">
                Hello <strong style="color: #0f172a;">{user_name_esc}</strong>,<br />
                Your payment has been successfully reviewed and verified by an administrator. Your full membership access to ADMIT TRADING market analytics, verified customs datasets, and export benchmarks is now officially active.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding: 0 36px 28px 36px;" class="mobile-padding">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden;">
                <tr>
                  <td colspan="2" style="background-color: #0f172a; padding: 12px 20px; color: #ffffff;">
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td align="left">
                          <span style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8;">
                            Official Receipt
                          </span>
                        </td>
                        <td align="right">
                          <span style="font-family: 'Courier New', Courier, monospace; font-size: 12px; font-weight: 700; color: #38bdf8;">
                            {receipt_num_esc}
                          </span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td class="receipt-row-label" style="padding: 11px 20px; font-size: 13px; color: #64748b; font-weight: 600; border-bottom: 1px solid #edf2f7; width: 40%;">Account Holder</td>
                  <td class="receipt-row-value" align="right" style="padding: 11px 20px; font-size: 13px; color: #0f172a; font-weight: 700; border-bottom: 1px solid #edf2f7;">{user_name_esc}</td>
                </tr>
                <tr>
                  <td class="receipt-row-label" style="padding: 11px 20px; font-size: 13px; color: #64748b; font-weight: 600; border-bottom: 1px solid #edf2f7;">Registered Email</td>
                  <td class="receipt-row-value" align="right" style="padding: 11px 20px; font-size: 13px; color: #0f172a; font-weight: 600; border-bottom: 1px solid #edf2f7;">{user_email_esc}</td>
                </tr>
                <tr>
                  <td class="receipt-row-label" style="padding: 13px 20px; font-size: 13px; color: #64748b; font-weight: 700; border-bottom: 1px solid #edf2f7;">Amount Verified</td>
                  <td class="receipt-row-value" align="right" style="padding: 13px 20px; font-size: 17px; color: #059669; font-weight: 900; border-bottom: 1px solid #edf2f7;">{amount}</td>
                </tr>
                <tr>
                  <td class="receipt-row-label" style="padding: 11px 20px; font-size: 13px; color: #64748b; font-weight: 600; border-bottom: 1px solid #edf2f7;">Payment Reference UUID</td>
                  <td class="receipt-row-value" align="right" style="padding: 11px 20px; font-size: 11px; color: #475569; font-family: monospace; font-weight: 600; border-bottom: 1px solid #edf2f7;">{payment_id_esc}</td>
                </tr>
                <tr>
                  <td class="receipt-row-label" style="padding: 11px 20px; font-size: 13px; color: #64748b; font-weight: 600; border-bottom: 1px solid #edf2f7;">Payment Verified (UTC)</td>
                  <td class="receipt-row-value" align="right" style="padding: 11px 20px; font-size: 12px; color: #334155; font-family: monospace; font-weight: 600; border-bottom: 1px solid #edf2f7;">{paid_at_esc}</td>
                </tr>
                <tr>
                  <td class="receipt-row-label" style="padding: 11px 20px; font-size: 13px; color: #64748b; font-weight: 600; border-bottom: 1px solid #edf2f7;">Approved By Admin (UTC)</td>
                  <td class="receipt-row-value" align="right" style="padding: 11px 20px; font-size: 12px; color: #334155; font-family: monospace; font-weight: 600; border-bottom: 1px solid #edf2f7;">{approved_at_esc}</td>
                </tr>
                <tr>
                  <td class="receipt-row-label" style="padding: 11px 20px; font-size: 13px; color: #64748b; font-weight: 600;">Membership Valid Until (UTC)</td>
                  <td class="receipt-row-value" align="right" style="padding: 11px 20px; font-size: 13px; color: #0369a1; font-weight: 800;">{expires_at_esc}</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding: 0 36px 30px 36px;" class="mobile-padding">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{url}" style="height:48px;v-text-anchor:middle;width:280px;" arcsize="24%" stroke="f" fillcolor="#0d9488">
                      <w:anchorlock/>
                      <center style="color:#ffffff;font-family:sans-serif;font-size:13px;font-weight:bold;">
                        Open ADMIT TRADING Portal &rarr;
                      </center>
                    </v:roundrect>
                    <![endif]-->
                    <!--[if !mso]><!-->
                    <a href="{url}" target="_blank" style="display: block; background: linear-gradient(90deg, #0284c7 0%, #0d9488 50%, #059669 100%); color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 800; text-align: center; padding: 15px 28px; border-radius: 12px; box-shadow: 0 4px 14px 0 rgba(13, 148, 136, 0.35); text-transform: uppercase; letter-spacing: 0.5px;">
                      Open ADMIT TRADING Portal &rarr;
                    </a>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding: 0 36px 28px 36px;" class="mobile-padding">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 12px 16px;">
                <tr>
                  <td valign="top" style="padding-right: 10px; font-size: 15px; line-height: 1;">&#128737;&#65039;</td>
                  <td valign="middle" style="font-size: 11px; line-height: 1.5; color: #166534;">
                    <strong>Official Verification:</strong> This electronic receipt confirms manual bank &amp; admin verification in the ADMIT TRADING customs audit ledger. No physical signature is required.
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="background-color: #0f172a; padding: 26px 36px; text-align: center;" class="mobile-padding">
              <p style="margin: 0 0 4px 0; font-size: 12px; font-weight: 800; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">
                ADMIT TRADING Intelligence System
              </p>
              <p style="margin: 0 0 12px 0; font-size: 11px; color: #94a3b8; line-height: 1.4;">
                Agricultural Customs &amp; Market Intelligence Registry<br />
                Phnom Penh, Kingdom of Cambodia
              </p>
              <p style="margin: 0; font-size: 10px; color: #64748b; line-height: 1.4;">
                This transactional email was sent to <strong style="color: #94a3b8;">{user_email_esc}</strong>.<br />
                &copy; 2026 ADMIT TRADING. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
        <!--[if mso]>
        </td></tr>
        </table>
        <![endif]-->
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_receipt(receipt, pdf_path: Path | None = None, client: httpx.Client | None = None) -> None:
    """Dispatches a rich ADMIT TRADING receipt email via Resend with universal client compatibility."""
    key, sender = _get_resend_credentials()
    text_content = build_receipt_text(receipt)
    html_content = build_receipt_html(receipt)

    attachments = []
    if logo := _get_logo_attachment():
        attachments.append(logo)

    payload = {
        "from": sender,
        "to": [receipt.user_email],
        "subject": f"[ADMIT TRADING] Payment Receipt #{receipt.number} — Membership Active",
        "text": text_content,
        "html": html_content,
    }
    if attachments:
        payload["attachments"] = attachments

    own_client = client is None
    client = client or httpx.Client(timeout=httpx.Timeout(30, connect=10), follow_redirects=False)
    try:
        response = client.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Idempotency-Key": f"admit-receipt-{receipt.id}"
            }
        )
        if response.status_code not in {200, 201, 202}:
            raise EmailDeliveryError(f"email_http_{response.status_code}")
        try:
            if not response.json().get("id"):
                raise EmailDeliveryError("email_invalid_response")
        except ValueError:
            raise EmailDeliveryError("email_invalid_response") from None
    except httpx.HTTPError:
        raise EmailDeliveryError("email_transport_error") from None
    finally:
        if own_client:
            client.close()


# ==============================================================================
# 2. WELCOME EMAIL (On First Google OAuth Login or Register)
# ==============================================================================

def build_welcome_text(user, portal_url: str | None = None) -> str:
    url = portal_url or getattr(settings, "FRONTEND_URL", "") or "https://admit-trading.gov.kh"
    return (
        "=======================================================\n"
        "WELCOME TO ADMIT TRADING\n"
        "=======================================================\n\n"
        f"Hello {user.name},\n\n"
        "Welcome to ADMIT TRADING — Cambodia's premier agricultural trade\n"
        "intelligence and customs analytics platform.\n\n"
        "With your new account, you can explore:\n"
        "- Real-time customs trade datasets & reporting cycles\n"
        "- HS4 & HS8 commodity classification breakdown\n"
        "- Destination markets & export trends across Southeast Asia & globally\n"
        "- Grounded AI trade analytics and price benchmarks\n\n"
        f"Get Started: {url}\n\n"
        "If you have any questions, our support team is always here to assist.\n\n"
        "ADMIT TRADING Intelligence System\n"
        "Phnom Penh, Kingdom of Cambodia\n"
        "=======================================================\n"
    )


def build_welcome_html(user, portal_url: str | None = None) -> str:
    url = portal_url or getattr(settings, "FRONTEND_URL", "") or "https://admit-trading.gov.kh"
    user_name_esc = html.escape(str(user.name or "Valued Member"))
    user_email_esc = html.escape(str(user.email or ""))

    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Welcome to ADMIT TRADING</title>
  <style type="text/css">
    body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
    table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
    body {{ margin: 0; padding: 0; width: 100% !important; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    .email-container {{ max-width: 600px !important; margin: 0 auto !important; }}
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9;">
  <div style="display: none; font-size: 1px; color: #f1f5f9; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
    Welcome to ADMIT TRADING. Your account has been successfully created.
  </div>

  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 30px 10px;">
    <tr>
      <td align="center">
        <!--[if mso]>
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="600" align="center">
        <tr><td>
        <![endif]-->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="email-container" style="max-width: 600px; background-color: #ffffff; border-radius: 20px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08);">
          <tr>
            <td height="6" style="background: linear-gradient(90deg, #0284c7 0%, #0d9488 50%, #10b981 100%); font-size: 0px; line-height: 0px;">&nbsp;</td>
          </tr>
          <tr>
            <td style="padding: 32px 36px 20px 36px;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="left">
                    <img src="cid:admit_logo" alt="ADMIT TRADING" width="150" style="display: block; width: 150px; max-width: 150px; height: auto; border: 0;" />
                  </td>
                  <td align="right">
                    <span style="display: inline-block; background-color: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; font-size: 11px; font-weight: 800; padding: 5px 12px; border-radius: 9999px; text-transform: uppercase;">
                      Account Active
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding: 0 36px 30px 36px;">
              <h1 style="margin: 0 0 12px 0; font-size: 24px; font-weight: 900; color: #0f172a; letter-spacing: -0.5px; line-height: 1.3;">
                Welcome to ADMIT TRADING!
              </h1>
              <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #475569;">
                Hello <strong style="color: #0f172a;">{user_name_esc}</strong>,<br />
                Thank you for joining ADMIT TRADING. Your account has been successfully set up and is ready to use.
              </p>

              <!-- Feature Highlights Box -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; padding: 18px 20px; margin-bottom: 24px;">
                <tr>
                  <td>
                    <p style="margin: 0 0 12px 0; font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; color: #0284c7;">
                      What you can do with your account:
                    </p>
                    <ul style="margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.7; color: #334155;">
                      <li><strong>Verified Customs Data:</strong> Official export statistics and tariff classifications.</li>
                      <li><strong>Market Intelligence:</strong> Track real-time destination markets and commodity trends.</li>
                      <li><strong>Grounded AI Research:</strong> Inquire on price benchmarks and trade regulations.</li>
                      <li><strong>Automated MEF Sync:</strong> Official daily exchange rate conversions.</li>
                    </ul>
                  </td>
                </tr>
              </table>

              <!-- CTA Button -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px;">
                <tr>
                  <td align="center">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{url}" style="height:48px;v-text-anchor:middle;width:280px;" arcsize="24%" stroke="f" fillcolor="#0284c7">
                      <w:anchorlock/>
                      <center style="color:#ffffff;font-family:sans-serif;font-size:13px;font-weight:bold;">
                        Start Exploring Dashboard &rarr;
                      </center>
                    </v:roundrect>
                    <![endif]-->
                    <!--[if !mso]><!-->
                    <a href="{url}" target="_blank" style="display: block; background: linear-gradient(90deg, #0284c7 0%, #0d9488 100%); color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 800; text-align: center; padding: 15px 28px; border-radius: 12px; box-shadow: 0 4px 14px 0 rgba(2, 132, 199, 0.35); text-transform: uppercase; letter-spacing: 0.5px;">
                      Start Exploring Dashboard &rarr;
                    </a>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>

            </td>
          </tr>
          <tr>
            <td style="background-color: #0f172a; padding: 24px 36px; text-align: center;">
              <p style="margin: 0 0 4px 0; font-size: 12px; font-weight: 800; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">
                ADMIT TRADING Intelligence System
              </p>
              <p style="margin: 0; font-size: 10px; color: #64748b; line-height: 1.4;">
                This welcome email was sent to <strong style="color: #94a3b8;">{user_email_esc}</strong>.<br />
                &copy; 2026 ADMIT TRADING. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
        <!--[if mso]>
        </td></tr>
        </table>
        <![endif]-->
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_welcome_email(user, client: httpx.Client | None = None) -> None:
    """Dispatches a welcome onboarding email to newly registered or first-time OAuth users."""
    key, sender = _get_resend_credentials()
    text_content = build_welcome_text(user)
    html_content = build_welcome_html(user)

    attachments = []
    if logo := _get_logo_attachment():
        attachments.append(logo)

    payload = {
        "from": sender,
        "to": [user.email],
        "subject": "[ADMIT TRADING] Welcome to ADMIT TRADING — Agricultural Trade Intelligence",
        "text": text_content,
        "html": html_content,
    }
    if attachments:
        payload["attachments"] = attachments

    own_client = client is None
    client = client or httpx.Client(timeout=httpx.Timeout(30, connect=10), follow_redirects=False)
    try:
        response = client.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Idempotency-Key": f"admit-welcome-{user.id}"
            }
        )
        if response.status_code not in {200, 201, 202}:
            raise EmailDeliveryError(f"email_http_{response.status_code}")
    except httpx.HTTPError:
        raise EmailDeliveryError("email_transport_error") from None
    finally:
        if own_client:
            client.close()


# ==============================================================================
# 3. MEMBERSHIP EXPIRATION REMINDER EMAIL (2 Days Before Expiry, Max 1/day)
# ==============================================================================

def build_membership_expiry_text(user, membership, days_left: int = 2, portal_url: str | None = None) -> str:
    url = portal_url or getattr(settings, "FRONTEND_URL", "") or "https://admit-trading.gov.kh/plans"
    day_str = "today" if days_left == 0 else ("tomorrow" if days_left == 1 else f"in {days_left} days")
    return (
        "=======================================================\n"
        "ADMIT TRADING — MEMBERSHIP EXPIRATION REMINDER\n"
        "=======================================================\n\n"
        f"Hello {user.name},\n\n"
        f"This is a reminder that your ADMIT TRADING membership expires {day_str}.\n"
        f"Expiration Date (UTC): {iso(membership.expires_at)}\n\n"
        "To ensure uninterrupted access to premium customs datasets, export\n"
        "analytics, and market reports, please renew your subscription.\n\n"
        f"Renew Your Membership: {url}\n\n"
        "ADMIT TRADING Intelligence System\n"
        "Phnom Penh, Kingdom of Cambodia\n"
        "=======================================================\n"
    )


def build_membership_expiry_html(user, membership, days_left: int = 2, portal_url: str | None = None) -> str:
    url = portal_url or getattr(settings, "FRONTEND_URL", "") or "https://admit-trading.gov.kh/plans"
    user_name_esc = html.escape(str(user.name or "Valued Member"))
    user_email_esc = html.escape(str(user.email or ""))
    expires_at_esc = html.escape(iso(membership.expires_at))
    day_str = "today" if days_left == 0 else ("tomorrow" if days_left == 1 else f"in {days_left} days")

    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ADMIT TRADING Membership Expiration Notice</title>
  <style type="text/css">
    body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
    body {{ margin: 0; padding: 0; width: 100% !important; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    .email-container {{ max-width: 600px !important; margin: 0 auto !important; }}
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9;">
  <div style="display: none; font-size: 1px; color: #f1f5f9; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
    Your ADMIT TRADING membership expires {day_str}. Renew now to keep access.
  </div>

  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 30px 10px;">
    <tr>
      <td align="center">
        <!--[if mso]>
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="600" align="center">
        <tr><td>
        <![endif]-->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="email-container" style="max-width: 600px; background-color: #ffffff; border-radius: 20px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08);">
          <tr>
            <td height="6" style="background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%); font-size: 0px; line-height: 0px;">&nbsp;</td>
          </tr>
          <tr>
            <td style="padding: 30px 36px 20px 36px;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="left">
                    <img src="cid:admit_logo" alt="ADMIT TRADING" width="140" style="display: block; width: 140px; max-width: 140px; height: auto; border: 0;" />
                  </td>
                  <td align="right">
                    <span style="display: inline-block; background-color: #fef3c7; border: 1px solid #fde68a; color: #92400e; font-size: 11px; font-weight: 800; padding: 5px 12px; border-radius: 9999px; text-transform: uppercase;">
                      &#9888; Expiring Soon
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding: 0 36px 30px 36px;">
              <h1 style="margin: 0 0 12px 0; font-size: 22px; font-weight: 900; color: #0f172a; letter-spacing: -0.5px;">
                Your Membership Expires {day_str.capitalize()}
              </h1>
              <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #475569;">
                Hello <strong style="color: #0f172a;">{user_name_esc}</strong>,<br />
                Your ADMIT TRADING subscription is scheduled to expire on <strong style="color: #0f172a;">{expires_at_esc} (UTC)</strong>.
              </p>

              <!-- Renewal Details Box -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #fffbeb; border: 1px solid #fef3c7; border-radius: 14px; padding: 16px 18px; margin-bottom: 24px;">
                <tr>
                  <td style="font-size: 13px; line-height: 1.6; color: #78350f;">
                    <strong>Maintain continuous access:</strong> Renewing before expiration ensures you retain uninterrupted access to historical customs exports, commodity benchmarks, and analytics exports without service pause.
                  </td>
                </tr>
              </table>

              <!-- CTA Button -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{url}" style="height:48px;v-text-anchor:middle;width:280px;" arcsize="24%" stroke="f" fillcolor="#d97706">
                      <w:anchorlock/>
                      <center style="color:#ffffff;font-family:sans-serif;font-size:13px;font-weight:bold;">
                        Renew Subscription Now &rarr;
                      </center>
                    </v:roundrect>
                    <![endif]-->
                    <!--[if !mso]><!-->
                    <a href="{url}" target="_blank" style="display: block; background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%); color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 800; text-align: center; padding: 15px 28px; border-radius: 12px; box-shadow: 0 4px 14px 0 rgba(217, 119, 6, 0.35); text-transform: uppercase; letter-spacing: 0.5px;">
                      Renew Subscription Now &rarr;
                    </a>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="background-color: #0f172a; padding: 24px 36px; text-align: center;">
              <p style="margin: 0 0 4px 0; font-size: 12px; font-weight: 800; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">
                ADMIT TRADING Intelligence System
              </p>
              <p style="margin: 0; font-size: 10px; color: #64748b; line-height: 1.4;">
                This notification was sent to <strong style="color: #94a3b8;">{user_email_esc}</strong>.<br />
                &copy; 2026 ADMIT TRADING. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
        <!--[if mso]>
        </td></tr>
        </table>
        <![endif]-->
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_membership_expiry_reminder(user, membership, days_left: int = 2, client: httpx.Client | None = None) -> None:
    """Dispatches a membership expiration reminder (enforced at most once per day)."""
    key, sender = _get_resend_credentials()
    text_content = build_membership_expiry_text(user, membership, days_left)
    html_content = build_membership_expiry_html(user, membership, days_left)

    attachments = []
    if logo := _get_logo_attachment():
        attachments.append(logo)

    payload = {
        "from": sender,
        "to": [user.email],
        "subject": f"[ADMIT TRADING] Notice: Your Membership Expires in {days_left} Day{'s' if days_left > 1 else ''}",
        "text": text_content,
        "html": html_content,
    }
    if attachments:
        payload["attachments"] = attachments

    own_client = client is None
    client = client or httpx.Client(timeout=httpx.Timeout(30, connect=10), follow_redirects=False)
    try:
        response = client.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Idempotency-Key": f"admit-expiry-{user.id}-{iso(membership.expires_at)[:10]}"
            }
        )
        if response.status_code not in {200, 201, 202}:
            raise EmailDeliveryError(f"email_http_{response.status_code}")
    except httpx.HTTPError:
        raise EmailDeliveryError("email_transport_error") from None
    finally:
        if own_client:
            client.close()


# ==============================================================================
# 4. FORGOT PASSWORD / PASSWORD RESET EMAIL
# ==============================================================================

def build_password_reset_text(user, reset_url: str) -> str:
    return (
        "=======================================================\n"
        "ADMIT TRADING — PASSWORD RESET REQUEST\n"
        "=======================================================\n\n"
        f"Hello {user.name},\n\n"
        "We received a request to reset the password for your ADMIT TRADING account.\n\n"
        f"Reset Link (Valid for 15 minutes):\n{reset_url}\n\n"
        "If you did not make this request, please ignore this email.\n"
        "Your password will remain unchanged and your account is secure.\n\n"
        "ADMIT TRADING Intelligence System\n"
        "Phnom Penh, Kingdom of Cambodia\n"
        "=======================================================\n"
    )


def build_password_reset_html(user, reset_url: str) -> str:
    user_name_esc = html.escape(str(user.name or "Valued Member"))
    user_email_esc = html.escape(str(user.email or ""))
    reset_url_esc = html.escape(reset_url)

    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ADMIT TRADING Password Reset</title>
  <style type="text/css">
    body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
    body {{ margin: 0; padding: 0; width: 100% !important; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    .email-container {{ max-width: 600px !important; margin: 0 auto !important; }}
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9;">
  <div style="display: none; font-size: 1px; color: #f1f5f9; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
    Password reset request for your ADMIT TRADING account. Valid for 15 minutes.
  </div>

  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; padding: 30px 10px;">
    <tr>
      <td align="center">
        <!--[if mso]>
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="600" align="center">
        <tr><td>
        <![endif]-->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="email-container" style="max-width: 600px; background-color: #ffffff; border-radius: 20px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08);">
          <tr>
            <td height="6" style="background: linear-gradient(90deg, #0284c7 0%, #6366f1 100%); font-size: 0px; line-height: 0px;">&nbsp;</td>
          </tr>
          <tr>
            <td style="padding: 30px 36px 20px 36px;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="left">
                    <img src="cid:admit_logo" alt="ADMIT TRADING" width="140" style="display: block; width: 140px; max-width: 140px; height: auto; border: 0;" />
                  </td>
                  <td align="right">
                    <span style="display: inline-block; background-color: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; font-size: 11px; font-weight: 800; padding: 5px 12px; border-radius: 9999px; text-transform: uppercase;">
                      Security Request
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding: 0 36px 30px 36px;">
              <h1 style="margin: 0 0 12px 0; font-size: 22px; font-weight: 900; color: #0f172a; letter-spacing: -0.5px;">
                Reset Your Password
              </h1>
              <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #475569;">
                Hello <strong style="color: #0f172a;">{user_name_esc}</strong>,<br />
                We received a request to reset the password for your ADMIT TRADING account (<strong style="color: #0f172a;">{user_email_esc}</strong>). Click the button below to choose a new password:
              </p>

              <!-- CTA Button -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td align="center">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{reset_url_esc}" style="height:48px;v-text-anchor:middle;width:280px;" arcsize="24%" stroke="f" fillcolor="#0284c7">
                      <w:anchorlock/>
                      <center style="color:#ffffff;font-family:sans-serif;font-size:13px;font-weight:bold;">
                        Reset Password &rarr;
                      </center>
                    </v:roundrect>
                    <![endif]-->
                    <!--[if !mso]><!-->
                    <a href="{reset_url_esc}" target="_blank" style="display: block; background: linear-gradient(90deg, #0284c7 0%, #4f46e5 100%); color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 800; text-align: center; padding: 15px 28px; border-radius: 12px; box-shadow: 0 4px 14px 0 rgba(2, 132, 199, 0.35); text-transform: uppercase; letter-spacing: 0.5px;">
                      Reset Password &rarr;
                    </a>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>

              <!-- 15-Minute Expiry Notice -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px 18px;">
                <tr>
                  <td style="font-size: 12px; line-height: 1.5; color: #64748b;">
                    <strong>Notice:</strong> This password reset link will expire in <strong>15 minutes</strong> for security. If you did not request a password reset, you can safely disregard this email. Your password will not change.
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="background-color: #0f172a; padding: 24px 36px; text-align: center;">
              <p style="margin: 0 0 4px 0; font-size: 12px; font-weight: 800; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">
                ADMIT TRADING Intelligence System
              </p>
              <p style="margin: 0; font-size: 10px; color: #64748b; line-height: 1.4;">
                This security email was sent to <strong style="color: #94a3b8;">{user_email_esc}</strong>.<br />
                &copy; 2026 ADMIT TRADING. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
        <!--[if mso]>
        </td></tr>
        </table>
        <![endif]-->
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_password_reset_email(user, reset_token: str, client: httpx.Client | None = None) -> None:
    """Dispatches a password reset link (15-minute expiration) to public users."""
    key, sender = _get_resend_credentials()
    frontend_base = getattr(settings, "FRONTEND_URL", "").rstrip("/") or "https://admit-trading.gov.kh"
    reset_url = f"{frontend_base}/reset-password?token={reset_token}"

    text_content = build_password_reset_text(user, reset_url)
    html_content = build_password_reset_html(user, reset_url)

    attachments = []
    if logo := _get_logo_attachment():
        attachments.append(logo)

    payload = {
        "from": sender,
        "to": [user.email],
        "subject": "[ADMIT TRADING] Password Reset Request",
        "text": text_content,
        "html": html_content,
    }
    if attachments:
        payload["attachments"] = attachments

    own_client = client is None
    client = client or httpx.Client(timeout=httpx.Timeout(30, connect=10), follow_redirects=False)
    try:
        response = client.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Idempotency-Key": f"admit-pwd-reset-{user.id}-{reset_token[:16]}"
            }
        )
        if response.status_code not in {200, 201, 202}:
            raise EmailDeliveryError(f"email_http_{response.status_code}")
    except httpx.HTTPError:
        raise EmailDeliveryError("email_transport_error") from None
    finally:
        if own_client:
            client.close()
