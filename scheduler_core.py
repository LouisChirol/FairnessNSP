from abc import ABC, abstractmethod
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary, LpStatus, value
from excel_export import export_schedule
from objectives import composite_objective
import os


class ScheduleOptimizer(ABC):
    """Abstract base class for schedule optimization with fairness constraints."""
    
    def __init__(self, config):
        """Initialize with configuration parameters."""
        self.config = config
        self.I = config['I']
        self.J = config['J'] 
        self.K = config['K']
        self.nb_shifts = config['nb_shifts']
        self.nb_weeks = config['nb_weeks']
        self.part_time_I = config['part_time_I']
        self.full_time_I = config['full_time_I']
        self.dest_file = config['dest_file']
        
        # Derived values
        self.multiple_6 = [j for j in self.J if j % 6 == 0]
        self.not_multiple_6 = [j for j in self.J if j % 6 != 0]
    
    def create_variables(self):
        """Create decision variables for the optimization problem."""
        return {(i, j, k): LpVariable(f"x{i},{j},{k}", cat=LpBinary) 
                for i in self.I for j in self.J for k in self.K}
    
    def add_common_constraints(self, prob, x):
        """Add constraints that are common to all agent types."""
        
        # C5: No more than one shift per day per agent
        for j in self.J:
            for i in self.I:
                prob += lpSum(x[i, j, k] for k in self.K[:self.nb_shifts]) <= 1
                
                # C6: No morning shift after evening shift
                if j < max(self.J):
                    prob += x[i, j, 2] + x[i, j + 1, 1] <= 1
        
        # C7: Weekend alternation constraint
        for i in self.I:
            for j in range(1, self.nb_weeks):
                prob += lpSum(x[i, j * 6, k] + x[i, (j + 1) * 6, k] 
                             for k in self.K[:self.nb_shifts]) == 1
        
        # C8: No evening-rest-morning sequence
        for i in self.I:
            for j in range(2, len(self.J)):
                prob += lpSum(x[i, j, k] - x[i, j-1, k] - x[i, j + 1, k] 
                             for k in self.K[:self.nb_shifts]) <= 0
        
        # C9: At least a day off per week
        for i in self.I:
            for j in range(1, len(self.J) - 5 + 1):
                prob += lpSum(x[i, j + index, k] for k in self.K[:self.nb_shifts] 
                             for index in range(5)) <= 4
        
        # C10: Days off constraint for full-time agents
        for i in self.I:
            prob += (lpSum(x[i, j, k] * (1 + int(j % 6 == 0)) for j in self.J for k in self.K[:self.nb_shifts])
                     <= len(self.not_multiple_6) + 2 * len(self.multiple_6) - (9 * (self.nb_weeks / 4)) + 1)
        
        # C11: No working day between two days off
        for i in self.I:
            for j in self.J[:-2]:
                prob += lpSum(x[i, j + 1, k] for k in self.K[:self.nb_shifts]) - x[i, j, 2] - x[i, j + 2, 1] >= -1
        
        # C12: Strict cyclical constraints
        for idx, i in enumerate(self.I[:-1]):
            next_i = self.I[(idx + 1) % len(self.I)]
            for j_idx, j in enumerate(self.J):
                next_j = self.J[(j_idx + 6) % len(self.J)]
                for k in self.K[:self.nb_shifts]:
                    prob += (x[i, j, k] == x[next_i, next_j, k])
        
        # C13: Part-time day off cyclical constraints
        for idx, i in enumerate(self.part_time_I[:-1]):
            next_i = self.part_time_I[(idx + 1) % len(self.part_time_I)]
            for j_idx, j in enumerate(self.J):
                for k in self.K[self.nb_shifts:]:
                    next_j = self.J[(j_idx + 6) % len(self.J)]
                    prob += (x[i, j, k] == x[next_i, next_j, k])
        
        # C14: No part-time day off for full-time agents
        for i in self.full_time_I:
            prob += lpSum(x[i, j, k] for j in self.J for k in self.K[self.nb_shifts:]) == 0
        
        # C15: Part-time agent constraints
        for i in self.part_time_I:
            # One day pinned per week except for weekends
            for s in range(0, self.nb_weeks):
                week_days = self.J[s * 6: s * 6 + 5]
                weekend_day = self.J[s * 6 + 5]
                prob += lpSum(x[i, j, k] for j in week_days for k in self.K[self.nb_shifts:]) == 1
                prob += lpSum(x[i, weekend_day, k] for k in self.K[self.nb_shifts:]) == 0
            
            # Day pinned must not be a day off
            for j in self.J:
                for k in self.K[:self.nb_shifts]:
                    prob += x[i, j, k + self.nb_shifts] - lpSum(x[i, j, k]) <= 0
        
        # C17: No more than 3 consecutive days off
        for i in self.I:
            for j in self.J[:-3]:
                prob += lpSum(x[i, j + index, k] for k in self.K[:self.nb_shifts] 
                             for index in range(4)) >= 1
    
    @abstractmethod
    def add_staffing_constraints(self, prob, x):
        """Add agent-specific staffing constraints. Must be implemented by subclasses."""
        pass
    
    def build_model(self):
        """Build the complete optimization model."""
        prob = LpProblem("Schedule Optimization", LpMaximize)
        x = self.create_variables()
        
        # Set objective function
        composite_objective(prob, x, self.I, self.J, self.K, self.nb_shifts)
        
        # Add constraints
        self.add_staffing_constraints(prob, x)
        self.add_common_constraints(prob, x)
        
        return prob, x
    
    def solve_and_export(self):
        """Solve the optimization problem and export results."""
        prob, x = self.build_model()
        
        # Print problem statistics
        print("Variables:", len(prob.variables()))
        print("Constraints:", len(prob.constraints))
        print("Total:", len(prob.variables()) + len(prob.constraints))
        
        print("Solving...")
        prob.solve()
        
        # Print results
        print("Solution status =", LpStatus[prob.status])
        print("Solution value =", value(prob.objective))
        
        # Export to Excel
        variable_names = [f"x{i},{j},{k}" for i in self.I for j in self.J for k in self.K]
        values = [value(x[i, j, k]) for i in self.I for j in self.J for k in self.K]
        
        os.makedirs("output", exist_ok=True)
        dest_path = os.path.join("output", self.dest_file)
        export_schedule(values, variable_names, self.I, self.J, self.K, 
                       self.part_time_I, self.nb_shifts, dest_path)
        
        return prob, x 