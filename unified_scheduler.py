#!/usr/bin/env python3
"""
Unified scheduler that can handle both nurse and caregiver scheduling.
"""

from nurse_scheduler import NurseScheduler
from caregiver_scheduler import CaregiverScheduler
from config_manager import get_nurse_config, get_caregiver_config


class UnifiedScheduler:
    """Unified scheduler for both nurse and caregiver scheduling."""
    
    @staticmethod
    def schedule_nurses():
        """Schedule nurses using the nurse-specific constraints."""
        config = get_nurse_config()
        scheduler = NurseScheduler(config)
        return scheduler.solve_and_export()
    
    @staticmethod
    def schedule_caregivers():
        """Schedule caregivers using the caregiver-specific constraints."""
        config = get_caregiver_config()
        scheduler = CaregiverScheduler(config)
        return scheduler.solve_and_export()
    
    @staticmethod
    def schedule_all():
        """Schedule both nurses and caregivers."""
        print("=== Scheduling Nurses ===")
        UnifiedScheduler.schedule_nurses()
        print("\n=== Scheduling Caregivers ===")
        UnifiedScheduler.schedule_caregivers()


def main():
    """Main function with command line interface."""
    import sys
    
    if len(sys.argv) > 1:
        agent_type = sys.argv[1].lower()
        if agent_type in ['nurse', 'nurses', 'inf']:
            UnifiedScheduler.schedule_nurses()
        elif agent_type in ['caregiver', 'caregivers', 'as']:
            UnifiedScheduler.schedule_caregivers()
        elif agent_type in ['all', 'both']:
            UnifiedScheduler.schedule_all()
        else:
            print("Usage: python unified_scheduler.py [nurse|caregiver|all]")
            print("  nurse/nurses/inf: Schedule nurses only")
            print("  caregiver/caregivers/as: Schedule caregivers only")
            print("  all/both: Schedule both (default)")
    else:
        # Default: schedule both
        UnifiedScheduler.schedule_all()


if __name__ == "__main__":
    main() 