"""SMTP email sender — the fallback real-send path when Resend isn't configured.

Runs the blocking `smtplib` call in a thread via `asyncio.to_thread` so it
doesn't block the event loop; there is no good async SMTP client worth adding
as a dependency for this.
"""

from __future__ import annotations

import asyncio
import smtplib
from email.mime.text import MIMEText

from app.channels.base import ChannelSender, SendResult
from app.core.config import settings
from app.core.ids import new_id
from app.core.logging import get_logger

log = get_logger(__name__)


def _send_sync(to: str, subject: str, body: str) -> None:
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.email_from
    message["To"] = to
    if settings.email_reply_to:
        message["Reply-To"] = settings.email_reply_to

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_starttls:
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.email_from, [to], message.as_string())


class SmtpChannel(ChannelSender):
    channel = "email"

    async def send(
        self, to: str, subject: str | None, body: str, *, case_id: str
    ) -> SendResult:
        try:
            await asyncio.to_thread(
                _send_sync, to, subject or "A message about your account", body
            )
        except (smtplib.SMTPException, OSError) as exc:
            log.warning("smtp send failed  case_id=%s  error=%s", case_id, exc)
            return SendResult(succeeded=False, provider_message_id=None, error=str(exc))

        return SendResult(succeeded=True, provider_message_id=new_id("smtpmsg"))
