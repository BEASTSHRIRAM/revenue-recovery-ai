"""Simulated outbox — the safe default for every channel.

No network call. Messages are already persisted to the `messages` table by
the recovery service before a sender is invoked; this driver's only job is to
report a believable send result so the pipeline behaves identically to a real
sender without actually contacting anyone.
"""

from __future__ import annotations

from app.channels.base import ChannelSender, SendResult
from app.core.ids import new_id


class SimulatedChannel(ChannelSender):
    def __init__(self, channel: str) -> None:
        self.channel = channel

    async def send(
        self, to: str, subject: str | None, body: str, *, case_id: str
    ) -> SendResult:
        return SendResult(succeeded=True, provider_message_id=new_id("simmsg"))
