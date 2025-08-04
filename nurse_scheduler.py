from scheduler_core import ScheduleOptimizer
from pulp import lpSum


class NurseScheduler(ScheduleOptimizer):
    """Nurse scheduling optimizer with nurse-specific constraints."""
    
    def add_staffing_constraints(self, prob, x):
        """Add nurse-specific staffing constraints."""
        staffing_constraints_week = self.config['staffing_constraints_week']
        staffing_constraints_weekend = self.config['staffing_constraints_weekend']
        
        # Staffing constraints (C1, C2, C3, C4)
        for j in self.J:
            for ik, k in enumerate(self.K[:self.nb_shifts]):
                if j % 6 != 0:  # Week days
                    prob += lpSum(x[i, j, k] for i in self.I) >= (
                        staffing_constraints_week[ik] + 
                        lpSum(x[i, j, k + self.nb_shifts] for i in self.part_time_I)
                    )
                else:  # Weekends
                    prob += lpSum(x[i, j, k] for i in self.I) >= (
                        staffing_constraints_weekend[ik] + 
                        lpSum(x[i, j, k + self.nb_shifts] for i in self.part_time_I)
                    ) 