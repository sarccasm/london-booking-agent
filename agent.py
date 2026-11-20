
import json
import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import AsyncOpenAI


LONDON = ZoneInfo("Europe/London")


@dataclass
class Decision:
    message: str
    understood: str
    decision: str
    status: str


SYSTEM = """
You are an autonomous restaurant booking assistant.
Write in polite, natural British English.

Your objective is to reserve a table for exactly two people
at 17:00 Europe/London on the date specified in Known facts.

Rules:
- Never invent restaurant names, availability or confirmations.
- Availability is NOT a confirmed reservation.
- Never claim a booking is confirmed without explicit approval.
- Ask for the restaurant name if it is unknown.
- Never accept another time instead of 17:00.
- If 17:00 is unavailable, politely decline.
- Only ask for booking name or phone if the manager requests them.
- Use the known booking name and phone if requested.
- Never invent missing information.
- If something is unclear, ask for clarification.
- Keep messages brief and professional.
- Do not send a final confirmation yourself.
  Python independently verifies and constructs it.
  - If the restaurant name is unknown, ask the manager for it
  and return status "continue", NOT "needs_user".
- Use "needs_user" only when information must be supplied
  by the operator, not by the restaurant manager.
- If the manager confirms availability but not the reservation,
  continue the conversation until explicit booking confirmation.

Return ONLY valid JSON:
{
  "message": "string",
  "understood": "string",
  "decision": "string",
  "status": "continue|confirmed|needs_user|declined"
}
"""


def safe_text(value):
    """Convert AI JSON values to strings safely."""
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        return " ".join(safe_text(item) for item in value).strip()

    if value is None:
        return ""

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)

    return str(value).strip()


