"""
Quick Start Example - New LastCron SDK Features

This example demonstrates the new features in a simple, practical way:
1. Flow.submit() - Trigger flows by calling the function
2. get_block() - Retrieve configuration blocks on-demand
3. Strong typing - Type-safe dataclasses
4. Clean flow signatures - Only receive your custom parameters

Run this to see how the new SDK features work together.
"""

from lastcron_sdk import flow, get_block, get_run_logger, get_workspace_id, Block, FlowRun, BlockType
from datetime import datetime, timedelta


# ============================================================================
# Define some flows
# ============================================================================

@flow
def send_email(recipient='user@example.com', subject='Hello', **params):
    """
    Sends an email using SMTP credentials from a block.

    Notice: No logger or workspace_id parameters!
    Access them via get_run_logger() and get_workspace_id()
    """
    logger = get_run_logger()

    logger.info(f"Sending email to {recipient}")
    
    # Get SMTP credentials from a block
    smtp_config: Block = get_block('smtp-credentials')
    
    if smtp_config:
        logger.info(f"Using SMTP config: {smtp_config.key_name}")
        logger.info(f"Config type: {smtp_config.type.value}")
        logger.info(f"Is secret: {smtp_config.is_secret}")
        
        # In real code, you would:
        # import smtplib
        # config = json.loads(smtp_config.value)
        # server = smtplib.SMTP(config['host'], config['port'])
        # server.login(config['username'], config['password'])
        # server.sendmail(sender, recipient, message)
        
        logger.info(f"Email sent to {recipient}")
    else:
        logger.error("SMTP credentials not found!")


@flow
def generate_report(type='daily', **params):
    """
    Generates a report and saves it to S3.
    """
    logger = get_run_logger()

    logger.info(f"Generating {type} report")
    
    # Get AWS credentials from a block
    aws_creds: Block = get_block('aws-credentials')
    
    if aws_creds:
        logger.info("Using AWS credentials to upload report")
        
        # In real code, you would:
        # import boto3
        # creds = json.loads(aws_creds.value)
        # s3 = boto3.client('s3', 
        #                   aws_access_key_id=creds['access_key'],
        #                   aws_secret_access_key=creds['secret_key'])
        # s3.upload_file('report.pdf', 'my-bucket', 'reports/daily.pdf')
        
        logger.info("Report uploaded to S3")
    else:
        logger.warning("AWS credentials not found, saving locally")


@flow
def cleanup_old_data(days_old=30, **params):
    """
    Cleans up old data from the database.
    """
    logger = get_run_logger()

    logger.info(f"Cleaning up data older than {days_old} days")
    
    # Get database credentials
    db_creds: Block = get_block('database-credentials')
    
    if db_creds:
        logger.info("Connecting to database")
        
        # In real code, you would:
        # import psycopg2
        # creds = json.loads(db_creds.value)
        # conn = psycopg2.connect(
        #     host=creds['host'],
        #     database=creds['database'],
        #     user=creds['user'],
        #     password=creds['password']
        # )
        # cursor = conn.cursor()
        # cursor.execute(f"DELETE FROM logs WHERE created_at < NOW() - INTERVAL '{days_old} days'")
        
        logger.info("Old data cleaned up")
    else:
        logger.error("Database credentials not found!")


# ============================================================================
# Main orchestrator flow
# ============================================================================

