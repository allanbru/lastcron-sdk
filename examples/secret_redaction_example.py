"""
Example: Automatic Secret Redaction

This demonstrates how the SDK automatically redacts secret values from logs
to prevent accidental exposure of sensitive information.

Key features:
1. Secrets are fetched on-demand using get_block()
2. Secret values are automatically added to the logger's redaction list
3. Any log message containing a secret value will have it replaced with '****'
4. Logger and workspace_id are accessed via get_run_logger() and get_workspace_id()
"""

from lastcron_sdk import flow, get_block, get_run_logger, get_workspace_id

@flow
def secure_api_caller(**params):
    """
    A flow that safely handles API credentials.

    The SDK automatically redacts secret values from all log messages,
    preventing accidental exposure in logs.
    """
    logger = get_run_logger()
    workspace_id = get_workspace_id()

    logger.info("Starting secure API caller")
    logger.info(f"Running in workspace: {workspace_id}")
    
    # Fetch API key block (on-demand)
    api_key_block = get_block('api-key')
    
    if not api_key_block:
        logger.error("API key block not found!")
        return
    
    logger.info("Successfully retrieved API key block")
    
    # The secret value is automatically added to the redaction list
    api_key = api_key_block.value
    
    # ⚠️ DANGER: This would normally expose the secret!
    # But the SDK automatically redacts it:
    logger.info(f"Using API key: {api_key}")
    # Output: "Using API key: ****"
    
    # Even if you accidentally log it in an error message:
    try:
        # Simulate an API call
        response = f"API call with key {api_key} failed"
        raise Exception(response)
    except Exception as e:
        # The secret is redacted even in exception messages!
        logger.error(f"API call failed: {e}")
        # Output: "API call failed: API call with key **** failed"
    
    # Fetch database credentials
    db_creds_block = get_block('database-credentials')
    
    if db_creds_block:
        logger.info("Retrieved database credentials")
        db_password = db_creds_block.value
        
        # This is also automatically redacted:
        logger.info(f"Connecting to database with password: {db_password}")
        # Output: "Connecting to database with password: ****"
    
    logger.info("Flow completed safely - no secrets exposed!")


@flow
def multi_secret_example(**params):
    """
    Example showing multiple secrets being redacted.
    """
    logger = get_run_logger()

    logger.info("Fetching multiple secrets")
    
    # Fetch multiple secret blocks
    aws_key = get_block('aws-access-key')
    aws_secret = get_block('aws-secret-key')
    api_token = get_block('api-token')
    
    # All secret values are automatically tracked
    secrets_found = []
    if aws_key:
        secrets_found.append('aws-access-key')
    if aws_secret:
        secrets_found.append('aws-secret-key')
    if api_token:
        secrets_found.append('api-token')
    
    logger.info(f"Found {len(secrets_found)} secrets: {', '.join(secrets_found)}")
    
    # Even if you construct a message with multiple secrets:
    if aws_key and aws_secret:
        message = f"AWS credentials: key={aws_key.value}, secret={aws_secret.value}"
        logger.info(message)
        # Output: "AWS credentials: key=****, secret=****"
    
    logger.info("All secrets are automatically redacted!")


@flow
def non_secret_example(**params):
    """
    Example showing that non-secret blocks are NOT redacted.
    """
    logger = get_run_logger()

    logger.info("Fetching configuration blocks")
    
    # Fetch a non-secret block (e.g., API endpoint URL)
    api_endpoint = get_block('api-endpoint')
    
    if api_endpoint:
        # Non-secret values are logged normally
        logger.info(f"API endpoint: {api_endpoint.value}")
        # Output: "API endpoint: https://api.example.com"
    
    # Fetch a secret block
    api_key = get_block('api-key')
    
    if api_key:
        # Secret values are redacted
        logger.info(f"API key: {api_key.value}")
        # Output: "API key: ****"
    
    logger.info("Only secrets are redacted, not regular config!")


# How it works:
# 
# 1. When you call get_block('api-key'), the SDK:
#    - Fetches the block from the API
#    - Checks if it's a secret (is_secret=True)
#    - If it's a secret, adds the value to logger.secrets list
#
# 2. When you call logger.info(message), the SDK:
#    - Iterates through all secrets in logger.secrets
#    - Replaces each secret value with '****' in the message
#    - Logs the redacted message
#
# 3. This happens automatically for:
#    - logger.info()
#    - logger.warning()
#    - logger.error()
#    - Both console output and API logs
#
# Benefits:
# ✅ Prevents accidental secret exposure
# ✅ Works automatically - no manual redaction needed
# ✅ Protects against common mistakes (logging exceptions, debug messages, etc.)
# ✅ Secrets are only loaded when needed (on-demand via get_block())

