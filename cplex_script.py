import cplex
from cplex.exceptions import CplexError


def populate_by_row(prob):
    prob.objective.set_sense(prob.objective.sense.minimize)

    # Add your variables
    # For a 3D variable x[i][j][k], you'll flatten this in a single list or array
    # E.g., x111, x112, ..., x2433 (flattening by iterating over i, j, k)
    names = [f"x{i}{j}{k}" for i in range(1, 12) for j in range(1, 25) for k in range(1, 4)]
    prob.variables.add(names=names, types=["I"] * len(names))  # "I" denotes integer variables

    # Add your constraints
    # This will depend on the specific form of your constraints
    # You need to convert each inequality into a linear expression
    # Example:
    # prob.linear_constraints.add(
    #     lin_expr=[cplex.SparsePair(ind=[variable_indices], val=[variable_coefficients])],
    #     senses=["L"],  # "L" for <=, "G" for >=, "E" for ==
    #     rhs=[right_hand_side_value]
    # )
    # Staffing constraints:
    variable_coefficients = [1] * 11  # Coefficient for each variable in the sum is 1
    for j in range(1, 25):  # J from 1 to 24
        # First constraint (staff >= 3 in the morning shift):
        morning_variable_indices = [names.index(f"x{i}{j}1") for i in range(1, 12)]  # i from 1 to 11, k fixed at 1
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=morning_variable_indices, val=variable_coefficients)],
            senses=["G"],  # "G" denotes greater than or equal to
            rhs=[3]  # Right hand side of the inequality
        )
        # Second constraint (staff >= 2 in the evening shift):
        evening_variable_indices = [names.index(f"x{i}{j}2") for i in range(1, 12)]  # i from 1 to 11, k fixed at 2
        prob.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=evening_variable_indices, val=variable_coefficients)],
            senses=["G"],  # "G" denotes greater than or equal to
            rhs=[2]  # Right hand side of the inequality
        )
        # Third  and fourth constraint (staff >= 1 in the day shift, exactly 0 for weekends):
        day_variable_indices = [names.index(f"x{i}{j}3") for i in range(1, 12)]  # i from 1 to 11, k fixed at 3
        if j % 6 == 0:  # TO VERIFY
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=day_variable_indices, val=variable_coefficients)],
                senses=["G"],  # "G" denotes greater than or equal to
                rhs=[1]  # Right hand side of the inequality
            )
        else:
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=day_variable_indices, val=variable_coefficients)],
                senses=["E"],  # "E" denotes equality
                rhs=[0]  # Right hand side of the inequality
            )
        for i in range(1, 12):
            shift_indices = [names.index(f"x{i}{j}{k}") for k in range(1, 4)]
            # Fifth constaint (at most 1 shift per day for all agents):
            prob.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=shift_indices, val=[1, 1, 1])],
                senses=["L"],  # "L" denotes less than or equal to
                rhs=[1]  # Right hand side of the inequality
            )
            # Sixth constraint (>12h of rest between shifts):
            if j < 24:
                shift_indices = [names.index(f"x{i}{j}2"), names.index(f"x{i}{j+1}1")]
                prob.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=shift_indices, val=[1, 1])],
                    senses=["L"],  # "L" denotes less than or equal to
                    rhs=[1]  # Right hand side of the inequality
                )
    # Define your objective function
    # Example:
    # prob.objective.set_linear(list(enumerate(objective_function_coefficients)))


if __name__ == "__main__":
    try:
        my_prob = cplex.Cplex()
        populate_by_row(my_prob)
        # Print number of variables and constraints
        print("Variables: ", my_prob.variables.get_num())
        print("Constraints: ", my_prob.linear_constraints.get_num())
        # my_prob.solve()
    except CplexError as exc:
        print(exc)

    # print("Solution status = ", my_prob.solution.get_status(), ":", end=' ')
    # print(my_prob.solution.status[my_prob.solution.get_status()])
    # print("Solution value  = ", my_prob.solution.get_objective_value())
