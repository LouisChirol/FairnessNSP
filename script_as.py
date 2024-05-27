from pulp import LpMaximize, LpMinimize, LpProblem, LpVariable, lpSum, LpBinary, LpContinuous, LpInteger, LpStatus, value  # noqa
from excel_export.excel_export_as import to_excel, openpyxl_formatting, to_excel_v2, openpyxl_formatting_v2  # noqa
from parameters.parametres_as import I, J, K, nb_semaines, part_time_I, full_time_I  # noqa
import os


def maximize_objective(prob, x):
    prob.sense = LpMaximize
    prob += lpSum(x[i, j, k] for i in I for j in J for k in K)


def minimize_objective(prob, x):
    prob.sense = LpMinimize
    prob += lpSum(x[i, j, k] for i in I for j in J for k in K)


def composite_objective(prob, x):
    """Maximize the number of agents for week shifts but minimize it for weekend shifts"""
    prob.sense = LpMaximize
    prob += (lpSum(x[i, j, k] for i in I for j in J if j % 6 != 0 for k in K)
             - lpSum(x[i, j, k] for i in I for j in J if j % 6 == 0 for k in K))


def jad_objective(prob, x):
    prob.sense = LpMinimize
    d_pos_80 = {i: LpVariable(f"d_pos_80{i}", lowBound=0, cat=LpContinuous) for i in part_time_I}
    d_neg_80 = {i: LpVariable(f"d_neg_80{i}", lowBound=0, cat=LpContinuous) for i in part_time_I}
    d_pos = {i: LpVariable(f"d_pos{i}", lowBound=0, cat=LpContinuous) for i in I if i not in part_time_I}
    d_neg = {i: LpVariable(f"d_neg{i}", lowBound=0, cat=LpContinuous) for i in I if i not in part_time_I}
    total_var = LpVariable("total_var", lowBound=0, cat=LpContinuous)
    total_var_80 = LpVariable("total_var_80", lowBound=0, cat=LpContinuous)

    prob += (lpSum(d_pos[i] + d_neg[i] for i in I if i not in part_time_I)
             + lpSum(d_pos_80[i] + d_neg_80[i]for i in part_time_I))
    prob += lpSum(x[i, j, k] for i in I for j in J for k in K if i not in part_time_I) == total_var
    prob += lpSum(x[i, j, k] for i in part_time_I for j in J for k in K) == total_var_80

    for i in I:
        if i in part_time_I:
            prob += ((len(part_time_I)) * (lpSum(x[i, j, k] for j in J for k in K) - d_pos_80[i] + d_neg_80[i])
                     == total_var_80)
        else:
            prob += ((len(I) - len(part_time_I)) * (lpSum(x[i, j, k] for j in J for k in K) - d_pos[i] + d_neg[i])
                     == total_var)

    dev_pos = {k: LpVariable(f"dev_pos{k}", lowBound=0, cat=LpContinuous) for k in K}
    dev_neg = {k: LpVariable(f"dev_neg{k}", lowBound=0, cat=LpContinuous) for k in K}
    total_var_shift = LpVariable("total_var_shift", lowBound=0, cat=LpContinuous)

    prob += lpSum(dev_pos[k] + dev_neg[k] for k in K)
    prob += lpSum(x[i, j, k] for i in I for j in J for k in K) == total_var_shift

    for k in K:
        prob += len(K)*(lpSum(x[i, j, k] for i in I for j in J) - dev_pos[k] + dev_neg[k]) == total_var_shift


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
            prob += lpSum(x[i, j, 1] for i in I) >= 3
            # C2 (evening shift constraint)
            prob += lpSum(x[i, j, 2] for i in I) >= 2
            # C3 (day shift constraint)
            prob += lpSum(x[i, j, 3] for i in I) == 0
        # Weekends
        else:
            # C1b (total week-end shift constraint)
            prob += lpSum(x[i, j, 1] + x[i, j, 2] for i in I) >= 4

            # prob += lpSum(x[i, j, 1] for i in I) - lpSum(x[i, j, 2] for i in I) >= 1
            # C1 (morning week-end shift constraint)
            prob += lpSum(x[i, j, 2] for i in I) >= 1
            # # C2 (evening week-end shift constraint)
            prob += lpSum(x[i, j, 2] for i in I) >= 1
            prob += lpSum(x[i, j, 2] for i in I) <= 2
            # C4 (day shift constraint)
            prob += lpSum(x[i, j, 3] for i in I) == 0
            # for i in I:
            #     prob += x[i, j, 1] - x[i, j, 2] >= 0

        for i in I:
            # C5 (no more than one shift per day per agent)
            prob += lpSum(x[i, j, k] for k in K) <= 1
            # C6 (no morning shift after evening shift)
            if j < max(J):
                prob += x[i, j, 2] + x[i, j + 1, 1] <= 1
    for i in I:
        # C7 (weekend alternation constraint)
        for j in range(1, nb_semaines):
            prob += lpSum(x[i, j * 6, k] + x[i, (j + 1) * 6, k] for k in K) == 1
        # C8 (no evening-rest-morning sequence)
        for j in range(2, len(J)):
            prob += lpSum(x[i, j, k]-x[i, j-1, k]-x[i, j+1, k] for k in K) <= 0
        # C9 (at least a day off per week)
        for j in range(1, len(J) - 5 + 1):
            prob += lpSum(x[i, j + index, k] for k in K for index in range(5)) <= 4
        # C10 (days off constraint for full-time agents)
        # prob += (lpSum(x[i, j, k] * (1 + int(j % 6 == 0)) for j in J for k in K)
        #          <= len(not_multiple_6) + 2 * len(multiple_6) - (9*(nb_semaines//4)))
        prob += (lpSum(x[i, j, k] * (1 + int(j % 6 == 0)) for j in J for k in K)
                 <= len(not_multiple_6) + 2 * len(multiple_6) - (9*(nb_semaines/4)) + 1)
    # # C11 (days off constraint for part-time agents)
    # for i in part_time_I:
    #     prob += (lpSum(x[i, j, k] * (1 + int(j % 6 == 0)) for j in J for k in K)
    #              <= len(not_multiple_6) + 2 * len(multiple_6) - (13*(nb_semaines//4)))
    # C12  (no working day between two days off)
    for i in I:
        for j in J[:-2]:
            prob += lpSum(x[i, j + 1, k] for k in K) - x[i, j, 2] - x[i, j + 2, 1] >= -1

    # C13: strict cyclical constraints: if agent i works shift k at time j, then he works shift k at time j+6
    # for idx, i in enumerate(part_time_I):
    #     next_i = part_time_I[(idx + 1) % len(part_time_I)]
    #     for j_idx, j in enumerate(J):
    #         next_j = J[(j_idx + 6) % len(J)]
    #         for k in K:
    #             prob += (x[i, j, k] == x[next_i, next_j, k])
    # for idx, i in enumerate(full_time_I):
    #     next_i = full_time_I[(idx + 1) % len(full_time_I)]
    #     for j_idx, j in enumerate(J):
    #         next_j = J[(j_idx + 6) % len(J)]
    #         for k in K:
    #             prob += (x[i, j, k] == x[next_i, next_j, k])
    # No need to differentiate between part-time and full-time agents
    for idx, i in enumerate(I[:-1]):
        next_i = I[(idx + 1) % len(I)]
        for j_idx, j in enumerate(J):
            next_j = J[(j_idx + 6) % len(J)]
            for k in K:
                prob += (x[i, j, k] == x[next_i, next_j, k])
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

    os.makedirs("export", exist_ok=True)
    to_excel(values, variable_names, dest_path="export/excel_as_v1.xlsx")
    openpyxl_formatting(src_path="export/excel_as_v1.xlsx", dest_path="export/trame_as_v1.xlsx")

    to_excel_v2(values, variable_names, dest_path="export/excel_as_v2.xlsx")
    openpyxl_formatting_v2(src_path="export/excel_as_v2.xlsx", dest_path="export/trame_as_v2.xlsx")
