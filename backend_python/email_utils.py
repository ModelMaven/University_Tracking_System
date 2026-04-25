import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import db

# ---------------------------------------------------------------------------
# Helper: load SMTP config from DB
# ---------------------------------------------------------------------------
def get_smtp_config():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings WHERE key LIKE 'smtp_%'")
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

def _invitation_body(first_name, role, setup_url, from_name):
    role_color = {'ADMIN': '#f87171', 'PROFESSOR': '#60a5fa', 'STUDENT': '#4ade80'}.get(role.upper(), '#94a3b8')
    role_label = role.capitalize()
    return f"""
      <h2 style="margin:0 0 8px;color:#f1f5f9;font-size:24px;font-weight:700;">You've been invited! 🎉</h2>
      <p style="margin:0 0 24px;color:#94a3b8;font-size:15px;line-height:1.6;">
        Hi <strong style="color:#f1f5f9;">{first_name}</strong>, your account has been created on the <strong style="color:#38bdf8;">University Attendance System</strong>.
      </p>

      <div style="background:#0f172a;border-radius:12px;padding:20px 24px;margin-bottom:28px;border-left:4px solid {role_color};">
        <p style="margin:0 0 4px;color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Your Role</p>
        <p style="margin:0;color:{role_color};font-size:18px;font-weight:700;">{role_label}</p>
      </div>

      <p style="margin:0 0 20px;color:#94a3b8;font-size:14px;line-height:1.6;">
        To get started, click the button below to set your password. This link is valid for <strong style="color:#f1f5f9;">24 hours</strong>.
      </p>

      <div style="text-align:center;margin:32px 0;">
        <a href="{setup_url}" style="display:inline-block;background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#ffffff;text-decoration:none;font-size:16px;font-weight:700;padding:16px 40px;border-radius:12px;letter-spacing:0.5px;">
          Set My Password →
        </a>
      </div>

      <p style="margin:28px 0 0;color:#475569;font-size:13px;line-height:1.6;">
        If the button doesn't work, copy and paste this link into your browser:<br>
        <a href="{setup_url}" style="color:#38bdf8;word-break:break-all;">{setup_url}</a>
      </p>

      <p style="margin:20px 0 0;color:#475569;font-size:12px;">
        If you didn't expect this invitation, please ignore this email or contact your administrator.
      </p>
    """

def _reset_body(first_name, reset_url, from_name):
    return f"""
      <h2 style="margin:0 0 8px;color:#f1f5f9;font-size:24px;font-weight:700;">Password Reset Request 🔐</h2>
      <p style="margin:0 0 24px;color:#94a3b8;font-size:15px;line-height:1.6;">
        Hi <strong style="color:#f1f5f9;">{first_name}</strong>, we received a request to reset your password.
      </p>

      <div style="background:#0f172a;border-radius:12px;padding:20px 24px;margin-bottom:28px;border-left:4px solid #f59e0b;">
        <p style="margin:0;color:#fcd34d;font-size:14px;">⚠️ This link will expire in <strong>24 hours</strong>. If you didn't request this, you can safely ignore this email.</p>
      </div>

      <div style="text-align:center;margin:32px 0;">
        <a href="{reset_url}" style="display:inline-block;background:linear-gradient(135deg,#10b981,#059669);color:#ffffff;text-decoration:none;font-size:16px;font-weight:700;padding:16px 40px;border-radius:12px;letter-spacing:0.5px;">
          Reset My Password →
        </a>
      </div>

      <p style="margin:28px 0 0;color:#475569;font-size:13px;line-height:1.6;">
        If the button doesn't work, copy and paste this link into your browser:<br>
        <a href="{reset_url}" style="color:#38bdf8;word-break:break-all;">{reset_url}</a>
      </p>

      <p style="margin:20px 0 0;color:#475569;font-size:12px;">
        If you did not request a password reset, your account is safe — no changes have been made.
      </p>
    """

# ---------------------------------------------------------------------------
# Core send function
# ---------------------------------------------------------------------------
def send_email(to_email, subject, html_body):
    """
    Attempts to send a real HTML email via SMTP.
    Falls back to printing the email to console if SMTP is not configured.
    Returns (success: bool, message: str)
    """
    cfg = get_smtp_config()

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
    cfg = get_smtp_config()
    from_name = cfg.get('smtp_from_name', 'University Attendance System')
    subject = f"You've been invited to {from_name}"
    body = _invitation_body(first_name, role, setup_url, from_name)
    return send_email(to_email, subject, body)

def send_password_reset_email(to_email, first_name, reset_url):
    cfg = get_smtp_config()
    from_name = cfg.get('smtp_from_name', 'University Attendance System')
    subject = f"Reset your password — {from_name}"
    body = _reset_body(first_name, reset_url, from_name)
    return send_email(to_email, subject, body)
