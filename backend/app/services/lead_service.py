"""Lead business logic."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enquiry import Enquiry
from app.models.lead import Lead
from app.models.lead_status import LeadStatus
from app.models.product import Product
from app.repositories.customers import CustomerRepository
from app.repositories.enquiries import EnquiryRepository
from app.repositories.leads import LeadRepository
from app.repositories.products import ProductRepository
from app.schemas.lead import (
    LeadAIInsightUpdate,
    LeadCreate,
    LeadScoreUpdate,
    LeadStatusUpdate,
    LeadUpdate,
)
from app.services.assignment_service import AssignmentService


class LeadService:
    """Business operations for OmniLead AI sales leads."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.leads = LeadRepository(db)
        self.customers = CustomerRepository(db)
        self.products = ProductRepository(db)
        self.enquiries = EnquiryRepository(db)
        self.assignments = AssignmentService(db)

    def get(
        self,
        organization_id: UUID,
        lead_id: UUID,
    ) -> Lead:
        """Return an organization-scoped lead."""

        lead = self.leads.get(lead_id)

        if (
            lead is None
            or lead.organization_id != organization_id
        ):
            raise NotFoundError(
                "Lead not found.",
                details={
                    "lead_id": str(lead_id),
                },
            )

        return lead

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        status_id: UUID | None = None,
        assigned_to_user_id: UUID | None = None,
        customer_id: UUID | None = None,
        product_id: UUID | None = None,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Lead]:
        """Return filtered leads for one organization."""

        return self.leads.list_by_organization(
            organization_id,
            status_id=status_id,
            assigned_to_user_id=assigned_to_user_id,
            customer_id=customer_id,
            product_id=product_id,
            include_archived=include_archived,
            offset=offset,
            limit=limit,
        )

    def create(
        self,
        payload: LeadCreate,
        *,
        assigned_by_user_id: UUID | None = None,
        assignment_reason: str | None = None,
        commit: bool = True,
    ) -> Lead:
        """Create a validated sales lead."""

        self._validate_customer(
            payload.organization_id,
            payload.customer_id,
        )

        self._validate_status(
            payload.organization_id,
            payload.status_id,
        )

        if payload.product_id is not None:
            self._validate_product(
                payload.organization_id,
                payload.product_id,
            )

        if payload.source_enquiry_id is not None:
            enquiry = self._validate_enquiry(
                payload.organization_id,
                payload.source_enquiry_id,
            )

            existing = self.leads.get_by_source_enquiry(
                payload.organization_id,
                payload.source_enquiry_id,
            )

            if existing is not None:
                raise ConflictError(
                    "A lead has already been created from this enquiry.",
                    details={
                        "lead_id": str(existing.id),
                        "enquiry_id": str(
                            payload.source_enquiry_id
                        ),
                    },
                )

            if (
                enquiry.customer_id is not None
                and enquiry.customer_id != payload.customer_id
            ):
                raise ValidationError(
                    "Lead customer does not match the enquiry customer.",
                    details={
                        "enquiry_id": str(enquiry.id),
                        "enquiry_customer_id": str(
                            enquiry.customer_id
                        ),
                        "lead_customer_id": str(
                            payload.customer_id
                        ),
                    },
                )

        values = payload.model_dump()

        assigned_to_user_id = values.pop(
            "assigned_to_user_id",
            None,
        )

        lead = Lead(
            **values,
            assigned_to_user_id=None,
        )

        try:
            self.leads.add(lead)

            if assigned_to_user_id is not None:
                self.assignments.assign(
                    payload.organization_id,
                    lead.id,
                    assigned_to_user_id,
                    assigned_by_user_id=assigned_by_user_id,
                    reason=assignment_reason,
                    commit=False,
                )

            if commit:
                self.db.commit()
                self.db.refresh(lead)
            else:
                self.db.flush()

        except Exception:
            self.db.rollback()
            raise

        return lead

    def update(
        self,
        organization_id: UUID,
        lead_id: UUID,
        payload: LeadUpdate,
        *,
        assigned_by_user_id: UUID | None = None,
        assignment_reason: str | None = None,
    ) -> Lead:
        """Update mutable lead fields with organization validation."""

        lead = self.get(
            organization_id,
            lead_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return lead

        assignment_requested = (
            "assigned_to_user_id" in values
        )
        assigned_to_user_id = values.pop(
            "assigned_to_user_id",
            None,
        )

        if "status_id" in values:
            status_id = values["status_id"]

            if status_id is None:
                raise ValidationError(
                    "Lead status cannot be null."
                )

            status = self._validate_status(
                organization_id,
                status_id,
            )

            if status.is_terminal:
                values.setdefault(
                    "closed_at",
                    datetime.now().astimezone(),
                )
            elif lead.status.is_terminal:
                values.setdefault(
                    "closed_at",
                    None,
                )

        if "product_id" in values:
            product_id = values["product_id"]

            if product_id is not None:
                self._validate_product(
                    organization_id,
                    product_id,
                )

        if "source_enquiry_id" in values:
            enquiry_id = values["source_enquiry_id"]

            if enquiry_id is not None:
                enquiry = self._validate_enquiry(
                    organization_id,
                    enquiry_id,
                )

                existing = self.leads.get_by_source_enquiry(
                    organization_id,
                    enquiry_id,
                )

                if (
                    existing is not None
                    and existing.id != lead.id
                ):
                    raise ConflictError(
                        "Another lead already uses this source enquiry.",
                        details={
                            "lead_id": str(existing.id),
                            "enquiry_id": str(enquiry_id),
                        },
                    )

                if (
                    enquiry.customer_id is not None
                    and enquiry.customer_id != lead.customer_id
                ):
                    raise ValidationError(
                        "Lead customer does not match the enquiry customer."
                    )

        try:
            if values:
                self.leads.update(
                    lead,
                    **values,
                )

            if assignment_requested:
                if assigned_to_user_id is None:
                    self.assignments.unassign(
                        organization_id,
                        lead_id,
                        commit=False,
                    )
                else:
                    self.assignments.assign(
                        organization_id,
                        lead_id,
                        assigned_to_user_id,
                        assigned_by_user_id=assigned_by_user_id,
                        reason=assignment_reason,
                        commit=False,
                    )

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(lead)

        return lead

    def update_status(
        self,
        organization_id: UUID,
        lead_id: UUID,
        payload: LeadStatusUpdate,
    ) -> Lead:
        """Move a lead to another lifecycle status."""

        lead = self.get(
            organization_id,
            lead_id,
        )

        status = self._validate_status(
            organization_id,
            payload.status_id,
        )

        if status.is_terminal:
            closed_at = (
                payload.closed_at
                or datetime.now().astimezone()
            )
        else:
            closed_at = payload.closed_at

            if lead.status.is_terminal and closed_at is None:
                closed_at = None

        try:
            self.leads.update(
                lead,
                status_id=status.id,
                closed_at=closed_at,
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(lead)

        return lead

    def assign(
        self,
        organization_id: UUID,
        lead_id: UUID,
        assigned_to_user_id: UUID,
        *,
        assigned_by_user_id: UUID | None = None,
        reason: str | None = None,
    ) -> Lead:
        """Assign a lead through the assignment-history service."""

        return self.assignments.assign(
            organization_id,
            lead_id,
            assigned_to_user_id,
            assigned_by_user_id=assigned_by_user_id,
            reason=reason,
            commit=True,
        )

    def unassign(
        self,
        organization_id: UUID,
        lead_id: UUID,
    ) -> Lead:
        """Remove current lead ownership."""

        return self.assignments.unassign(
            organization_id,
            lead_id,
            commit=True,
        )

    def update_scores(
        self,
        organization_id: UUID,
        lead_id: UUID,
        payload: LeadScoreUpdate,
    ) -> Lead:
        """Update explainable lead and priority scores."""

        lead = self.get(
            organization_id,
            lead_id,
        )

        try:
            self.leads.update(
                lead,
                **payload.model_dump(),
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(lead)

        return lead

    def update_ai_insights(
        self,
        organization_id: UUID,
        lead_id: UUID,
        payload: LeadAIInsightUpdate,
    ) -> Lead:
        """Update AI-generated lead intelligence."""

        lead = self.get(
            organization_id,
            lead_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return lead

        try:
            self.leads.update(
                lead,
                **values,
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(lead)

        return lead

    def set_next_followup(
        self,
        organization_id: UUID,
        lead_id: UUID,
        next_followup_at: datetime | None,
    ) -> Lead:
        """Synchronize the lead's next follow-up timestamp."""

        lead = self.get(
            organization_id,
            lead_id,
        )

        try:
            self.leads.update(
                lead,
                next_followup_at=next_followup_at,
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(lead)

        return lead

    def touch_last_contact(
        self,
        organization_id: UUID,
        lead_id: UUID,
        contacted_at: datetime,
    ) -> Lead:
        """Update the lead's latest customer-contact timestamp."""

        lead = self.get(
            organization_id,
            lead_id,
        )

        try:
            self.leads.update(
                lead,
                last_contact_at=contacted_at,
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(lead)

        return lead

    def archive(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        archived_at: datetime | None = None,
    ) -> Lead:
        """Archive a lead without deleting its history."""

        lead = self.get(
            organization_id,
            lead_id,
        )

        if lead.archived_at is not None:
            return lead

        try:
            self.leads.update(
                lead,
                archived_at=(
                    archived_at
                    or datetime.now().astimezone()
                ),
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(lead)

        return lead

    def restore(
        self,
        organization_id: UUID,
        lead_id: UUID,
    ) -> Lead:
        """Restore an archived lead."""

        lead = self.get(
            organization_id,
            lead_id,
        )

        if lead.archived_at is None:
            return lead

        try:
            self.leads.update(
                lead,
                archived_at=None,
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(lead)

        return lead

    def list_priority_queue(
        self,
        organization_id: UUID,
        *,
        minimum_priority_score: int = 0,
        limit: int = 50,
    ) -> Sequence[Lead]:
        """Return the organization's highest-priority active leads."""

        return self.leads.list_priority_queue(
            organization_id,
            minimum_priority_score=minimum_priority_score,
            limit=limit,
        )

    def _validate_customer(
        self,
        organization_id: UUID,
        customer_id: UUID,
    ) -> None:
        customer = self.customers.get(customer_id)

        if (
            customer is None
            or customer.organization_id != organization_id
        ):
            raise NotFoundError(
                "Customer not found.",
                details={
                    "customer_id": str(customer_id),
                },
            )

    def _validate_status(
        self,
        organization_id: UUID,
        status_id: UUID,
    ) -> LeadStatus:
        status = self.db.get(
            LeadStatus,
            status_id,
        )

        if (
            status is None
            or status.organization_id != organization_id
        ):
            raise NotFoundError(
                "Lead status not found.",
                details={
                    "status_id": str(status_id),
                },
            )

        if not status.is_active:
            raise ValidationError(
                "Inactive lead status cannot be assigned.",
                details={
                    "status_id": str(status_id),
                },
            )

        return status

    def _validate_product(
        self,
        organization_id: UUID,
        product_id: UUID,
    ) -> Product:
        product = self.products.get(product_id)

        if (
            product is None
            or product.organization_id != organization_id
        ):
            raise NotFoundError(
                "Product not found.",
                details={
                    "product_id": str(product_id),
                },
            )

        if not product.is_active:
            raise ValidationError(
                "Inactive product cannot be assigned to a lead.",
                details={
                    "product_id": str(product_id),
                },
            )

        return product

    def _validate_enquiry(
        self,
        organization_id: UUID,
        enquiry_id: UUID,
    ) -> Enquiry:
        enquiry = self.enquiries.get(enquiry_id)

        if (
            enquiry is None
            or enquiry.organization_id != organization_id
        ):
            raise NotFoundError(
                "Enquiry not found.",
                details={
                    "enquiry_id": str(enquiry_id),
                },
            )

        return enquiry
