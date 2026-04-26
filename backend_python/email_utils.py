import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import db

# ---------------------------------------------------------------------------
# Helper: load settings from DB
# ---------------------------------------------------------------------------
def get_settings():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {r['key']: r['value'] for r in rows}

def is_smtp_configured(cfg):
    return all([cfg.get('smtp_host'), cfg.get('smtp_user'), cfg.get('smtp_password'), cfg.get('smtp_from_email')])

# ---------------------------------------------------------------------------
# HTML Templates
# ---------------------------------------------------------------------------
EMAIL_WRAPPER = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
</head>
<body style="margin:0;padding:0;background-color:#0f172a;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0f172a;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

          <!-- HEADER -->
          <tr>
            <td style="background:linear-gradient(135deg,#1e3a5f 0%,#0f172a 100%);border-radius:16px 16px 0 0;padding:40px 40px 30px;text-align:center;border:1px solid #1e293b;">
              <div style="display:inline-block;background:linear-gradient(135deg,#38bdf8,#818cf8);-webkit-background-clip:text;font-size:28px;font-weight:900;letter-spacing:-1px;color:#38bdf8;">
                📍 UniTrack
              </div>
              <p style="margin:8px 0 0;color:#64748b;font-size:13px;letter-spacing:2px;text-transform:uppercase;">University Attendance System</p>
            </td>
          </tr>

          <!-- BODY -->
          <tr>
            <td style="background:#1e293b;padding:40px;border-left:1px solid #1e293b;border-right:1px solid #1e293b;">
              {body}
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="background:#0f172a;border-radius:0 0 16px 16px;padding:24px 40px;text-align:center;border:1px solid #1e293b;border-top:none;">
              <p style="margin:0;color:#334155;font-size:12px;">© 2026 University Attendance System. All rights reserved.</p>
              <p style="margin:8px 0 0;color:#334155;font-size:11px;">This is an automated email, please do not reply directly.</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

def _invitation_body(first_name, role, setup_url, cfg):
    role_color = {'ADMIN': '#f87171', 'PROFESSOR': '#60a5fa', 'STUDENT': '#4ade80'}.get(role.upper(), '#94a3b8')
    role_label = role.capitalize()
    
    template = cfg.get('email_template_invitation', "You've been invited, {first_name}! Link: {setup_url}")
    return template.format(first_name=first_name, role_color=role_color, role_label=role_label, setup_url=setup_url)

def _reset_body(first_name, reset_url, cfg):
    template = cfg.get('email_template_reset_password', "Password Reset for {first_name}. Link: {reset_url}")
    return template.format(first_name=first_name, reset_url=reset_url)

# ---------------------------------------------------------------------------
# Core send function
# ---------------------------------------------------------------------------
def send_email(to_email, subject, html_body, cfg):
    """
    Attempts to send a real HTML email via SMTP.
    Falls back to printing the email to console if SMTP is not configured.
    Returns (success: bool, message: str)
    """
    full_html = EMAIL_WRAPPER.format(subject=subject, body=html_body)

    if not is_smtp_configured(cfg):
        # ---- MOCK MODE ----
        print(f"\n{'='*60}")
        print(f"[MOCK EMAIL - SMTP not configured]")
        print(f"TO:      {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"----")
        # Extract the setup link from body for easy copy-paste
        import re
        links = re.findall(r'href="(http[^"]+)"', html_body)
        for link in links:
            if 'reset_password' in link or 'forgot' in link:
                print(f"LINK:    {link}")
                break
        print(f"{'='*60}\n")
        return True, "mock"

    # ---- REAL SMTP MODE ----
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f"{cfg['smtp_from_name']} <{cfg['smtp_from_email']}>"
        msg['To']      = to_email

        msg.attach(MIMEText(full_html, 'html'))

        port = int(cfg.get('smtp_port', 587))
        with smtplib.SMTP(cfg['smtp_host'], port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(cfg['smtp_user'], cfg['smtp_password'])
            server.sendmail(cfg['smtp_from_email'], to_email, msg.as_string())

        return True, "sent"
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send to {to_email}: {e}")
        return False, str(e)

# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------
def send_invitation_email(to_email, first_name, role, setup_url):
    cfg = get_settings()
    from_name = cfg.get('smtp_from_name', 'University Attendance System')
    subject = f"You've been invited to {from_name}"
    body = _invitation_body(first_name, role, setup_url, cfg)
    return send_email(to_email, subject, body, cfg)

def send_password_reset_email(to_email, first_name, reset_url):
    cfg = get_settings()
    from_name = cfg.get('smtp_from_name', 'University Attendance System')
    subject = f"Reset your password — {from_name}"
    body = _reset_body(first_name, reset_url, cfg)
    return send_email(to_email, subject, body, cfg)
