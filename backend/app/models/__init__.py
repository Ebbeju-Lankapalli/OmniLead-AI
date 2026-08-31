"""SQLAlchemy model registry for OmniLead AI.

Importing this package registers every application model with SQLAlchemy's
shared declarative metadata. Alembic imports this module when generating
database migrations.
"""

from app.models.ai_analysis import AIAnalysis
from app.models.ai_feedback import AIFeedback
from app.models.audit_log import AuditLog
from app.models.call_recording import CallRecording
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.customer_identity import CustomerIdentity
from app.models.duplicate_candidate import DuplicateCandidate
from app.models.enquiry import Enquiry
from app.models.followup import FollowUp
from app.models.integration import Integration
from app.models.interaction import Interaction
from app.models.lead import Lead
from app.models.lead_assignment import LeadAssignment
from app.models.lead_status import LeadStatus
from app.models.note import Note
from app.models.notification import Notification
from app.models.objection import Objection
from app.models.organization import Organization
from app.models.product import Product
from app.models.user import User
from app.models.webhook_event import WebhookEvent

__all__ = [
    "AIAnalysis",
    "AIFeedback",
    "AuditLog",
    "CallRecording",
    "Conversation",
    "Customer",
    "CustomerIdentity",
    "DuplicateCandidate",
    "Enquiry",
    "FollowUp",
    "Integration",
    "Interaction",
    "Lead",
    "LeadAssignment",
    "LeadStatus",
    "Note",
    "Notification",
    "Objection",
    "Organization",
    "Product",
    "User",
    "WebhookEvent",
]
