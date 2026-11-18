"""SMTP ile e-posta (demo: Mailpit yakalar). HTML gövdede tüm kullanıcı metni escape edilir (T15)."""

import html
import smtplib
from email.message import EmailMessage

from app.config import get_settings


def send(
    to: str,
    subject: str,
    body: str,
    link_path: str | None = None,
    attachments: list[tuple[str, str, bytes]] | None = None,
) -> None:
    """attachments: (dosya adı, MIME türü, içerik)."""
    s = get_settings()
    msg = EmailMessage()
    msg["From"] = s.smtp_from
    msg["To"] = to
    msg["Subject"] = subject.replace("\r", " ").replace("\n", " ")[:200]
    link = f"{s.public_base_url.rstrip('/')}{link_path}" if link_path else s.public_base_url
    msg.set_content(f"{body}\n\nCyber Task Hub: {link}\n")
    msg.add_alternative(
        f"<p>{html.escape(body)}</p>"
        f'<p><a href="{html.escape(link, quote=True)}">Cyber Task Hub\'da aç</a></p>',
        subtype="html",
    )
    for name, mime, data in attachments or []:
        maintype, _, subtype = mime.partition("/")
        msg.add_attachment(data, maintype=maintype, subtype=subtype or "octet-stream", filename=name)
    with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=10) as smtp:
        smtp.send_message(msg)