@flow
def daily_workflow(**params):
    """
    Main workflow that orchestrates multiple tasks.

    This demonstrates:
    - Using .submit() to trigger flows
    - Getting configuration from blocks
    - Type-safe returns (FlowRun, Block)
    - Scheduling flows for later
    - Clean flow signatures (no logger/workspace_id params)
    """
    logger = get_run_logger()
    workspace_id = get_workspace_id()

    logger.info("=== Daily Workflow Started ===")
    logger.info(f"Running in workspace {workspace_id}")
    
    # Get workflow configuration
    workflow_config: Block = get_block('workflow-config')
    
    if workflow_config:
        logger.info(f"Loaded workflow config: {workflow_config.key_name}")
        
        # Check if it's JSON config
        if workflow_config.type == BlockType.JSON:
            logger.info("Config is JSON format")
            # import json
            # config = json.loads(workflow_config.value)
            # enabled_tasks = config.get('enabled_tasks', [])
    else:
        logger.info("No workflow config found, using defaults")
    
    # Task 1: Generate daily report
    logger.info("\n--- Task 1: Generate Report ---")
    report_run: FlowRun = generate_report.submit(
        parameters={'type': 'daily'}
    )
    
    if report_run:
        logger.info(f"✓ Report generation triggered")
        logger.info(f"  Run ID: {report_run.id}")
        logger.info(f"  Flow ID: {report_run.flow_id}")
        logger.info(f"  State: {report_run.state.value}")
        logger.info(f"  Parameters: {report_run.parameters}")
    else:
        logger.error("✗ Failed to trigger report generation")
    
    # Task 2: Send notification email
    logger.info("\n--- Task 2: Send Email ---")
    email_run: FlowRun = send_email.submit(
        parameters={
            'recipient': 'admin@example.com',
            'subject': 'Daily Report Generated'
        }
    )
    
    if email_run:
        logger.info(f"✓ Email sending triggered")
        logger.info(f"  Run ID: {email_run.id}")
    else:
        logger.error("✗ Failed to trigger email")
    
    # Task 3: Schedule cleanup for tonight (2 AM)
    logger.info("\n--- Task 3: Schedule Cleanup ---")
    
    # Calculate 2 AM tomorrow
    now = datetime.now()
    tomorrow_2am = now.replace(hour=2, minute=0, second=0, microsecond=0)
    if tomorrow_2am <= now:
        tomorrow_2am += timedelta(days=1)
    
    cleanup_run: FlowRun = cleanup_old_data.submit(
        parameters={'days_old': 30},
        scheduled_start=tomorrow_2am
    )
    
    if cleanup_run:
        logger.info(f"✓ Cleanup scheduled")
        logger.info(f"  Run ID: {cleanup_run.id}")
        logger.info(f"  Scheduled for: {cleanup_run.scheduled_start}")
        
        # Check if it's actually scheduled
        from lastcron_sdk import FlowRunState
        if cleanup_run.state == FlowRunState.PENDING:
            logger.info("  Status: Pending execution")
    else:
        logger.error("✗ Failed to schedule cleanup")
    
    logger.info("\n=== Daily Workflow Completed ===")
    logger.info(f"Triggered {sum([1 for r in [report_run, email_run, cleanup_run] if r])} tasks")


# ============================================================================
# Alternative: Using run_flow() (old way, still works)
# ============================================================================

@flow
def daily_workflow_old_style(**params):
    """
    Same workflow using the old run_flow() approach.

    This still works, but .submit() is recommended for new code.
    """
    from lastcron_sdk import run_flow

    logger = get_run_logger()

    logger.info("=== Daily Workflow (Old Style) ===")
    
    # Old way: use run_flow() with string names
    report_run = run_flow('generate_report', parameters={'type': 'daily'})
    
    if report_run:
        # Returns FlowRun dataclass (same as .submit())
        logger.info(f"Report run ID: {report_run.id}")
    
    # New way: get blocks on-demand
    smtp_config = get_block('smtp-credentials')

    if smtp_config:
        logger.info(f"Found SMTP config: {smtp_config.key_name}")


# ============================================================================
# Comparison: Old vs New
# ============================================================================

@flow
def comparison_example(**params):
    """
    Side-by-side comparison of old and new approaches.
    """
    logger = get_run_logger()

    logger.info("=== Old vs New Comparison ===\n")

    # ========================================
    # OLD WAY
    # ========================================
    logger.info("--- OLD WAY ---")

    # Triggering flows: string-based, no type safety
    from lastcron_sdk import run_flow
    run = run_flow('send_email', parameters={'recipient': 'user@example.com'})
    if run:
        logger.info(f"Run ID: {run.id}")  # Still typed as FlowRun
    
    # ========================================
    # NEW WAY (RECOMMENDED)
    # ========================================
    logger.info("\n--- NEW WAY (RECOMMENDED) ---")
    
    # Triggering flows: function-based, type-safe
    run: FlowRun = send_email.submit(
        parameters={'recipient': 'user@example.com'}
    )
    if run:
        logger.info(f"Run ID: {run.id}")  # IDE knows this is int
        logger.info(f"State: {run.state.value}")  # IDE knows this is FlowRunState
    
    # Getting blocks: direct retrieval, type-safe
    api_key_block: Block = get_block('api-key')
    if api_key_block:
        logger.info(f"API key found: {api_key_block.value[:10]}...")
        logger.info(f"Is secret: {api_key_block.is_secret}")  # IDE knows this is bool
    
    logger.info("\n✓ New way is cleaner and type-safe!")

