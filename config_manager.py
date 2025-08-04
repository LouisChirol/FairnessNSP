from parameters.parametres_inf import (
    I as I_inf, J as J_inf, K as K_inf, nb_shifts as nb_shifts_inf,
    nb_weeks as nb_weeks_inf, part_time_I as part_time_I_inf,
    staffing_constraints_week as staffing_constraints_week_inf,
    staffing_constraints_weekend as staffing_constraints_weekend_inf,
    dest_file as dest_file_inf
)
from parameters.parametres_as import (
    I as I_as, J as J_as, K as K_as, nb_shifts as nb_shifts_as,
    nb_weeks as nb_weeks_as, part_time_I as part_time_I_as,
    dest_file as dest_file_as
)


def get_nurse_config():
    """Get configuration for nurse scheduling."""
    return {
        'I': I_inf,
        'J': J_inf,
        'K': K_inf,
        'nb_shifts': nb_shifts_inf,
        'nb_weeks': nb_weeks_inf,
        'part_time_I': part_time_I_inf,
        'full_time_I': [i for i in I_inf if i not in part_time_I_inf],
        'staffing_constraints_week': staffing_constraints_week_inf,
        'staffing_constraints_weekend': staffing_constraints_weekend_inf,
        'dest_file': dest_file_inf
    }


def get_caregiver_config():
    """Get configuration for caregiver scheduling."""
    return {
        'I': I_as,
        'J': J_as,
        'K': K_as,
        'nb_shifts': nb_shifts_as,
        'nb_weeks': nb_weeks_as,
        'part_time_I': part_time_I_as,
        'full_time_I': [i for i in I_as if i not in part_time_I_as],
        'dest_file': dest_file_as
    } 