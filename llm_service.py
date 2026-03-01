"""
LLM service: converts natural-language scheduling constraints into a
validated StaffingSpec JSON object using the Mistral AI API (v1.x).
"""
from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from mistralai import Mistral

from constraint_schema import StaffingSpec

load_dotenv()

_SYSTEM_PROMPT = """\
You are an expert in hospital staff scheduling. Your task is to read a
natural-language description of staffing requirements (written in English or
French) and return a single JSON object that precisely captures those
requirements.

## Context
The scheduling model uses:
- Shifts indexed 1..nb_shifts  (1 = morning/matin, 2 = evening/soir, 3 = day/jour)
- Days indexed 1..nb_weeks*6. A day j is a WEEKEND day if j % 6 == 0, otherwise WEEKDAY.
- Fairness constraints (rest days, cyclical rotation, part-time rules) are ALREADY
  handled by the base model. You only need to encode STAFFING MINIMUMS.

## JSON schema you must produce
{
  "nb_shifts": <integer, must equal the nb_shifts value given to you>,
  "weekday": {
    "shifts": [
      {
        "shift_index": <1-based integer>,
        "min_staff": <integer >= 0>,
        "max_staff": <integer >= 0 or null>,
        "relation": <"gte" or "eq">
      }
    ]
  },
  "weekend": {
    "shifts": [ ...same structure... ]
  },
  "include_part_time_offset": <true or false>,
  "max_consecutive_working_days": <integer 1-3 or null>,
  "part_time_days_off_per_week": <integer 1-4, default 1>,
  "max_total_staff": <integer >= 1 or null>,
  "notes": <string or null>
}

## Rules
1. Only list shifts that have an explicit requirement. An unlisted shift has no constraint.
2. Use "relation": "eq" only when the user says "exactly N" or "no one / nobody / 0".
   Use "relation": "gte" for "at least N" or a plain number.
3. If the user mentions a maximum ("at most N", "no more than N"), set max_staff.
4. Set include_part_time_offset to true unless the user explicitly says the minimum
   should count part-time rest slots as full workers (very unusual).
5. The base model already enforces these rules — do NOT re-encode them:
   - At most 4 consecutive working days (C9)
   - At most 3 consecutive rest days (C17)
   - No morning shift the day after an evening shift (C6)
   - Weekend alternation: each agent works exactly one of two consecutive weekends (C7)
   - At least 1 rest day per 5-day window (C9)
   - Part-time agents have a configurable number of off-days per week (see below).
6. max_consecutive_working_days: set this to an integer 1–3 if the user requests a
   stricter consecutive-day limit than the base model's 4. If the user asks for ≤ 4
   consecutive days (already enforced), leave this null. If they ask for 0 or > 4,
   leave it null and explain in notes.
7. part_time_days_off_per_week: number of weekday off-slots per week for part-time agents.
   1 = 80% workload (default), 2 = 60%, 3 = 40%, 4 = 20%.
   Convert from percentages: 80% → 1, 60% → 2, 40% → 3, 20% → 4.
   If the user does not mention part-time workload, leave this at 1 (default).
8. max_total_staff: if the user specifies a maximum total number of agents working on
   any day (e.g. "no more than 8 people in the building at once"), set this field.
   Leave null if no such cap is requested.
9. nb_shifts in your response MUST equal the nb_shifts value provided.
10. Write the "notes" field in the same language as specified by the "response_language"
    parameter in the user message (e.g. "fr" → French, "en" → English).
11. Respond with ONLY the JSON object. No markdown, no explanation, no code fences.
"""


def _build_user_message(
    user_text: str,
    nb_shifts: int,
    nb_agents: int,
    nb_weeks: int,
    nb_part_time: int,
    lang: str = "en",
) -> str:
    return (
        f"Parameters:\n"
        f"  nb_shifts            = {nb_shifts}\n"
        f"  nb_agents            = {nb_agents}\n"
        f"  nb_weeks             = {nb_weeks}\n"
        f"  nb_part_time_agents  = {nb_part_time}\n"
        f"  response_language    = {lang}\n\n"
        f"User constraints (English or French):\n"
        f"{user_text.strip()}"
    )


class LLMConstraintParser:
    """
    Calls Mistral in JSON mode to turn natural-language scheduling constraints
    into a validated StaffingSpec.

    Replaces the old LLMSchedulerGenerator entirely — no Python code is
    generated or executed.
    """

    MAX_RETRIES = 2

    def __init__(self, model: str = "mistral-large-latest") -> None:
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "MISTRAL_API_KEY not found. "
                "Create a .env file with MISTRAL_API_KEY=<your key>. "
                "See .env.example for the format."
            )
        self.client = Mistral(api_key=api_key)
        self.model = model

    def parse(
        self,
        user_text: str,
        basic_params: dict[str, Any],
        lang: str = "en",
    ) -> StaffingSpec:
        """
        Parse user_text into a validated StaffingSpec.

        Uses a retry loop: if the LLM response fails Pydantic validation,
        the error is fed back as a follow-up user message so the model can
        self-correct. Raises ValueError after MAX_RETRIES failed attempts.
        """
        nb_shifts = basic_params["nb_shifts"]
        nb_agents = basic_params["nb_agents"]
        nb_weeks = basic_params["nb_weeks"]
        nb_part_time = basic_params["nb_part_time_agents"]

        messages: list[dict[str, str]] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_message(
                    user_text, nb_shifts, nb_agents, nb_weeks, nb_part_time, lang
                ),
            },
        ]

        raw_json: str = ""
        last_error: Exception | None = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            if attempt > 1:
                # Append the previous (bad) response and the validation error
                # so the model can see exactly what needs fixing.
                messages.append({"role": "assistant", "content": raw_json})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your previous response caused this validation error:\n"
                            f"{last_error}\n\n"
                            f"Please return only the corrected JSON object."
                        ),
                    }
                )

            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=1024,
            )

            raw_json = response.choices[0].message.content.strip()

            try:
                data = json.loads(raw_json)
                return StaffingSpec.model_validate(data)
            except Exception as exc:
                last_error = exc

        raise ValueError(
            f"LLM failed to produce a valid StaffingSpec after "
            f"{self.MAX_RETRIES} attempt(s).\n"
            f"Last error : {last_error}\n"
            f"Last response: {raw_json}"
        )
