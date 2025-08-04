#!/usr/bin/env python3
"""
Caregiver scheduling script using the refactored architecture.
"""

from caregiver_scheduler import CaregiverScheduler
from config_manager import get_caregiver_config


def main():
    """Main function to schedule caregivers."""
    config = get_caregiver_config()
    scheduler = CaregiverScheduler(config)
    scheduler.solve_and_export()


if __name__ == "__main__":
    main() 