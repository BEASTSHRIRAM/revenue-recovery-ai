"""Application settings.

Every credential is optional. The platform is designed to run end-to-end with an
empty .env: the payment provider falls back to a mock driver, email falls back to
a simulated outbox, and the agent falls back to a deterministic stub. Adding a key
upgrades a subsystem in place without touching code.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PaymentProviderName = Literal["mock", "razorpay"]
EmailChannelName = Literal["simulated", "resend", "smtp"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---------- app ----------
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    link_signing_secret: str = "change-me-in-production"
    public_app_url: str = "http://localhost:3000"

    # ---------- database ----------
    database_url: str = "sqlite+aiosqlite:///./recovery.db"
    checkpoint_db: str = "./checkpoints.sqlite"

    # ---------- groq ----------
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"
    groq_temperature: float = 0.2
    groq_max_retries: int = 2
    groq_timeout_seconds: int = 60

    # ---------- payments ----------
    payment_provider: PaymentProviderName = "mock"
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    razorpay_webhook_secret: str | None = None

    # ---------- email ----------
    email_channel: EmailChannelName = "simulated"
    email_from: str = "Billing <billing@example.com>"
    email_reply_to: str | None = None
    resend_api_key: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_starttls: bool = True

    # ---------- outreach safety rails ----------
    # Hard limits enforced in code; the agent cannot argue its way past these.
    max_messages_per_customer_per_week: int = 3
    max_retries_per_case: int = 4
    require_human_approval: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept CORS_ORIGINS as a comma-separated string from the environment."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # ---------- derived capability flags ----------
    @property
    def groq_enabled(self) -> bool:
        """True when a real Groq key is present; otherwise the agent uses its stub brain."""
        return bool(self.groq_api_key and self.groq_api_key.strip())

    @property
    def razorpay_enabled(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)

    @property
    def effective_payment_provider(self) -> PaymentProviderName:
        """Never hand back `razorpay` without credentials — degrade to mock instead."""
        if self.payment_provider == "razorpay" and not self.razorpay_enabled:
            return "mock"
        return self.payment_provider

    @property
    def effective_email_channel(self) -> EmailChannelName:
        """Degrade to the simulated outbox when the chosen sender is unconfigured."""
        if self.email_channel == "resend" and not self.resend_api_key:
            return "simulated"
        if self.email_channel == "smtp" and not self.smtp_host:
            return "simulated"
        return self.email_channel

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Process-wide settings singleton. Cached so .env is parsed once."""
    return Settings()


settings = get_settings()
