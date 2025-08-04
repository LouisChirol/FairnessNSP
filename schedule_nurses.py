#!/usr/bin/env python3
"""
Nurse scheduling script using the refactored architecture.
"""

from nurse_scheduler import NurseScheduler
from config_manager import get_nurse_config


def main():
    """Main function to schedule nurses."""
    config = get_nurse_config()
    scheduler = NurseScheduler(config)
    scheduler.solve_and_export()


if __name__ == "__main__":
    main() 