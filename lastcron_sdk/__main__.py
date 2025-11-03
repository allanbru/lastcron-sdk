"""
CLI entry point for the LastCron SDK.

This allows the SDK to be executed as a module:
    python -m lastcron_sdk

This replaces the need for orchestrator_wrapper.py in each repository.
"""

from lastcron_sdk.client import main

if __name__ == '__main__':
    main()

