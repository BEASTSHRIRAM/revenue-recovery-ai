"""Channel sender registry — one factory per channel, degrades safely."""

from __future__ import annotations

from functools import lru_cache

from app.channels.base import ChannelSender, SendResult
from app.channels.simulated import SimulatedChannel
from app.core.config import settings

__all__ = ["ChannelSender", "SendResult", "get_channel_sender"]


@lru_cache
def get_channel_sender(channel: str) -> ChannelSender:
    """Return the configured sender for `channel` (email/sms/whatsapp).

    Only email has a real driver today (Resend, then SMTP); SMS and WhatsApp
    always simulate, matching the product decision to draft-but-not-send those
    channels for now while keeping the same interface ready for a real driver.
    """
    if channel == "email" and settings.effective_email_channel == "resend":
        from app.channels.resend_channel import ResendChannel

        return ResendChannel()
    if channel == "email" and settings.effective_email_channel == "smtp":
        from app.channels.smtp_channel import SmtpChannel

        return SmtpChannel()
    return SimulatedChannel(channel)
