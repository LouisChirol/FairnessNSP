nb_weeks = 10
nb_shifts = 3
nb_agents = 11
nb_part_time_agents = 3
I = range(1, nb_agents + 1)  # Adjust according to your actual range  # noqa
J = range(1, nb_weeks * 6 + 1)  # Adjust according to your actual range
K = range(1, nb_shifts * 2 + 1)   # Adjust according to your actual range
part_time_I = range(1, nb_part_time_agents + 1)  # Indices of part-time agents in I
full_time_I = [i for i in I if i not in part_time_I]  # Indices of full-time agents in I
staffing_constraints_week = [3, 2, 1]
staffing_constraints_weekend = [3, 2, 0]
