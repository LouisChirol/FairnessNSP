from pulp import LpMaximize, LpMinimize, LpProblem, LpVariable, lpSum, LpBinary, LpStatus, value
from excel_export.excel_export_as_tp import to_excel_v2, openpyxl_formatting_v2
from parameters.parametres_as_tp import (I, J, K, nb_shifts, nb_semaines,
                                         part_time_I, full_time_I)
import os


def maximize_objective(prob, x):
    prob.sense = LpMaximize
    prob += lpSum(x[i, j, k] for i in I for j in J for k in K[:nb_shifts])


def minimize_objective(prob, x):
    prob.sense = LpMinimize
    prob += lpSum(x[i, j, k] for i in I for j in J for k in K[:nb_shifts])


def composite_objective(prob, x):
    """Maximize the number of agents for week shifts but minimize it for weekend shifts"""
    prob.sense = LpMaximize
    prob += (lpSum(x[i, j, k] for i in I for j in J if j % 6 != 0 for k in K[:nb_shifts])
             - lpSum(x[i, j, k] for i in I for j in J if j % 6 == 0 for k in K[:nb_shifts]))


def populate_by_row(prob):

    # Define decision variables
    x = {(i, j, k): LpVariable(f"x{i},{j},{k}", cat=LpBinary) for i in I for j in J for k in K}

    # Define the objective function
    composite_objective(prob, x)

    # For later use in constraints 9 and 10
    multiple_6 = [j for j in J if j % 6 == 0]
    not_multiple_6 = [j for j in J if j % 6 != 0]

    # Staffing constraints
    for j in J:
        # Week days
        if j % 6 != 0:
            # C1 (morning shift constraint)
            prob += lpSum(x[i, j, 1] for i in I) >= 3 + lpSum(x[i, j, 4] for i in part_time_I)
            # C2 (evening shift constraint)
            prob += lpSum(x[i, j, 2] for i in I) >= 2 + lpSum(x[i, j, 5] for i in part_time_I)
            # C3 (day shift constraint)
            prob += lpSum(x[i, j, 3] for i in I) == 0
        # Weekends
        else:
            # C1b (total week-end shift constraint)
            prob += lpSum(x[i, j, 1] + x[i, j, 2] for i in I) >= 4
            # C1 (morning week-end shift constraint)
            prob += lpSum(x[i, j, 2] for i in I) >= 1
            # # C2 (evening week-end shift constraint)
            prob += lpSum(x[i, j, 2] for i in I) >= 1
            prob += lpSum(x[i, j, 2] for i in I) <= 2
            # C4 (day shift constraint)
            prob += lpSum(x[i, j, 3] for i in I) == 0

        for i in I:
            # C5 (no more than one shift per day per agent)
            prob += lpSum(x[i, j, k] for k in K[:nb_shifts]) <= 1
            # C6 (no morning shift after evening shift)
            if j < max(J):
                prob += x[i, j, 2] + x[i, j + 1, 1] <= 1
    for i in I:
        # C7 (weekend alternation constraint)
        for j in range(1, nb_semaines):
            prob += lpSum(x[i, j * 6, k] + x[i, (j + 1) * 6, k] for k in K[:nb_shifts]) == 1
        # C8 (no evening-rest-morning sequence)
        for j in range(2, len(J)):
            prob += lpSum(x[i, j, k] - x[i, j-1, k] - x[i, j + 1, k] for k in K[:nb_shifts]) <= 0
        # C9 (at least a day off per week)
        for j in range(1, len(J) - 5 + 1):
            prob += lpSum(x[i, j + index, k] for k in K[:nb_shifts] for index in range(5)) <= 4
        # C10 (days off constraint for full-time agents)
        prob += (lpSum(x[i, j, k] * (1 + int(j % 6 == 0)) for j in J for k in K[:nb_shifts])
                 <= len(not_multiple_6) + 2 * len(multiple_6) - (9*(nb_semaines/4)) + 1)
    # C12  (no working day between two days off)
    for i in I:
        for j in J[:-2]:
            prob += lpSum(x[i, j + 1, k] for k in K[:nb_shifts]) - x[i, j, 2] - x[i, j + 2, 1] >= -1

    # C13: strict cyclical constraints: if agent i works shift k at time j, then he works shift k at time j+6
    # No need to differentiate between part-time and full-time agents
    for idx, i in enumerate(I[:-1]):
        next_i = I[(idx + 1) % len(I)]
        for j_idx, j in enumerate(J):
            next_j = J[(j_idx + 6) % len(J)]
            for k in K[:nb_shifts]:
                prob += (x[i, j, k] == x[next_i, next_j, k])
    # Part-time day off cyclical constraints
    for idx, i in enumerate(part_time_I[:-1]):
        next_i = part_time_I[(idx + 1) % len(part_time_I)]
        for j_idx, j in enumerate(J):
            for k in K[nb_shifts:]:
                next_j = J[(j_idx + 6) % len(J)]
                prob += (x[i, j, k] == x[next_i, next_j, k])

    # C14: no more than 3 consecutive days off
    for i in I:
        for j in J[:-2]:
            prob += 3 - lpSum(x[i, j + index, k] for k in K[:nb_shifts] for index in range(3)) >= 0

    # Part-time agents
    for i in full_time_I:
        prob += lpSum(x[i, j, k] for j in J for k in K[nb_shifts:]) == 0
    for i in part_time_I:
        # C15 (One day pinned per week except for weekends)
        for s in range(0, nb_semaines):
            week_days = J[s * 6: s * 6 + 5]
            weekend_day = J[s * 6 + 5]
            prob += lpSum(x[i, j, k] for j in week_days for k in K[nb_shifts:]) == 1
            prob += lpSum(x[i, weekend_day, k] for k in K[nb_shifts:]) == 0
        # C16 (Day pinned must not be a day off)
        for j in J:
            for k in K[:nb_shifts]:
                prob += x[i, j, k + nb_shifts] - lpSum(x[i, j, k]) <= 0
    return x


if __name__ == "__main__":
    prob = LpProblem("Minimize Staffing", LpMinimize)
    x = populate_by_row(prob)

    # Print number of variables and constraints
    print("Variables: ", len(prob.variables()))
    print("Constraints: ", len(prob.constraints))
    print("Total: ", len(prob.variables()) + len(prob.constraints))

    print("Solving...")
    prob.solve()

    # Print the solution status and objective value
    print("Solution status = ", LpStatus[prob.status])
    print("Solution value  = ", value(prob.objective))

    variable_names = [f"x{i},{j},{k}" for i in I for j in J for k in K]
    values = [value(x[i, j, k]) for i in I for j in J for k in K]

    os.makedirs("output", exist_ok=True)
    to_excel_v2(values, variable_names, dest_path="output/excel_as_tp_v2.xlsx")
    openpyxl_formatting_v2(src_path="output/excel_as_tp_v2.xlsx", dest_path="output/trame_as_tp_v2.xlsx")
