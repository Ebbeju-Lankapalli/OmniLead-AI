"""Application-wide constants for OmniLead AI."""

from __future__ import annotations

APP_NAME = "OmniLead AI"
API_V1_PREFIX = "/api/v1"

DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_CURRENCY = "INR"

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

DEFAULT_FOLLOWUP_REMINDER_MINUTES = 30

DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60

DEFAULT_MAX_UPLOAD_SIZE_MB = 25

REQUEST_ID_HEADER = "X-Request-ID"

SUPPORTED_AUDIO_EXTENSIONS = frozenset(
    {
        "wav",
        "mp3",
        "m4a",
        "flac",
        "ogg",
        "webm",
    }
)

SUPPORTED_LEAD_SOURCES = frozenset(
    {
        "INSTAGRAM",
        "WHATSAPP",
        "META_AD_WHATSAPP",
        "PHONE",
        "REFERRAL",
        "WALK_IN",
        "MANUAL",
        "OTHER",
    }
)

SUPPORTED_CONVERSATION_CHANNELS = frozenset(
    {
        "INSTAGRAM",
        "WHATSAPP",
        "PHONE",
        "MANUAL",
        "OTHER",
    }
)

SUPPORTED_PURCHASE_INTENTS = frozenset(
    {
        "GENERAL_ENQUIRY",
        "POTENTIAL_LEAD",
        "HIGH_INTENT",
        "NOT_INTERESTED",
        "UNCERTAIN",
    }
)

SUPPORTED_USER_ROLES = frozenset(
    {
        "ADMIN",
        "SALES",
    }
)