import re
from datetime import datetime
from typing import Any

from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_MODEL
from .prompt import SYSTEM_PROMPT
from .schemas import LeadState, Session


class BookingSimulator:
    def book(self, date: str, time: str) -> dict[str, Any]:

        if time == "00:00":
            return {
                "success": False,
                "reason": "The requested slot is unavailable.",
            }

        if "fail" in f"{date} {time}".lower():
            return {
                "success": False,
                "reason": "The requested slot is unavailable.",
            }

        return {
            "success": True,
            "date": date,
            "time": time,
            "booking_id": "NS-DEMO-" + datetime.now().strftime("%H%M%S"),
        }


class ConversationService:

    def __init__(self):
        self.sessions: dict[str, Session] = {}
        self.booking = BookingSimulator()

        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. Add it to your .env file."
            )

        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def get_session(self, session_id: str) -> Session:

        if session_id not in self.sessions:
            self.sessions[session_id] = Session()

        return self.sessions[session_id]

    def reset(self, session_id: str):
        self.sessions.pop(session_id, None)

    def _extract_name(self, text: str) -> str | None:

        patterns = [
            r"\bmy name is ([a-zA-Z][a-zA-Z ]{1,30})",
            r"\bi am ([a-zA-Z][a-zA-Z ]{1,30})",
            r"\bi'm ([a-zA-Z][a-zA-Z ]{1,30})",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:

                name = match.group(1).strip()

                name = re.split(
                    r"\b(and|but|i|looking|interested|from|with)\b",
                    name,
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )[0].strip()

                if name:
                    return name.title()

        return None

    def _heuristic_update(
        self,
        lead: LeadState,
        text: str,
    ):

        lower = text.lower()

        if re.search(r"\b2\s*bhk\b", lower):
            lead.configuration = "2 BHK"

        elif re.search(r"\b3\s*bhk\b", lower):
            lead.configuration = "3 BHK"

        name = self._extract_name(text)

        if name:
            lead.name = name

        if any(
            phrase in lower
            for phrase in [
                "don't contact",
                "do not contact",
                "stop calling",
                "stop contacting",
                "unsubscribe",
                "no more calls",
                "don't call",
                "do not call",
                "remove me",
            ]
        ):
            lead.opted_out = True
            lead.conversation_ended = True

        if any(
            phrase in lower
            for phrase in [
                "human",
                "agent",
                "representative",
                "sales person",
                "salesperson",
                "talk to sales",
            ]
        ):
            lead.human_escalation = True

        if any(
            phrase in lower
            for phrase in [
                "later",
                "tomorrow",
                "next week",
                "next month",
                "busy",
                "call me later",
                "contact me later",
            ]
        ):
            lead.follow_up_required = True

            if "tomorrow" in lower:
                lead.follow_up_time = "tomorrow"

            elif "next week" in lower:
                lead.follow_up_time = "next week"

            elif "next month" in lower:
                lead.follow_up_time = "next month"

            else:
                lead.follow_up_time = "later"

        if any(
            phrase in lower
            for phrase in [
                "site visit",
                "visit the site",
                "schedule a visit",
                "let's visit",
                "lets visit",
                "want to visit",
                "visit the property",
            ]
        ):
            if lead.site_visit_status == "not_requested":
                lead.site_visit_status = "requested"

        if any(
            phrase in lower
            for phrase in [
                "not interested",
                "no thanks",
                "just looking",
                "not looking",
                "don't want to buy",
                "do not want to buy",
            ]
        ):
            lead.interest_level = "low"

        elif any(
            phrase in lower
            for phrase in [
                "very interested",
                "interested",
                "looking for",
                "looking to buy",
                "want to buy",
                "want to purchase",
                "planning to buy",
                "plan to buy",
                "ready to buy",
                "ready to purchase",
                "i want",
                "i need",
                "book",
                "schedule",
            ]
        ):
            lead.interest_level = "high"

        elif any(
            phrase in lower
            for phrase in [
                "maybe",
                "thinking",
                "considering",
                "not sure",
            ]
        ):
            lead.interest_level = "medium"

        crore = re.search(
            r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:crores?|cr)\b",
            lower,
        )

        lakh = re.search(
            r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?|lac)\b",
            lower,
        )

        if crore:
            lead.budget = f"₹{crore.group(1)} crore"

        elif lakh:
            lead.budget = f"₹{lakh.group(1)} lakh"

    def _lead_context(
        self,
        lead: LeadState,
    ) -> str:

        return f"""
CURRENT LEAD MEMORY

Name: {lead.name or "Unknown"}
Configuration: {lead.configuration or "Unknown"}
Budget: {lead.budget or "Unknown"}
Location preference: {lead.location_preference or "Unknown"}
Purchase timeline: {lead.purchase_timeline or "Unknown"}
Interest level: {lead.interest_level}

Site visit status: {lead.site_visit_status}
Requested visit date: {lead.requested_visit_date or "Unknown"}
Requested visit time: {lead.requested_visit_time or "Unknown"}

Follow-up required: {lead.follow_up_required}
Follow-up time: {lead.follow_up_time or "Unknown"}
Human escalation: {lead.human_escalation}
Opted out: {lead.opted_out}

Use this information as reliable conversation memory.

Do not ask again for information that is already known.

If configuration and budget are known, use both when responding.

If a site visit date and time are already known and the application has
confirmed the booking, treat the booking status as authoritative.
"""

    def _conversation_for_gemini(
        self,
        session: Session,
    ):

        contents = []

        for message in session.messages[-20:]:

            role = (
                "user"
                if message["role"] == "user"
                else "model"
            )

            contents.append(
                types.Content(
                    role=role,
                    parts=[
                        types.Part.from_text(
                            text=message["content"]
                        )
                    ],
                )
            )

        return contents

    async def _ai_reply(
        self,
        session: Session,
        application_context: str | None = None,
    ) -> str:

        contents = self._conversation_for_gemini(
            session
        )

        system_instruction = (
            SYSTEM_PROMPT
            + "\n\n"
            + self._lead_context(session.lead)
        )

        if application_context:

            system_instruction += (
                "\n\nAPPLICATION CONTEXT:\n"
                + application_context
            )

        response = await self.client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=300,
                thinking_config=types.ThinkingConfig(
                    thinking_level="minimal"
                ),
            ),
        )

        reply = (response.text or "").strip()

        if not reply:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return reply

    def _extract_visit_datetime(
        self,
        text: str,
    ) -> tuple[str | None, str | None]:

        date_match = re.search(
            r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b",
            text,
        )

        time_match = re.search(
            r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b",
            text.lower(),
        )

        date = None
        time = None

        if date_match:

            date = date_match.group(1).replace(
                "/",
                "-",
            )

        if time_match:

            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            meridiem = time_match.group(3)

            if meridiem == "pm" and hour < 12:
                hour += 12

            elif meridiem == "am" and hour == 12:
                hour = 0

            time = f"{hour:02d}:{minute:02d}"

        return date, time

    def _maybe_booking_context(
        self,
        session: Session,
        text: str,
    ) -> str | None:

        lead = session.lead

        date, time = self._extract_visit_datetime(
            text
        )

        if date:
            lead.requested_visit_date = date

        if time:
            lead.requested_visit_time = time

        if date or time:

            if lead.site_visit_status == "not_requested":
                lead.site_visit_status = "requested"

        requested_date = lead.requested_visit_date
        requested_time = lead.requested_visit_time

        if not requested_date or not requested_time:
            return None

        if lead.site_visit_status == "booked":
            return None

        try:

            requested_date_obj = datetime.strptime(
                requested_date,
                "%Y-%m-%d",
            ).date()

        except ValueError:

            lead.site_visit_status = "failed"

            return (
                "APPLICATION BOOKING RESULT: FAILED. "
                "The requested date is invalid. "
                "Ask the customer for another valid future date and time."
            )

        today = datetime.now().date()

        if requested_date_obj < today:

            lead.site_visit_status = "failed"

            return (
                "APPLICATION BOOKING RESULT: FAILED. "
                f"The requested date {requested_date} is in the past "
                "and cannot be booked. "
                "Ask the customer for a future date and time."
            )

        result = self.booking.book(
            requested_date,
            requested_time,
        )

        if result["success"]:

            lead.site_visit_status = "booked"

            return (
                "APPLICATION BOOKING RESULT: SUCCESS. "
                f"The site visit was successfully booked for "
                f"{requested_date} at {requested_time}. "
                f"Booking ID: {result['booking_id']}. "
                "Tell the customer the booking is confirmed. "
                "Provide the booking ID. "
                "Do not invent any other booking details."
            )

        lead.site_visit_status = "failed"

        return (
            "APPLICATION BOOKING RESULT: FAILED. "
            "The requested site visit slot is unavailable. "
            "Tell the customer that the slot could not be booked. "
            "Ask for another future date and time or offer human escalation."
        )

    async def chat(
        self,
        session_id: str,
        text: str,
    ) -> dict[str, Any]:

        session = self.get_session(
            session_id
        )

        if session.lead.conversation_ended:

            return {
                "session_id": session_id,
                "reply": (
                    "This conversation has ended. "
                    "Please start a new chat if you need anything else."
                ),
                "ended": True,
                "lead": session.lead.__dict__,
            }

        self._heuristic_update(
            session.lead,
            text,
        )

        session.messages.append(
            {
                "role": "user",
                "content": text,
            }
        )

        booking_context = self._maybe_booking_context(
            session,
            text,
        )

        reply = await self._ai_reply(
            session,
            application_context=booking_context,
        )

        lower = text.lower()

        if session.lead.opted_out:

            session.lead.conversation_ended = True

        elif any(
            phrase in lower
            for phrase in [
                "goodbye",
                "bye",
                "that's all",
                "that is all",
            ]
        ):

            session.lead.conversation_ended = True

        session.messages.append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        return {
            "session_id": session_id,
            "reply": reply,
            "ended": session.lead.conversation_ended,
            "lead": session.lead.__dict__,
        }

    async def analytics(
        self,
        session_id: str,
    ) -> dict[str, Any]:

        if session_id not in self.sessions:
            raise KeyError(session_id)

        session = self.sessions[session_id]
        lead = session.lead

        return {
            "session_id": session_id,
            "lead": lead.__dict__,
            "message_count": len(session.messages),
            "summary": self._summary(session),
        }

    def _summary(
        self,
        session: Session,
    ) -> str:

        lead = session.lead
        parts = []

        if lead.name:
            parts.append(
                f"name {lead.name}"
            )

        if lead.configuration:
            parts.append(
                lead.configuration
            )

        if lead.budget:
            parts.append(
                f"budget {lead.budget}"
            )

        if lead.location_preference:
            parts.append(
                f"location preference {lead.location_preference}"
            )

        if lead.purchase_timeline:
            parts.append(
                f"timeline {lead.purchase_timeline}"
            )

        if lead.site_visit_status != "not_requested":

            parts.append(
                f"site visit {lead.site_visit_status}"
            )

        if lead.interest_level != "unknown":

            parts.append(
                f"{lead.interest_level} interest"
            )

        if lead.follow_up_required:

            parts.append(
                "follow-up required"
            )

        if lead.human_escalation:

            parts.append(
                "human escalation requested"
            )

        if lead.opted_out:

            parts.append(
                "opted out"
            )

        return (
            "Lead conversation: "
            + (
                ", ".join(parts)
                if parts
                else "insufficient qualification data."
            )
        )