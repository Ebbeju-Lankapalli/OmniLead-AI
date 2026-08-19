"""Repository exports for OmniLead AI data-access operations."""

from app.repositories.ai_analyses import (
    AIAnalysisRepository,
    AIFeedbackRepository,
)
from app.repositories.base import BaseRepository
from app.repositories.conversations import ConversationRepository
from app.repositories.customers import CustomerRepository
from app.repositories.enquiries import EnquiryRepository
from app.repositories.followups import FollowUpRepository
from app.repositories.interactions import InteractionRepository
from app.repositories.leads import LeadRepository
from app.repositories.notifications import NotificationRepository
from app.repositories.organizations import OrganizationRepository
from app.repositories.products import ProductRepository
from app.repositories.users import UserRepository

__all__ = [
    "AIFeedbackRepository",
    "AIAnalysisRepository",
    "BaseRepository",
    "ConversationRepository",
    "CustomerRepository",
    "EnquiryRepository",
    "FollowUpRepository",
    "InteractionRepository",
    "LeadRepository",
    "NotificationRepository",
    "OrganizationRepository",
    "ProductRepository",
    "UserRepository",
]
