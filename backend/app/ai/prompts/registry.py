"""Versioned prompt registry for OmniLead AI workflows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromptDefinition:
    """One immutable versioned AI prompt."""

    name: str
    version: str
    system_instruction: str
    template: str
    temperature: float = 0.2

    def render(self, **values: object) -> str:
        """Render the prompt template with named values."""

        try:
            rendered = self.template.format(**values)
        except KeyError as exc:
            missing = str(exc).strip("'")

            raise ValueError(
                f"Missing prompt variable: {missing}"
            ) from exc

        cleaned = rendered.strip()

        if not cleaned:
            raise ValueError(
                "Rendered prompt cannot be empty."
            )

        return cleaned


PROMPT_REGISTRY: dict[str, PromptDefinition] = {
    "INTENT_ANALYSIS": PromptDefinition(
        name="intent_analysis",
        version="1.0",
        system_instruction=(
            "You are the purchase-intent classification component "
            "of OmniLead AI. Classify only from evidence in the "
            "customer communication. Do not invent facts."
        ),
        template=(
            "Analyze the following customer communication and classify "
            "its purchase intent.\n\n"
            "Customer communication:\n"
            "{content}\n\n"
            "Return structured evidence, confidence, buying signals, "
            "and negative signals."
        ),
        temperature=0.1,
    ),
    "LEAD_QUALIFICATION": PromptDefinition(
        name="lead_qualification",
        version="1.0",
        system_instruction=(
            "You are the lead-qualification component of OmniLead AI. "
            "Use only supplied customer evidence and clearly distinguish "
            "known facts from unavailable information."
        ),
        template=(
            "Qualify this potential sales lead.\n\n"
            "Customer communication:\n"
            "{content}\n\n"
            "Known customer context:\n"
            "{customer_context}\n\n"
            "Known product context:\n"
            "{product_context}\n\n"
            "Evaluate requirement clarity, urgency, budget, authority, "
            "timeline, qualification reasons, and disqualification reasons."
        ),
        temperature=0.15,
    ),
    "NEXT_ACTION": PromptDefinition(
        name="next_action",
        version="1.0",
        system_instruction=(
            "You are the next-best-action recommendation component "
            "of OmniLead AI. Recommend a practical sales action based "
            "only on the provided evidence."
        ),
        template=(
            "Recommend the next best sales action.\n\n"
            "Lead context:\n"
            "{lead_context}\n\n"
            "Recent conversation:\n"
            "{conversation_context}\n\n"
            "Return the action, reason, confidence, optional suggested "
            "message, priority, and recommended follow-up delay."
        ),
        temperature=0.2,
    ),
    "CONVERSATION_SUMMARY": PromptDefinition(
        name="conversation_summary",
        version="1.0",
        system_instruction=(
            "You summarize sales conversations for OmniLead AI. "
            "Preserve important customer facts, requirements, commitments, "
            "and unresolved questions without inventing information."
        ),
        template=(
            "Summarize the following conversation.\n\n"
            "{conversation}\n\n"
            "Include key points, customer requirements, commitments, "
            "and unresolved questions."
        ),
        temperature=0.1,
    ),
    "EXTRACTION": PromptDefinition(
        name="extraction",
        version="1.0",
        system_instruction=(
            "You extract customer and enquiry entities for OmniLead AI. "
            "Return null when information is not present. Never guess "
            "phone numbers, emails, budgets, products, or identities."
        ),
        template=(
            "Extract structured customer and enquiry information from:\n\n"
            "{content}"
        ),
        temperature=0.0,
    ),
    "OBJECTION_ANALYSIS": PromptDefinition(
        name="objection_analysis",
        version="1.0",
        system_instruction=(
            "You detect sales objections for OmniLead AI. "
            "Only identify objections explicitly supported by the text."
        ),
        template=(
            "Analyze customer objections in this communication:\n\n"
            "{content}\n\n"
            "Identify objection categories, severity, and helpful "
            "non-deceptive response suggestions."
        ),
        temperature=0.15,
    ),
    "FOLLOWUP_RECOMMENDATION": PromptDefinition(
        name="followup_recommendation",
        version="1.0",
        system_instruction=(
            "You recommend sales follow-ups for OmniLead AI. "
            "Use the supplied evidence and avoid excessive or manipulative "
            "follow-up recommendations."
        ),
        template=(
            "Recommend whether and how to follow up.\n\n"
            "Lead context:\n"
            "{lead_context}\n\n"
            "Conversation context:\n"
            "{conversation_context}"
        ),
        temperature=0.2,
    ),
    "ENQUIRY_TRIAGE": PromptDefinition(
        name="enquiry_triage",
        version="1.0",
        system_instruction=(
            "You are the automatic enquiry-triage component of OmniLead AI. "
            "Classify incoming customer enquiries using only the supplied "
            "message evidence. Decide whether the enquiry should become a "
            "sales lead, remain a general enquiry, or require human review. "
            "Never invent customer requirements, budget, urgency, identity, "
            "or purchase intent."
        ),
        template=(
            "Triage the following incoming customer enquiry.\n\n"
            "Customer enquiry:\n"
            "{content}\n\n"
            "Customer context:\n"
            "{customer_context}\n\n"
            "Determine the appropriate triage decision, confidence, reasoning, "
            "customer requirement, sales signals, general-enquiry signals, "
            "and any ambiguity requiring human review. Use only evidence "
            "present in the provided information."
        ),
        temperature=0.1,
    ),
    "NATURAL_LANGUAGE_SEARCH": PromptDefinition(
        name="natural_language_search",
        version="1.0",
        system_instruction=(
            "You convert natural-language CRM lead-search requests into "
            "safe structured filters for OmniLead AI. Never generate SQL. "
            "Only use supported structured fields. Do not invent IDs."
        ),
        template=(
            "Convert this lead-search request into structured filters.\n\n"
            "Search request:\n"
            "{query}\n\n"
            "Current time:\n"
            "{current_time}\n\n"
            "Supported sources include INSTAGRAM, WHATSAPP, "
            "META_AD_WHATSAPP, PHONE, REFERRAL, WALK_IN, MANUAL, OTHER.\n"
            "Supported purchase intents include GENERAL_ENQUIRY, "
            "POTENTIAL_LEAD, HIGH_INTENT, NOT_INTERESTED, UNCERTAIN.\n\n"
            "Interpret score thresholds, assignment state, follow-up state, "
            "date ranges, tags, sorting, and whether semantic search is useful. "
            "Only populate tags when the user explicitly asks for CRM tags or "
            "tagged leads. Do not convert ordinary concepts, interests, products, "
            "requirements, industries, or semantic keywords into tag filters."
        ),
        temperature=0.0,
    ),
    "CALL_ANALYSIS": PromptDefinition(
        name="call_analysis",
        version="1.1",
        system_instruction=(
            "You analyze call transcripts for OmniLead AI. "
            "Use only the transcript. Extract customer intent, requirements, "
            "objections, commitments, questions, and action items. "
            "Preserve monetary amounts exactly and consistently. "
            "For Indian currency, remember: 1 lakh = 100,000 INR and "
            "1 crore = 10,000,000 INR. Never provide a numeric conversion "
            "that conflicts with the stated lakh or crore amount. "
            "If speech recognition produces an ambiguous monetary phrase, "
            "prefer the contextually supported Indian-numbering interpretation "
            "and do not invent unsupported precision."
        ),
        template=(
            "Analyze this call transcript:\n\n"
            "{transcript}\n\n"
            "Important currency rules:\n"
            "- 1 lakh = 100,000 INR.\n"
            "- 3 lakh = 300,000 INR.\n"
            "- 3.25 lakh = 325,000 INR.\n"
            "- 1 crore = 10,000,000 INR.\n"
            "- Keep all monetary representations internally consistent.\n"
            "- Do not convert an amount if the conversion is uncertain."
        ),
        temperature=0.1,
    ),
}


def get_prompt(
    analysis_type: str,
) -> PromptDefinition:
    """Return a registered prompt by normalized analysis type."""

    normalized = (
        analysis_type.strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )

    prompt = PROMPT_REGISTRY.get(normalized)

    if prompt is None:
        raise KeyError(
            f"Unsupported AI analysis type: {normalized}"
        )

    return prompt
