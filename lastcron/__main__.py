"""
CLI entry point for the LastCron SDK.

This allows the SDK to be executed as a module:
    python -m lastcron

This replaces the need for orchestrator_wrapper.py in each repository.
"""

from lastcron.client import main

if __name__ == "__main__":
    main()
