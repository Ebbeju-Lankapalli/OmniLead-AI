"""Reusable database value types and normalization helpers."""

from __future__ import annotations

from enum import StrEnum
from typing import TypeVar


class UppercaseStrEnum(StrEnum):
    """
    Base class for stable string enums stored by their uppercase values.

    Application enums can inherit from this class while remaining compatible
    with JSON, Pydantic, SQLAlchemy, and PostgreSQL string-backed columns.
    """

    @classmethod
    def values(cls) -> tuple[str, ...]:
        """Return all enum values in declaration order."""

        return tuple(member.value for member in cls)


EnumType = TypeVar("EnumType", bound=UppercaseStrEnum)


def normalize_enum_value(value: str) -> str:
    """Normalize external enum-like values before validation."""

    return value.strip().upper().replace("-", "_").replace(" ", "_")


class UserRole(UppercaseStrEnum):
    ADMIN = "ADMIN"
    SALES = "SALES"


class LeadSource(UppercaseStrEnum):
    INSTAGRAM = "INSTAGRAM"
    WHATSAPP = "WHATSAPP"
    META_AD_WHATSAPP = "META_AD_WHATSAPP"
    PHONE = "PHONE"
    REFERRAL = "REFERRAL"
    WALK_IN = "WALK_IN"
    MANUAL = "MANUAL"
    OTHER = "OTHER"


class ConversationChannel(UppercaseStrEnum):
    INSTAGRAM = "INSTAGRAM"
    WHATSAPP = "WHATSAPP"
    PHONE = "PHONE"
    MANUAL = "MANUAL"
    OTHER = "OTHER"


class PurchaseIntent(UppercaseStrEnum):
    GENERAL_ENQUIRY = "GENERAL_ENQUIRY"
    POTENTIAL_LEAD = "POTENTIAL_LEAD"
    HIGH_INTENT = "HIGH_INTENT"
    NOT_INTERESTED = "NOT_INTERESTED"
    UNCERTAIN = "UNCERTAIN"


class EnquiryStatus(UppercaseStrEnum):
    NEW = "NEW"
    AI_ANALYZED = "AI_ANALYZED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONVERTED_TO_LEAD = "CONVERTED_TO_LEAD"
    GENERAL_ENQUIRY = "GENERAL_ENQUIRY"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class InteractionDirection(UppercaseStrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    INTERNAL = "INTERNAL"


class InteractionType(UppercaseStrEnum):
    MESSAGE = "MESSAGE"
    CALL = "CALL"
    CALL_NOTE = "CALL_NOTE"
    NOTE = "NOTE"
    STATUS_CHANGE = "STATUS_CHANGE"
    ASSIGNMENT = "ASSIGNMENT"
    FOLLOWUP_SCHEDULED = "FOLLOWUP_SCHEDULED"
    FOLLOWUP_COMPLETED = "FOLLOWUP_COMPLETED"
    EMAIL = "EMAIL"
    LEAD_CREATED = "LEAD_CREATED"
    AI_REVIEW = "AI_REVIEW"


class FollowUpType(UppercaseStrEnum):
    CALL = "CALL"
    WHATSAPP = "WHATSAPP"
    INSTAGRAM = "INSTAGRAM"
    EMAIL = "EMAIL"
    MEETING = "MEETING"
    OTHER = "OTHER"


class FollowUpStatus(UppercaseStrEnum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"
    OVERDUE = "OVERDUE"


class NotificationChannel(UppercaseStrEnum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"


class NotificationStatus(UppercaseStrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AIReviewDecision(UppercaseStrEnum):
    ACCEPTED = "ACCEPTED"
    EDITED = "EDITED"
    REJECTED = "REJECTED"
