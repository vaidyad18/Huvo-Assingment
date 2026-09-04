from dataclasses import dataclass, field
from typing import Any


@dataclass
class LeadState:
    name: str | None = None
    configuration: str | None = None
    budget: str | None = None
    location_preference: str | None = None
    purchase_timeline: str | None = None
    interest_level: str = "unknown"

    site_visit_status: str = "not_requested"
    requested_visit_date: str | None = None
    requested_visit_time: str | None = None

    follow_up_required: bool = False
    follow_up_time: str | None = None

    human_escalation: bool = False
    opted_out: bool = False
    conversation_ended: bool = False


@dataclass
class Session:
    lead: LeadState = field(default_factory=LeadState)
    messages: list[dict[str, Any]] = field(default_factory=list)