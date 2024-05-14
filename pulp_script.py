from pulp import LpMaximize, LpMinimize, LpProblem, LpVariable, lpSum, LpBinary, LpContinuous, LpInteger, LpStatus, value  # noqa
from excel_export import to_excel, openpyxl_formatting, to_excel_v2, openpyxl_formatting_v2  # noqa
from parameters import I, J, K, part_time_I, full_time_I, nb_semaines
import os


def populate_by_row(prob):

    # Define decision variables
    x = {(i, j, k): LpVariable(f"x{i},{j},{k}", cat=LpBinary) for i in I for j in J for k in K}

    # Define the objective function
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

    # # Simpler objective function: maximize sum of x[i, j, k]
    # prob.sense = LpMaximize
    # prob += lpSum(x[i, j, k] for i in I for j in J for k in K)

    # For later use in constraints 9 and 10
    multiple_6 = [j for j in J if j % 6 == 0]
    not_multiple_6 = [j for j in J if j % 6 != 0]

    # Staffing constraints
    for j in J:
        # C1
        prob += lpSum(x[i, j, 1] for i in I) >= 3
        # C2
        prob += lpSum(x[i, j, 2] for i in I) >= 2
        # C3
        if j % 6 != 0:
            prob += lpSum(x[i, j, 3] for i in I) >= 1
        # C4
        else:
            prob += lpSum(x[i, j, 3] for i in I) == 0
        for i in I:
            # C5
            prob += lpSum(x[i, j, k] for k in K) <= 1
            # C6
            if j < max(J):
                prob += x[i, j, 2] + x[i, j + 1, 1] <= 1
    for i in I:
        # C7
        for j in range(1, nb_semaines):
            prob += lpSum(x[i, j * 6, k] + x[i, (j + 1) * 6, k] for k in K) == 1
        # C8
        for j in range(2, len(J)):
            prob += lpSum(x[i, j, k]-x[i, j-1, k]-x[i, j+1, k] for k in K) <= 0
        # C9
        for j in range(1, len(J) - 5 + 1):
            prob += lpSum(x[i, j + index, k] for k in K for index in range(5)) <= 4
        # C10
        prob += (lpSum(x[i, j, k] * (1 + int(j % 6 == 0)) for j in J for k in K)
                 <= len(not_multiple_6) + 2 * len(multiple_6) - (9*(nb_semaines//4)))
    # C11
    for i in part_time_I:
        prob += (lpSum(x[i, j, k] * (1 + int(j % 6 == 0)) for j in J for k in K)
                 <= len(not_multiple_6) + 2 * len(multiple_6) - (13*(nb_semaines//4)))
    # C12
    for i in I:
        for j in J[:-2]:
            prob += lpSum(x[i, j + 1, k] for k in K) - x[i, j, 2] - x[i, j + 2, 1] >= -1

    # C13: strict cyclical constraints: if agent i works shift k at time j, then he works shift k at time j+6
    for idx, i in enumerate(part_time_I):
        next_i = part_time_I[(idx + 1) % len(part_time_I)]
        for j_idx, j in enumerate(J):
            next_j = J[(j_idx + 6) % len(J)]
            for k in K:
                prob += (x[i, j, k] == x[next_i, next_j, k])
    for idx, i in enumerate(full_time_I):
        next_i = full_time_I[(idx + 1) % len(full_time_I)]
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
    to_excel(values, variable_names)
    openpyxl_formatting()

    to_excel_v2(values, variable_names)
    openpyxl_formatting_v2()
