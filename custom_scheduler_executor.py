"""
CustomSchedulerFromSpec: a safe, exec-free subclass of ScheduleOptimizer.

Instead of executing LLM-generated Python code, this module reads a
validated StaffingSpec (Pydantic model) and translates it directly into
PuLP constraints. No arbitrary code is ever generated or executed.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from pulp import LpProblem, lpSum, value

from constraint_schema import DayTypeRequirements, StaffingSpec
from excel_export import export_schedule
from scheduler_core import ScheduleOptimizer


class CustomSchedulerFromSpec(ScheduleOptimizer):
    """
    Concrete ScheduleOptimizer whose staffing constraints come from a
    StaffingSpec rather than hand-written or LLM-generated Python code.

    All fairness constraints (C5–C17) are inherited from ScheduleOptimizer
    unchanged.
    """

    def __init__(self, config: dict[str, Any], spec: StaffingSpec) -> None:
        super().__init__(config)
        self.spec = spec

    def add_staffing_constraints(self, prob: LpProblem, x: dict) -> None:
        """Translate StaffingSpec into PuLP constraints."""
        self._apply_requirements(prob, x, self.not_multiple_6, self.spec.weekday)
        self._apply_requirements(prob, x, self.multiple_6, self.spec.weekend)
        if self.spec.max_consecutive_working_days is not None:
            self._add_max_consecutive_constraint(prob, x, self.spec.max_consecutive_working_days)
        if self.spec.max_total_staff is not None:
            self._add_max_total_staff_constraint(prob, x, self.spec.max_total_staff)

    def _apply_requirements(
        self,
        prob: LpProblem,
        x: dict,
        day_indices: list[int],
        requirements: DayTypeRequirements,
    ) -> None:
        """
        For each ShiftRequirement, add the corresponding PuLP constraint
        for every day in day_indices.

        Mirrors the NurseScheduler part-time offset pattern exactly:
        when include_part_time_offset is True, part-time agents on a
        pinned-off shift (x[i,j,k+nb_shifts]=1) count against the minimum,
        so we add them back as an offset.
        """
        for req in requirements.shifts:
            k = req.shift_index  # 1-based, matches K indexing in ScheduleOptimizer

            for j in day_indices:
                lhs = lpSum(x[i, j, k] for i in self.I)

                if self.spec.include_part_time_offset:
                    pt_offset = lpSum(
                        x[i, j, k + self.nb_shifts] for i in self.part_time_I
                    )
                else:
                    pt_offset = 0

                if req.relation == "gte":
                    prob += lhs >= req.min_staff + pt_offset
                else:  # "eq"
                    prob += lhs == req.min_staff + pt_offset

                if req.max_staff is not None:
                    prob += lhs <= req.max_staff + pt_offset

    def _add_max_consecutive_constraint(
        self, prob: LpProblem, x: dict, max_consec: int
    ) -> None:
        """
        At most max_consec consecutive working days: in any window of
        max_consec+1 days, at most max_consec can be working days.
        This is strictly tighter than C9 (which enforces ≤ 4).
        """
        J_list = list(self.J)
        window = max_consec + 1
        for i in self.I:
            for start in range(len(J_list) - max_consec):
                prob += (
                    lpSum(
                        x[i, J_list[start + offset], k]
                        for offset in range(window)
                        for k in self.K[:self.nb_shifts]
                    )
                    <= max_consec
                )

    def _add_max_total_staff_constraint(
        self, prob: LpProblem, x: dict, max_total: int
    ) -> None:
        """
        At most max_total agents working on any single day (across all shifts).
        """
        for j in self.J:
            prob += lpSum(x[i, j, k] for i in self.I for k in self.K[:self.nb_shifts]) <= max_total


# ── Helper functions ──────────────────────────────────────────────────────────


def build_custom_config(
    basic_params: dict[str, Any],
    dest_filename: str = "custom_schedule.xlsx",
) -> dict[str, Any]:
    """
    Build the config dict expected by ScheduleOptimizer.__init__ from the
    flat basic_params dict that comes from the Streamlit form.
    """
    nb_agents = basic_params["nb_agents"]
    nb_weeks = basic_params["nb_weeks"]
    nb_shifts = basic_params["nb_shifts"]
    nb_part_time = basic_params["nb_part_time_agents"]

    return {
        "I": range(1, nb_agents + 1),
        "J": range(1, nb_weeks * 6 + 1),
        "K": range(1, nb_shifts * 2 + 1),
        "nb_shifts": nb_shifts,
        "nb_weeks": nb_weeks,
        "part_time_I": range(1, nb_part_time + 1),
        "full_time_I": [i for i in range(1, nb_agents + 1) if i > nb_part_time],
        "dest_file": dest_filename,
    }


def run_custom_schedule(
    spec: StaffingSpec,
    basic_params: dict[str, Any],
    dest_filename: str = "custom_schedule.xlsx",
) -> tuple[Optional[str], int, Optional[float]]:
    """
    Build, solve, and export a schedule from a validated StaffingSpec.

    Returns:
        (output_path, pulp_status_code, objective_value)
        output_path is None when the solver does not find an optimal solution.
    """
    config = build_custom_config(basic_params, dest_filename)
    config['part_time_days_off_per_week'] = spec.part_time_days_off_per_week

    scheduler = CustomSchedulerFromSpec(config, spec)
    prob, x = scheduler.build_model()
    prob.solve()

    status_code: int = prob.status
    # PuLP status 1 == Optimal
    if status_code != 1:
        return None, status_code, None

    variable_names = [
        f"x{i},{j},{k}"
        for i in config["I"]
        for j in config["J"]
        for k in config["K"]
    ]
    values = [
        value(x[i, j, k])
        for i in config["I"]
        for j in config["J"]
        for k in config["K"]
    ]

    os.makedirs("output", exist_ok=True)
    output_path = os.path.join("output", dest_filename)
    export_schedule(
        values,
        variable_names,
        config["I"],
        config["J"],
        config["K"],
        config["part_time_I"],
        config["nb_shifts"],
        output_path,
    )

    return output_path, status_code, value(prob.objective)
