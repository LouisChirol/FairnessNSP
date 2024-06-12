from pulp import LpMaximize, LpMinimize, lpSum


def maximize_objective(prob, x, I, J, K, nb_shifts):  # noqa
    prob.sense = LpMaximize
    prob += lpSum(x[i, j, k] for i in I for j in J for k in K[:nb_shifts])


def minimize_objective(prob, x, I, J, K, nb_shifts):  # noqa
    prob.sense = LpMinimize
    prob += lpSum(x[i, j, k] for i in I for j in J for k in K[:nb_shifts])


def composite_objective(prob, x, I, J, K, nb_shifts):  # noqa
    """Maximize the number of agents for week shifts but minimize it for weekend shifts"""
    prob.sense = LpMaximize
    prob += (lpSum(x[i, j, k] for i in I for j in J if j % 6 != 0 for k in K[:nb_shifts])
             - lpSum(x[i, j, k] for i in I for j in J if j % 6 == 0 for k in K[:nb_shifts]))
