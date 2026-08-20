"""Resend email sender.

Calls Resend's HTTP API directly via httpx rather than pulling in their SDK —
it's a single POST with a bearer token, not worth an extra dependency.
"""

from __future__ import annotations

import httpx

from app.channels.base import ChannelSender, SendResult
from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

_RESEND_URL = "https://api.resend.com/emails"


class ResendChannel(ChannelSender):
    channel = "email"

    async def send(
        self, to: str, subject: str | None, body: str, *, case_id: str
    ) -> SendResult:
        payload = {
            "from": settings.email_from,
            "to": [to],
            "subject": subject or "A message about your account",
            "text": body,
        }
        if settings.email_reply_to:
            payload["reply_to"] = settings.email_reply_to

        headers = {"Authorization": f"Bearer {settings.resend_api_key}"}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(_RESEND_URL, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            log.warning("resend send failed  case_id=%s  error=%s", case_id, exc)
            return SendResult(succeeded=False, provider_message_id=None, error=str(exc))

        data = response.json()
        return SendResult(succeeded=True, provider_message_id=data.get("id"))
