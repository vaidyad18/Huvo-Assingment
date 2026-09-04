from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LeadState:
    name: Optional[str] = None
    configuration: Optional[str] = None
    budget: Optional[str] = None
    location_preference: Optional[str] = None
    purchase_timeline: Optional[str] = None
    interest_level: str = "unknown"
    site_visit_status: str = "not_requested"
    follow_up_required: bool = False
    follow_up_time: Optional[str] = None
    human_escalation: bool = False
    opted_out: bool = False
    conversation_ended: bool = False


@dataclass
class Session:
    messages: list[dict] = field(default_factory=list)
    lead: LeadState = field(default_factory=LeadState)
