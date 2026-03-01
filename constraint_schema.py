"""
Pydantic schema for the staffing constraint specification.

This is the contract between the LLM (Step 1: natural language → JSON)
and the safe executor (Step 2: JSON → PuLP constraints).
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class ShiftRequirement(BaseModel):
    """Minimum (and optionally maximum) staffing for one shift on one day-type."""

    shift_index: int = Field(
        ...,
        ge=1,
        description="1-based shift index (1=morning, 2=evening, 3=day, …)",
    )
    min_staff: int = Field(
        ...,
        ge=0,
        description="Minimum number of agents required on this shift.",
    )
    max_staff: Optional[int] = Field(
        None,
        ge=0,
        description="Optional maximum cap. None means unconstrained.",
    )
    relation: Literal["gte", "eq"] = Field(
        "gte",
        description=(
            "'gte' = at least min_staff (>= constraint); "
            "'eq'  = exactly min_staff (== constraint, e.g. == 0 to forbid a shift)."
        ),
    )


class DayTypeRequirements(BaseModel):
    """All shift requirements for a given day type (weekday or weekend)."""

    shifts: list[ShiftRequirement] = Field(
        default_factory=list,
        description="One entry per shift that carries a non-trivial staffing requirement.",
    )


class StaffingSpec(BaseModel):
    """
    Top-level specification produced by the LLM.

    Covers weekdays (j % 6 != 0) and weekends (j % 6 == 0) independently.
    All fairness constraints (rest days, cyclical rotation, part-time rules)
    are already handled by the base ScheduleOptimizer and are NOT encoded here.
    """

    nb_shifts: int = Field(
        ...,
        ge=1,
        le=5,
        description="Number of shift types in use — must match the UI input.",
    )
    weekday: DayTypeRequirements = Field(
        ...,
        description="Staffing requirements for weekdays (Monday–Friday).",
    )
    weekend: DayTypeRequirements = Field(
        ...,
        description="Staffing requirements for the weekend day (6th day of each week).",
    )
    include_part_time_offset: bool = Field(
        True,
        description=(
            "When True, the minimum is net: part-time agents on a pinned-off shift "
            "are added as an offset (mirrors NurseScheduler behaviour). "
            "Set to False only when the minimum should apply to the raw headcount."
        ),
    )
    max_consecutive_working_days: Optional[int] = Field(
        None,
        ge=1,
        le=3,
        description=(
            "If set, no agent may work more than this many consecutive days. "
            "Only meaningful for values 1–3; the base model already enforces ≤ 4 via C9. "
            "Adds a sliding-window constraint: in any window of N+1 days, at most N are worked."
        ),
    )
    part_time_days_off_per_week: int = Field(
        1,
        ge=1,
        le=4,
        description=(
            "Number of weekday off-slots per week for part-time agents. "
            "1 = 80% workload (default), 2 = 60%, 3 = 40%, 4 = 20%. "
            "Weekend days are never used as part-time off-slots."
        ),
    )
    max_total_staff: Optional[int] = Field(
        None,
        ge=1,
        description=(
            "If set, no more than this many agents may be working (across all shifts) "
            "on any single day. Applies equally to weekdays and weekends. "
            "Useful to cap total presence, e.g. for small wards."
        ),
    )
    notes: Optional[str] = Field(
        None,
        description=(
            "Free-text field for the LLM to record constraints it could not encode "
            "in any structured field."
        ),
    )

    @model_validator(mode="after")
    def validate_shift_indices_and_bounds(self) -> "StaffingSpec":
        """Ensure shift_index values are in range and max_staff ≥ min_staff."""
        for day_label, day_req in [("weekday", self.weekday), ("weekend", self.weekend)]:
            for req in day_req.shifts:
                if req.shift_index > self.nb_shifts:
                    raise ValueError(
                        f"{day_label}: shift_index {req.shift_index} exceeds "
                        f"nb_shifts={self.nb_shifts}."
                    )
                if req.max_staff is not None and req.max_staff < req.min_staff:
                    raise ValueError(
                        f"{day_label} shift {req.shift_index}: "
                        f"max_staff ({req.max_staff}) < min_staff ({req.min_staff})."
                    )
        return self

    # ── Human-readable rendering for the UI confirmation step ─────────────────

    def to_human_readable(self, lang: str = "en") -> str:
        """Render the spec as plain text for the UI confirmation step."""
        if lang == "fr":
            return self._render("fr")
        return self._render("en")

    def _render(self, lang: str) -> str:
        if lang == "fr":
            shift_names = {1: "Matin", 2: "Soir", 3: "Jour"}
            relation_map = {"gte": "au moins", "eq": "exactement"}
            labels = {
                "nb_shifts": f"Nombre d'équipes : {self.nb_shifts}",
                "weekday": "JOURS DE SEMAINE (Lun–Ven) :",
                "weekend": "WEEKENDS (Samedi) :",
                "no_req": "  Aucune exigence explicite.",
                "shift": "Équipe",
                "agents": "agent(s)",
                "at_most": "au plus",
                "consec": lambda n: f"Jours consécutifs max : {n} jour(s)",
                "pt_rate": lambda d: f"Temps partiel : {d} jour(s) de repos/semaine ({(5-d)*20}% de charge)",
                "max_total": lambda n: f"Présence totale max par jour : {n} agent(s)",
                "pt_note": (
                    "Note : les agents à temps partiel en jour de repos réduit "
                    "sont comptabilisés dans le minimum (décalage équité appliqué)."
                ),
                "ai_notes": "Notes de l'IA (contraintes non encodées) :",
            }
        else:
            shift_names = {1: "Morning", 2: "Evening", 3: "Day"}
            relation_map = {"gte": "at least", "eq": "exactly"}
            labels = {
                "nb_shifts": f"Number of shifts: {self.nb_shifts}",
                "weekday": "WEEKDAYS (Mon–Fri):",
                "weekend": "WEEKENDS (Saturday):",
                "no_req": "  No explicit requirements.",
                "shift": "Shift",
                "agents": "agent(s)",
                "at_most": "at most",
                "consec": lambda n: f"Max consecutive working days: {n}",
                "pt_rate": lambda d: f"Part-time: {d} day(s) off/week ({(5-d)*20}% workload)",
                "max_total": lambda n: f"Max total staff per day: {n} agent(s)",
                "pt_note": (
                    "Note: Part-time agents on a pinned-off shift add to the minimum "
                    "(standard fairness offset applied)."
                ),
                "ai_notes": "Note from AI (constraints it could not fully encode):",
            }

        lines = [labels["nb_shifts"], ""]

        for period_label, day_req in [
            (labels["weekday"], self.weekday),
            (labels["weekend"], self.weekend),
        ]:
            lines.append(period_label)
            if not day_req.shifts:
                lines.append(labels["no_req"])
            for req in day_req.shifts:
                name = shift_names.get(req.shift_index, f"{labels['shift']} {req.shift_index}")
                rel = relation_map[req.relation]
                line = f"  {name}: {rel} {req.min_staff} {labels['agents']}"
                if req.max_staff is not None:
                    line += f", {labels['at_most']} {req.max_staff}"
                lines.append(line)
            lines.append("")

        if self.max_consecutive_working_days is not None:
            lines.append(labels["consec"](self.max_consecutive_working_days))
            lines.append("")

        if self.part_time_days_off_per_week != 1:
            lines.append(labels["pt_rate"](self.part_time_days_off_per_week))
            lines.append("")

        if self.max_total_staff is not None:
            lines.append(labels["max_total"](self.max_total_staff))
            lines.append("")

        if self.include_part_time_offset:
            lines.append(labels["pt_note"])
            lines.append("")

        if self.notes:
            lines.append(labels["ai_notes"])
            lines.append(self.notes)

        return "\n".join(lines).rstrip()
