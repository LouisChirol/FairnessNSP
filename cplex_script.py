import cplex
from cplex.exceptions import CplexError
from excel_export import to_excel, openpyxl_formatting, to_excel_v2, openpyxl_formatting_v2  # noqa
from parameters import I, J, K, part_time_I


def populate_by_row(prob):
    prob.objective.set_sense(prob.objective.sense.minimize)

    # Add your variables
    # For a 3D variable x[i][j][k], you'll flatten this in a single list or array
    # E.g., x1,1,1, x1,1,2, ..., x2,12,3 (flattening by iterating over i, j, k)
    x_names = [f"x{i},{j},{k}" for i in I for j in J for k in K]
    prob.variables.add(names=x_names, types=["B"] * len(x_names))  # "I" denotes integer variables, "B" binary variables

    # For later use in constraints 9 and 10
    weekend_coefs = [1 + int(j % 6 == 0) for j in J for k in K]
    multiple_6 = [j for j in J if j % 6 == 0]
    not_multiple_6 = [j for j in J if j % 6 != 0]

    # Staffing constraints:
    variable_coefficients = [1] * len(I)  # Coefficient for each variable in the sum is 1
    for j in J:
        # First constraint (staff >= 3 in the morning shift):
        morning_variable_indices = [x_names.index(f"x{i},{j},1") for i in I]  # k=1 denotes morning shift
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=morning_variable_indices, val=variable_coefficients)],
            senses=["G"],  # "G" for >= ; "L" for <= ; "E" for ==
            rhs=[3]  # Right hand side of the inequality
        )
        # Second constraint (staff >= 2 in the evening shift):
        evening_variable_indices = [x_names.index(f"x{i},{j},2") for i in I]  # k=2 denotes evening shift
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=evening_variable_indices, val=variable_coefficients)],
            senses=["G"],
            rhs=[2]
        )
        # Third and fourth constraints (staff >= 1 in the day shift, exactly 0 for weekends):
        day_variable_indices = [x_names.index(f"x{i},{j},3") for i in I]  # k=3 denotes day shift
        if j % 6 != 0:  # TO VERIFY
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=day_variable_indices, val=variable_coefficients)],
                senses=["G"],
                rhs=[1]
            )
        else:
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=day_variable_indices, val=variable_coefficients)],
                senses=["E"],
                rhs=[0]
            )
        for i in range(1, 12):
            shift_indices = [x_names.index(f"x{i},{j},{k}") for k in K]
            # Fifth constaint (at most 1 shift per day for all agents):
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=shift_indices, val=[1]*len(K))],
                senses=["L"],
                rhs=[1]
            )
            # Sixth constraint (>12h of rest between shifts):
            if j < max(J):
                shift_indices = [x_names.index(f"x{i},{j},2"), x_names.index(f"x{i},{j+1},1")]
                prob.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=shift_indices, val=[1, 1])],
                    senses=["L"],
                    rhs=[1]
                )
    for i in I:
        for j in range(1, max(J)//6):
            # Seventh constraint (week-end alternance):
            weekend_indices = ([x_names.index(f"x{i},{j*6},{k}") for k in K]  # saturday
                               + [x_names.index(f"x{i},{(j+1)*6},{k}") for k in K])  # sunday
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=weekend_indices, val=[1]*len(weekend_indices))],
                senses=["E"],
                rhs=[1]
            )
        for j in range(0, max(J)//6):
            # Eighth constraint (2 days off per week):
            # off_indices = [x_names.index(f"x{i},{jj},{k}") for jj in range(6*j+1, 6*(j+1)+1) for k in K]  # 6 days per week  # noqa
            off_indices = ([x_names.index(f"x{i},{jj},{k}") for jj in range(6*j+1, 6*j+6) for k in K]
                           + [x_names.index(f"x{i},{6*j+6},{k}") for k in K])
            off_val = [1 for jj in range(6*j+1, 6*j+6) for k in K] + [2 for k in K]
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=off_indices, val=off_val)],
                senses=["L"],
                rhs=[5]
            )
        # Ninth constraint (9 rest days per month):
        month_off_indices = [x_names.index(f"x{i},{j},{k}") for j in J for k in K]
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=month_off_indices, val=weekend_coefs)],
            senses=["L"],
            rhs=[len(not_multiple_6) + 2*len(multiple_6) - 9]
        )
    # Tenth constraint (off days for part-time agents):
    for i in part_time_I:
        part_time_indices = [x_names.index(f"x{i},{j},{k}") for j in J for k in K]
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=part_time_indices, val=weekend_coefs)],
            senses=["L"],
            rhs=[len(not_multiple_6) + 2*len(multiple_6) - 13]
        )
    # Eleventh constraint (at least 36h rest for off days):
    for i in I:
        for j in J[:-2]:
            off_indices = ([x_names.index(f"x{i},{j+1},{k}") for k in K]
                           + [x_names.index(f"x{i},{j},2"), x_names.index(f"x{i},{j+2},1")])
            off_variable_coefficients = [1] * len(K) + [-1, -1]
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=off_indices, val=off_variable_coefficients)],
                senses=["G"],
                rhs=[-1]
            )

    # Define your objective function: minimize the total number of deviations to smooth the schedule
    # Auxiliary variables for deviations
    d_pos = [f"d_pos{i}" for i in I]  # Positive deviations for each agent
    d_neg = [f"d_neg{i}" for i in I]  # Negative deviations for each agent
    prob.variables.add(names=d_pos + d_neg,
                       lb=[0]*len(d_pos + d_neg),  # Lower bound of zero
                       types=["C"]*len(d_pos + d_neg))  # Continuous variables
    # Variable to capture the total sum of all x_ijk
    prob.variables.add(names=["total_var"],
                       lb=[0],  # Lower bound of zero, no upper bound needed
                       types=["I"])  # Integer variable

    # Objective function: Minimize sum of d_pos + d_neg
    prob.objective.set_sense(prob.objective.sense.minimize)
    obj_coeffs = [1] * (len(d_pos) + len(d_neg))
    prob.objective.set_linear(list(zip(d_pos + d_neg, obj_coeffs)))

    # Constraint to set total_var equal to the sum of all x_ijk
    total_sum_expr = cplex.SparsePair(ind=x_names + ["total_var"], val=[1]*len(x_names) + [-1])
    prob.linear_constraints.add(
        lin_expr=[total_sum_expr],
        senses=["E"],  # Equals sense
        rhs=[0]  # This ensures that total_var is the sum of all x_ijk
    )

    # Constraints to link deviations with x sums
    for i in I:
        sum_i_indices = [x_names.index(f"x{i},{j},{k}") for j in J for k in K]
        indices = sum_i_indices + [d_pos[i-1], d_neg[i-1], "total_var"]
        values = [1] * len(sum_i_indices) + [-1, 1, -1.0/len(I)]
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=indices, val=values)],
            senses=["E"],
            rhs=[0]
        )


if __name__ == "__main__":
    try:
        my_prob = cplex.Cplex()
        populate_by_row(my_prob)

        # Print number of variables and constraints
        print("Variables: ", my_prob.variables.get_num())
        print("Constraints: ", my_prob.linear_constraints.get_num())
        print("Total: ", my_prob.variables.get_num() + my_prob.linear_constraints.get_num())

        print("Solving...")
        my_prob.solve()

    except CplexError as exc:
        print(exc)

    print("Solution status = ", my_prob.solution.get_status(), ":", end=' ')
    print(my_prob.solution.status[my_prob.solution.get_status()])
    print("Solution value  = ", my_prob.solution.get_objective_value())

    variable_names = [f"x{i},{j},{k}" for i in I for j in J for k in K]
    values = my_prob.solution.get_values(variable_names)

    to_excel(values, variable_names)
    openpyxl_formatting()

    to_excel_v2(values, variable_names)
    openpyxl_formatting_v2()
