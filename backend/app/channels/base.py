"""Outreach channel abstraction.

Mirrors the payment provider pattern: one interface, several drivers, and a
factory that degrades to a safe default (the simulated outbox) when a real
sender isn't configured. Nothing outside this package should import `resend`
or `smtplib` directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SendResult:
    succeeded: bool
    provider_message_id: str | None
    error: str | None = None


class ChannelSender(ABC):
    """Interface every outreach channel (email/SMS/WhatsApp) sender implements."""

    channel: str

    @abstractmethod
    async def send(
        self, to: str, subject: str | None, body: str, *, case_id: str
    ) -> SendResult:
        """Send one message. `subject` is None for channels without one (SMS/WhatsApp)."""
