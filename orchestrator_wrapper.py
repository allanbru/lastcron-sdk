# orchestrator_wrapper.py

import os
import sys
from lastcron_sdk.client import execute_lastcron_flow

# The PHP FlowExecutor sets these environment variables:
# ORCH_RUN_ID, ORCH_TOKEN, ORCH_API_BASE_URL
run_id = os.environ.get('ORCH_RUN_ID')
token = os.environ.get('ORCH_TOKEN')
api_base_url = os.environ.get('ORCH_API_BASE_URL')

if not all([run_id, token, api_base_url]):
    # This scenario means the PHP launch failed to set critical environment variables
    print("Fatal: Missing LastCron orchestration environment variables.", file=sys.stderr)
    sys.exit(128)

try:
    # Delegate all orchestration logic to the SDK
    execute_lastcron_flow(run_id, token, api_base_url)

except Exception as e:
    # If the SDK failed to initialize or execute, log the error here.
    # The SDK should have already attempted an API callback, but this is a final fallback.
    print(f"FATAL LastCron Execution Error: {e}", file=sys.stderr)
    sys.exit(1)