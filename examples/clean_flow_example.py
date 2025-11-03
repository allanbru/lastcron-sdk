"""
Example: Clean Flow Signatures

This demonstrates the new clean flow signature pattern where:
1. Flows only receive their custom parameters (no logger, workspace_id, blocks)
2. Logger is accessed via get_logger()
3. Workspace ID is accessed via get_workspace_id()
4. Blocks are fetched on-demand via get_block()
5. Secrets are automatically redacted from logs
"""

from lastcron_sdk import flow, get_logger, get_workspace_id, get_block


@flow
def process_data(batch_size=100, source='api', **kwargs):
    """
    A clean flow that only receives its custom parameters.
    
    Notice how the function signature is clean and focused:
    - No logger parameter
    - No workspace_id parameter
    - No blocks parameter
    - Just your business logic parameters!
    """
    # Get logger and workspace_id from context
    logger = get_logger()
    workspace_id = get_workspace_id()
    
    logger.info(f"Processing data in workspace {workspace_id}")
    logger.info(f"Batch size: {batch_size}, Source: {source}")
    
    # Fetch configuration blocks on-demand
    api_config = get_block('api-config')
    
    if api_config:
        logger.info(f"Using API config: {api_config.key_name}")
        # Process data...
    
    logger.info("Data processing complete!")


@flow
def send_notification(recipient, message, priority='normal'):
    """
    Another clean flow - only receives what it needs.
    """
    logger = get_logger()
    
    logger.info(f"Sending {priority} priority notification to {recipient}")
    
    # Fetch email credentials (secret block)
    email_creds = get_block('email-credentials')
    
    if email_creds:
        # The secret value is automatically redacted from logs!
        logger.info(f"Using credentials: {email_creds.value}")
        # Output: "Using credentials: ****"
        
        # Send email...
        logger.info(f"Notification sent: {message}")
    else:
        logger.error("Email credentials not found!")


@flow
def orchestrator(environment='production'):
    """
    Orchestrator flow that triggers other flows.
    """
    logger = get_logger()
    workspace_id = get_workspace_id()
    
    logger.info(f"Orchestrating workflows in {environment} environment")
    logger.info(f"Workspace: {workspace_id}")
    
    # Trigger data processing
    process_run = process_data.submit(
        parameters={
            'batch_size': 500,
            'source': 'database'
        }
    )
    
    if process_run:
        logger.info(f"Started data processing: run {process_run.id}")
    
    # Trigger notification
    notification_run = send_notification.submit(
        parameters={
            'recipient': 'admin@example.com',
            'message': 'Data processing started',
            'priority': 'high'
        }
    )
    
    if notification_run:
        logger.info(f"Started notification: run {notification_run.id}")
    
    logger.info("Orchestration complete!")


# ============================================================================
# Comparison: Old vs New
# ============================================================================

# OLD WAY (Still works, but not recommended)
@flow
def old_style_flow(**params):
    """
    Old style: Had to extract everything from params.
    """
    logger = get_logger()
    
    # Had to extract parameters manually
    parameters = params.get('parameters', {})
    batch_size = parameters.get('batch_size', 100)
    source = parameters.get('source', 'api')
    
    # Had to iterate through blocks manually
    blocks = params.get('blocks', [])
    api_config = None
    for block in blocks:
        if block['key_name'] == 'api-config':
            api_config = block
            break
    
    logger.info(f"Processing with batch_size={batch_size}")


# NEW WAY (Recommended)
@flow
def new_style_flow(batch_size=100, source='api'):
    """
    New style: Clean function signature with your parameters.
    """
    logger = get_logger()
    
    # Parameters are directly available as function arguments!
    logger.info(f"Processing with batch_size={batch_size}")
    
    # Blocks are fetched on-demand
    api_config = get_block('api-config')
    
    if api_config:
        logger.info(f"Using config: {api_config.key_name}")


# ============================================================================
# Benefits of the New Pattern
# ============================================================================

"""
✅ CLEANER CODE
   - Function signatures are focused on business logic
   - No boilerplate parameters (logger, workspace_id, blocks)
   - Parameters are directly accessible as function arguments

✅ BETTER TYPE HINTS
   @flow
   def my_flow(user_id: int, email: str, active: bool = True):
       # IDE knows the types of your parameters!
       logger = get_logger()
       logger.info(f"Processing user {user_id}")

✅ EASIER TESTING
   # You can test flows by calling them directly
   my_flow(user_id=123, email='test@example.com')
   
✅ MORE PYTHONIC
   # Follows standard Python function conventions
   # No special "magic" parameters

✅ AUTOMATIC SECURITY
   # Secrets are automatically redacted from logs
   # No manual redaction needed

✅ ON-DEMAND LOADING
   # Blocks are only fetched when needed
   # Better performance

✅ BACKWARD COMPATIBLE
   # Old flows still work
   # Migrate at your own pace
"""


# ============================================================================
# How to Migrate
# ============================================================================

"""
STEP 1: Update function signature
   OLD: def my_flow(logger, workspace_id, **params):
   NEW: def my_flow(param1, param2, **kwargs):

STEP 2: Get logger and workspace_id from context
   Add at the start of your flow:
   logger = get_logger()
   workspace_id = get_workspace_id()

STEP 3: Extract parameters directly
   OLD: parameters = params.get('parameters', {})
        batch_size = parameters.get('batch_size', 100)
   NEW: (parameters are function arguments)

STEP 4: Use get_block() instead of iterating blocks
   OLD: blocks = params.get('blocks', [])
        for block in blocks:
            if block['key_name'] == 'api-key':
                api_key = block['value']
   NEW: api_key_block = get_block('api-key')
        api_key = api_key_block.value

STEP 5: Remove manual secret redaction
   OLD: logger.info(f"API key: {'****' if api_key else 'none'}")
   NEW: logger.info(f"API key: {api_key}")  # Automatically redacted!
"""