class BookingAgent:
    def __init__(
        self,
        api_key: str,
        model: str,
        date: str,
        name: str = "",
        phone: str = "",
        base_url: str | None = None,
    ):
        if not api_key:
            raise ValueError("AI API key cannot be empty")

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
            timeout=60.0,
            max_retries=1,
        )

        self.model = model
        self.date = date
        self.name = name
        self.phone = phone

        self.history = []
        self.restaurant = ""
        self.manager_confirmed = False
        self.user_notes = []

    def opening(self) -> Decision:
        text = (
            "Good afternoon! I hope you're well. "
            f"Would it be possible to reserve a table for two people "
            f"on {self.date} at 5:00 pm, please? Many thanks!"
        )

        self.history.append({
            "role": "assistant",
            "content": text,
        })

        return Decision(
            message=text,
            understood="No manager response yet",
            decision="Request a table for two at 17:00",
            status="continue",
        )

    def extract_restaurant(self, text: str) -> str:
        """Extract restaurant name from explicit manager statements."""
        patterns = [
            r"(?:our\s+)?restaurant\s+is\s+called\s+(.+?)(?:[.!?]|$)",
            r"(?:our\s+)?restaurant\s+name\s+is\s+(.+?)(?:[.!?]|$)",
            r"(?:our\s+)?restaurant\s+is\s+(.+?)(?:[.!?]|$)",
            r"we(?:'re|\s+are)\s+called\s+(.+?)(?:[.!?]|$)",
            r"we(?:'re|\s+are)\s+at\s+(.+?)(?:[.!?]|$)",
            r"reservation\s+for\s+(?:two|2)\s+people.*?\bat\s+"
            r"(.+?)\s+(?:is|has\s+been)\s+confirmed\b",
            r"reservation\s+at\s+(.+?)\s+"
            r"(?:is|has\s+been)\s+confirmed\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.I)

            if match:
                name = match.group(1).strip(" .,!?")

                if name and len(name) <= 70:
                    return name

        return ""

    def is_explicit_confirmation(self, text: str) -> bool:
        """Verify explicit approval for the requested time and party size."""
        text = text.lower()

        negative_patterns = [
            r"\bnot\s+(?:confirmed|booked|reserved)\b",
            r"\b(?:cannot|can't|couldn't|unable\s+to)\s+"
            r"(?:confirm|book|reserve)\b",
            r"\b(?:no|without)\s+confirmation\b",
            r"\b(?:fully\s+booked|unavailable|no\s+availability)\b",
            r"\b(?:cancelled|canceled)\b",
            r"\b(?:pending|provisional|tentative)\b",
        ]

        if any(re.search(pattern, text) for pattern in negative_patterns):
            return False

        approval_patterns = [
            r"\b(?:reservation|booking|table)\s+"
            r"(?:is|has\s+been)\s+(?:confirmed|booked|reserved)\b",
            r"\b(?:confirmed|booked|reserved)\s+"
            r"(?:your\s+)?(?:reservation|booking|table)\b",
            r"\byour\s+reservation\b.*?\bis\s+confirmed\b",
        ]

        approval = any(
            re.search(pattern, text)
            for pattern in approval_patterns
        )

        time_ok = bool(
            re.search(
                r"(?<!\d)(?:17[:.]00|5(?::00)?\s*p\.?\s*m\.?)(?!\w)",
                text,
                re.I,
            )
        )

        party_ok = bool(
            re.search(
                r"\b(?:two|2)\s+(?:people|guests|persons)\b",
                text,
            )
            or re.search(
                r"\btable\s+for\s+(?:two|2)\b",
                text,
            )
        )

        times = re.findall(
            r"(?<!\d)(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)\b"
            r"|(?<!\d)(\d{1,2}):(\d{2})(?!\d)",
            text,
            re.I,
        )

        for hour12, minute12, ampm, hour24, minute24 in times:
            if hour24:
                hour = int(hour24)
                minute = int(minute24)
            else:
                hour = int(hour12) % 12
                minute = int(minute12 or 0)

                if ampm.lower().startswith("p"):
                    hour += 12

            if (hour, minute) != (17, 0):
                return False

        return approval and time_ok and party_ok

    def final_confirmation(self) -> str:
        return (
            f"Thank you for confirming our reservation at "
            f"{self.restaurant} for two people on {self.date} "
            f"at 17:00 London time. "
            "We look forward to visiting!"
        )

    def booking_time_passed(self) -> bool:
        now = datetime.now(LONDON)
        today = now.date().isoformat()

        if today != self.date:
            return True

        return (now.hour, now.minute) >= (17, 0)

    async def respond(self, manager_text: str) -> Decision:
        self.history.append({
            "role": "user",
            "content": manager_text,
        })

        restaurant_name = self.extract_restaurant(manager_text)

        if restaurant_name:
            self.restaurant = restaurant_name

        explicit_confirmation = self.is_explicit_confirmation(
            manager_text
        )

        if explicit_confirmation:
            self.manager_confirmed = True

        if self.manager_confirmed and self.restaurant:
            return Decision(
                message=self.final_confirmation(),
                understood=(
                    "Manager explicitly confirmed the reservation "
                    "for two people at 17:00"
                ),
                decision="Booking details verified",
                status="confirmed",
            )

        facts = {
            "date_london": self.date,
            "time_london": "17:00",
            "guests": 2,
            "booking_name": self.name or None,
            "booking_phone": self.phone or None,
            "restaurant_name_verified": self.restaurant or None,
            "manager_explicitly_confirmed": self.manager_confirmed,
            "operator_supplied_information": self.user_notes,
        }

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        SYSTEM
                        + "\nKnown facts: "
                        + json.dumps(facts)
                    ),
                },
                *self.history,
            ],
        )

        raw_content = response.choices[0].message.content

        if isinstance(raw_content, str):
            content = raw_content.strip()
        elif isinstance(raw_content, list):
            parts = []

            for item in raw_content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(safe_text(item.get("text", "")))
                elif hasattr(item, "text"):
                    parts.append(safe_text(item.text))

            content = "\n".join(parts).strip()
        else:
            raise ValueError(
                "AI provider returned unsupported content format"
            )

        if content.startswith("```"):
            content = re.sub(
                r"^```(?:json)?\s*|\s*```$",
                "",
                content,
                flags=re.I,
            ).strip()

        try:
            obj = json.loads(content)
        except json.JSONDecodeError:
            found = re.search(r"\{.*\}", content, re.S)

            if not found:
                raise ValueError(
                    "AI provider did not return valid JSON"
                )

            obj = json.loads(found.group(0))

        if not isinstance(obj, dict):
            raise ValueError(
                "AI output must be a JSON object"
            )

        decision = Decision(
            message=safe_text(obj.get("message", "")),
            understood=safe_text(obj.get("understood", "")),
            decision=safe_text(obj.get("decision", "")),
            status=safe_text(obj.get("status", "continue")),
        )

        if decision.status not in {
            "continue",
            "confirmed",
            "needs_user",
            "declined",
        }:
            raise ValueError("Invalid agent status")

        if decision.status == "confirmed":
            decision = Decision(
                message="",
                understood=decision.understood,
                decision=(
                    "AI suggested confirmation without "
                    "verified manager approval"
                ),
                status="needs_user",
            )

        if decision.status == "continue" and not decision.message:
            raise ValueError("Empty agent message")

        if decision.status == "continue":
            self.history.append({
                "role": "assistant",
                "content": decision.message,
            })

        return decision

    def verify_confirmation(
        self,
        restaurant: str,
        explicit_approval: bool,
    ):
        self.restaurant = restaurant.strip()
        self.manager_confirmed = explicit_approval
