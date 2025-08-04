from scheduler_core import ScheduleOptimizer
from pulp import lpSum


class CaregiverScheduler(ScheduleOptimizer):
    """Caregiver scheduling optimizer with caregiver-specific constraints."""
    
    def add_staffing_constraints(self, prob, x):
        """Add caregiver-specific staffing constraints."""
        for j in self.J:
            # Week days
            if j % 6 != 0:
                # C1 (morning shift constraint)
                prob += lpSum(x[i, j, 1] for i in self.I) >= 3 + lpSum(x[i, j, 4] for i in self.part_time_I)
                # C2 (evening shift constraint)
                prob += lpSum(x[i, j, 2] for i in self.I) >= 2 + lpSum(x[i, j, 5] for i in self.part_time_I)
                # C3 (day shift constraint)
                prob += lpSum(x[i, j, 3] for i in self.I) == 0
            # Weekends
            else:
                # C1b (total week-end shift constraint)
                prob += lpSum(x[i, j, 1] + x[i, j, 2] for i in self.I) >= 4
                # C1 (morning week-end shift constraint)
                prob += lpSum(x[i, j, 2] for i in self.I) >= 1
                # C2 (evening week-end shift constraint)
                prob += lpSum(x[i, j, 2] for i in self.I) >= 1
                prob += lpSum(x[i, j, 2] for i in self.I) <= 2
                # C4 (day shift constraint)
                prob += lpSum(x[i, j, 3] for i in self.I) == 0 