"""Structured lead search business logic."""

from __future__ import annotations

import math

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.ai.retrieval.semantic_search import (
    LeadSemanticSearchService,
)
from app.core.config import settings
from app.core.exceptions import ValidationError
from app.models.customer import Customer
from app.models.lead import Lead
from app.models.lead_status import LeadStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.search import (
    LeadSearchFilters,
    LeadSearchResult,
    SearchRequest,
    SearchResponse,
    SearchSort,
)


class SearchService:
    """Execute safe structured lead searches."""

    SORTABLE_FIELDS = {
        "priority_score": Lead.priority_score,
        "lead_score": Lead.lead_score,
        "followup_risk_score": Lead.followup_risk_score,
        "next_followup_at": Lead.next_followup_at,
        "last_contact_at": Lead.last_contact_at,
        "created_at": Lead.created_at,
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:
        """Search leads using validated structured filters."""

        statement = (
            select(
                Lead,
                Customer,
                LeadStatus,
                Product,
                User,
            )
            .join(
                Customer,
                Customer.id == Lead.customer_id,
            )
            .join(
                LeadStatus,
                LeadStatus.id == Lead.status_id,
            )
            .outerjoin(
                Product,
                Product.id == Lead.product_id,
            )
            .outerjoin(
                User,
                User.id == Lead.assigned_to_user_id,
            )
            .where(
                Lead.organization_id == request.organization_id,
                Customer.organization_id == request.organization_id,
                LeadStatus.organization_id == request.organization_id,
            )
        )

        statement = self._apply_filters(
            statement,
            request.filters,
        )

        if request.semantic_search:
            return self._semantic_search(
                request,
                statement,
            )

        count_statement = select(
            func.count()
        ).select_from(
            statement.order_by(None).subquery()
        )

        total_items = int(
            self.db.scalar(count_statement)
            or 0
        )

        statement = self._apply_sort(
            statement,
            request.sort,
        )

        offset = (
            request.page - 1
        ) * request.page_size

        rows = self.db.execute(
            statement
            .offset(offset)
            .limit(request.page_size)
        ).all()

        results = [
            self._to_result(
                lead=lead,
                customer=customer,
                status=status,
                product=product,
                assignee=assignee,
            )
            for (
                lead,
                customer,
                status,
                product,
                assignee,
            ) in rows
        ]

        total_pages = (
            math.ceil(
                total_items
                / request.page_size
            )
            if total_items
            else 0
        )

        return SearchResponse(
            query=request.query,
            filters=request.filters,
            sort=request.sort,
            results=results,
            page=request.page,
            page_size=request.page_size,
            total_items=total_items,
            total_pages=total_pages,
            semantic_search_used=False,
            metadata={
                "structured_search": True,
            },
        )

    def _semantic_search(
        self,
        request: SearchRequest,
        statement,
    ) -> SearchResponse:
        """Combine semantic interaction retrieval with lead filters."""

        if not settings.SEMANTIC_SEARCH_ENABLED:
            raise ValidationError(
                "Semantic search is not enabled."
            )

        if not request.query:
            raise ValidationError(
                "A search query is required for semantic search."
            )

        similarities = LeadSemanticSearchService(
            self.db
        ).search(
            request.organization_id,
            request.query,
            limit=request.semantic_limit,
        )

        if not similarities:
            return SearchResponse(
                query=request.query,
                filters=request.filters,
                sort=request.sort,
                results=[],
                page=request.page,
                page_size=request.page_size,
                total_items=0,
                total_pages=0,
                semantic_search_used=True,
                metadata={
                    "structured_search": True,
                    "semantic_search": True,
                    "semantic_candidate_leads": 0,
                },
            )

        statement = statement.where(
            Lead.id.in_(
                list(similarities)
            )
        )

        rows = self.db.execute(
            statement
        ).all()

        results = [
            self._to_result(
                lead=lead,
                customer=customer,
                status=status,
                product=product,
                assignee=assignee,
                semantic_similarity=(
                    similarities.get(
                        lead.id
                    )
                ),
            )
            for (
                lead,
                customer,
                status,
                product,
                assignee,
            ) in rows
        ]

        results.sort(
            key=lambda item: (
                item.semantic_similarity
                if item.semantic_similarity
                is not None
                else -1.0
            ),
            reverse=True,
        )

        total_items = len(results)

        total_pages = (
            math.ceil(
                total_items
                / request.page_size
            )
            if total_items
            else 0
        )

        offset = (
            request.page - 1
        ) * request.page_size

        paginated = results[
            offset:
            offset + request.page_size
        ]

        return SearchResponse(
            query=request.query,
            filters=request.filters,
            sort=request.sort,
            results=paginated,
            page=request.page,
            page_size=request.page_size,
            total_items=total_items,
            total_pages=total_pages,
            semantic_search_used=True,
            metadata={
                "structured_search": True,
                "semantic_search": True,
                "semantic_candidate_leads": len(
                    similarities
                ),
                "semantic_ranking": (
                    "cosine_similarity_desc"
                ),
            },
        )

    def _apply_filters(
        self,
        statement,
        filters: LeadSearchFilters,
    ):
        """Apply validated lead filters."""

        if filters.sources:
            statement = statement.where(
                Lead.source.in_(
                    source.value
                    for source in filters.sources
                )
            )

        if filters.original_sources:
            statement = statement.where(
                Lead.original_source.in_(
                    source.value
                    for source in filters.original_sources
                )
            )

        if filters.purchase_intents:
            statement = statement.where(
                Lead.purchase_intent.in_(
                    intent.value
                    for intent in filters.purchase_intents
                )
            )

        if filters.status_ids:
            statement = statement.where(
                Lead.status_id.in_(
                    filters.status_ids
                )
            )

        if filters.assigned_to_user_ids:
            statement = statement.where(
                Lead.assigned_to_user_id.in_(
                    filters.assigned_to_user_ids
                )
            )

        if filters.product_ids:
            statement = statement.where(
                Lead.product_id.in_(
                    filters.product_ids
                )
            )

        if filters.customer_ids:
            statement = statement.where(
                Lead.customer_id.in_(
                    filters.customer_ids
                )
            )

        statement = self._apply_score_range(
            statement,
            Lead.lead_score,
            filters.lead_score,
        )

        statement = self._apply_score_range(
            statement,
            Lead.priority_score,
            filters.priority_score,
        )

        statement = self._apply_score_range(
            statement,
            Lead.followup_risk_score,
            filters.followup_risk_score,
        )

        if filters.next_followup_at is not None:
            if filters.next_followup_at.start is not None:
                statement = statement.where(
                    Lead.next_followup_at
                    >= filters.next_followup_at.start
                )

            if filters.next_followup_at.end is not None:
                statement = statement.where(
                    Lead.next_followup_at
                    <= filters.next_followup_at.end
                )

        if filters.last_contact_at is not None:
            if filters.last_contact_at.start is not None:
                statement = statement.where(
                    Lead.last_contact_at
                    >= filters.last_contact_at.start
                )

            if filters.last_contact_at.end is not None:
                statement = statement.where(
                    Lead.last_contact_at
                    <= filters.last_contact_at.end
                )

        if filters.tags:
            for tag in filters.tags:
                statement = statement.where(
                    Lead.tags.contains(
                        [tag]
                    )
                )

        if filters.has_assignee is True:
            statement = statement.where(
                Lead.assigned_to_user_id.is_not(None)
            )
        elif filters.has_assignee is False:
            statement = statement.where(
                Lead.assigned_to_user_id.is_(None)
            )

        if filters.has_next_followup is True:
            statement = statement.where(
                Lead.next_followup_at.is_not(None)
            )
        elif filters.has_next_followup is False:
            statement = statement.where(
                Lead.next_followup_at.is_(None)
            )

        if filters.is_archived is True:
            statement = statement.where(
                Lead.archived_at.is_not(None)
            )
        elif filters.is_archived is False:
            statement = statement.where(
                Lead.archived_at.is_(None)
            )

        return statement

    @staticmethod
    def _apply_score_range(
        statement,
        column,
        score_range,
    ):
        """Apply an optional inclusive score range."""

        if score_range is None:
            return statement

        if score_range.minimum is not None:
            statement = statement.where(
                column >= score_range.minimum
            )

        if score_range.maximum is not None:
            statement = statement.where(
                column <= score_range.maximum
            )

        return statement

    def _apply_sort(
        self,
        statement,
        sort: SearchSort,
    ):
        """Apply allow-listed deterministic sorting."""

        column = self.SORTABLE_FIELDS.get(
            sort.field,
            Lead.priority_score,
        )

        ordering = (
            asc(column)
            if sort.direction == "asc"
            else desc(column)
        )

        return statement.order_by(
            ordering.nullslast(),
            Lead.id,
        )

    @staticmethod
    def _to_result(
        *,
        lead: Lead,
        customer: Customer,
        status: LeadStatus,
        product: Product | None,
        assignee: User | None,
        semantic_similarity: float | None = None,
    ) -> LeadSearchResult:
        """Convert a joined database row into an API search result."""

        return LeadSearchResult(
            lead_id=lead.id,
            customer_id=lead.customer_id,
            customer_name=customer.full_name,
            company_name=customer.company_name,
            primary_phone=customer.primary_phone,
            primary_email=customer.primary_email,
            product_id=lead.product_id,
            product_name=(
                product.name
                if product is not None
                else None
            ),
            status_id=lead.status_id,
            status_name=status.name,
            assigned_to_user_id=lead.assigned_to_user_id,
            assigned_to_name=(
                assignee.full_name
                if assignee is not None
                else None
            ),
            source=lead.source,
            original_source=lead.original_source,
            purchase_intent=lead.purchase_intent,
            requirement=lead.requirement,
            qualification_summary=lead.qualification_summary,
            conversation_summary=lead.conversation_summary,
            lead_score=lead.lead_score,
            priority_score=lead.priority_score,
            followup_risk_score=lead.followup_risk_score,
            next_best_action=lead.next_best_action,
            next_followup_at=lead.next_followup_at,
            last_contact_at=lead.last_contact_at,
            tags=lead.tags,
            semantic_similarity=semantic_similarity,
        )
