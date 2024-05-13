from pulp import LpMaximize, LpMinimize, LpProblem, LpVariable, lpSum, LpBinary, LpContinuous, LpInteger, LpStatus, value  # noqa
from excel_export import to_excel, openpyxl_formatting, to_excel_v2, openpyxl_formatting_v2  # noqa
from parameters import I, J, K, part_time_I


def populate_by_row(prob):
    prob.sense = LpMinimize

    # Define decision variables
    x = {(i, j, k): LpVariable(f"x{i},{j},{k}", cat=LpBinary) for i in I for j in J for k in K}

    # Define the objective function
    d_pos = {i: LpVariable(f"d_pos{i}", lowBound=0, cat=LpContinuous) for i in I}
    d_neg = {i: LpVariable(f"d_neg{i}", lowBound=0, cat=LpContinuous) for i in I}
    total_var = LpVariable("total_var", lowBound=0, cat=LpContinuous)

    prob += lpSum(d_pos[i] + d_neg[i] for i in I)
    prob += lpSum(x[i, j, k] for i in I for j in J for k in K) == total_var

    for i in I:
        prob += len(I) * (lpSum(x[i, j, k] for j in J for k in K) - d_pos[i] + d_neg[i]) == total_var

    # For later use in constraints 9 and 10
    weekend_coefs = {j: 1 + int(j % 6 == 0) for j in J}
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
        for i in range(1, 12):
            # C5
            prob += lpSum(x[i, j, k] for k in K) <= 1
            # C6
            if j < max(J):
                prob += x[i, j, 2] + x[i, j + 1, 1] <= 1
    for i in I:
        # C7
        for j in range(1, max(J) // 6):
            prob += lpSum(x[i, j * 6, k] + x[i, (j + 1) * 6, k] for k in K) == 1
        # C8
        for j in range(2, len(J)):
            prob += lpSum(x[i, j, k]-x[i, j-1, k]-x[i, j+1, k] for k in K) <= 0
        # C9
        for j in range(1, len(J) - 5 + 1):
            prob += lpSum(x[i, j + index, k] for k in K for index in range(5)) <= 4
        # C10
        prob += lpSum(x[i, j, k] * weekend_coefs[j] for j in J for k in K) <= len(not_multiple_6) + 2 * len(multiple_6) - 9  # noqa
    # C11
    for i in part_time_I:
        prob += lpSum(x[i, j, k] * weekend_coefs[j] for j in J for k in K) <= len(not_multiple_6) + 2 * len(multiple_6) - 13  # noqa
    # C12
    for i in I:
        for j in J[:-2]:
            prob += lpSum(x[i, j + 1, k] for k in K) - x[i, j, 2] - x[i, j + 2, 1] >= -1

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

    to_excel(values, variable_names)
    openpyxl_formatting()

    to_excel_v2(values, variable_names)
    openpyxl_formatting_v2()
