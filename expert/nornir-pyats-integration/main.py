# main.py - Complete production orchestration system
import sys
import argparse
from pathlib import Path
from datetime import datetime
import structlog

# Import all our modules
from inventory_manager import UnifiedInventoryManager
from orchestrator.integration import OrchestrationEngine, DeploymentPhase
from validation.pyats_validator import PyATSValidator
from tasks.config_management import ConfigurationManager
from security.credential_vault import VaultManager, AuditLogger, RBACEnforcer
from observability.metrics import AutomationMetrics, AlertingEngine
from error_handling import ErrorRegistry
from logging_config import configure_structured_logging


def setup_logging(log_level: str = 'INFO'):
    """Configure comprehensive logging"""
    configure_structured_logging(
        log_dir='./logs',
        log_level=log_level,
        enable_json=True
    )


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Network Automation Orchestration System'
    )
    
    parser.add_argument(
        '--devices',
        nargs='+',
        help='Target devices (default: all devices from inventory)'
    )
    
    parser.add_argument(
        '--site',
        help='Filter devices by site'
    )
    
    parser.add_argument(
        '--role',
        help='Filter devices by role'
    )
    
    parser.add_argument(
        '--commands',
        nargs='+',
        required=True,
        help='Configuration commands to execute'
    )
    
    parser.add_argument(
        '--change-ticket',
        required=True,
        help='Change ticket number for audit trail'
    )
    
    parser.add_argument(
        '--user',
        required=True,
        help='Username executing the change'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Execute in dry-run mode (no actual changes)'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        default=True,
        help='Execute in parallel (default: True)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Batch size for large deployments'
    )
    
    return parser.parse_args()


def main():
    """Main orchestration workflow"""
    
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging()
    logger = structlog.get_logger()
    
    logger.info(
        "automation_starting",
        user=args.user,
        change_ticket=args.change_ticket,
        dry_run=args.dry_run
    )
    
    try:
        # Step 1: Initialize security components
        logger.info("initializing_security")
        
        vault = VaultManager(
            vault_type='hashicorp',
            vault_url='https://vault.example.com'
        )
        
        audit = AuditLogger(audit_db_path='./audit.db')
        
        rbac = RBACEnforcer(policy_file='./rbac_policy.yaml')
        
        # Step 2: Initialize observability
        logger.info("initializing_observability")
        
        metrics = AutomationMetrics(
            pushgateway_url='http://prometheus-pushgateway:9091'
        )
        
        alerting = AlertingEngine()
        alerting.add_slack_channel('https://hooks.slack.com/services/YOUR/WEBHOOK')
        
        # Step 3: Generate unified inventory
        logger.info("generating_inventory")
        
        inv_mgr = UnifiedInventoryManager(
            netbox_url='https://netbox.example.com',
            netbox_token='your_token_here'
        )
        
        # Apply filters
        filters = {}
        if args.site:
            filters['site'] = args.site
        if args.role:
            filters['role'] = args.role
        
        # Generate both inventory types
        nornir_inv = inv_mgr.generate_nornir_inventory(filters)
        pyats_testbed = inv_mgr.generate_pyats_testbed(filters)
        
        # Save to disk
        inv_mgr.save_testbed(pyats_testbed, './testbed.yaml')
        
        # Step 4: Check RBAC permissions
        logger.info("checking_permissions", user=args.user)
        
        target_devices = args.devices if args.devices else list(nornir_inv['hosts'].keys())
        
        allowed, reason = rbac.check_permission(
            user=args.user,
            action='deploy_config',
            devices=target_devices
        )
        
        if not allowed:
            logger.error("permission_denied", user=args.user, reason=reason)
            sys.exit(1)
        
        logger.info("permission_granted", user=args.user, reason=reason)
        
        # Step 5: Initialize orchestration engine
        logger.info("initializing_orchestration")
        
        engine = OrchestrationEngine(
            nornir_config='./nornir_config.yaml',
            pyats_testbed='./testbed.yaml',
            state_dir='./states',
            report_dir='./reports',
            dry_run=args.dry_run,
            max_retries=3,
            circuit_breaker_threshold=0.20
        )
        
        # Add metrics tracking
        engine.metrics = metrics
        engine.alerting = alerting
        
        # Step 6: Execute deployment
        logger.info(
            "starting_deployment",
            devices=len(target_devices),
            commands=len(args.commands)
        )
        
        start_time = datetime.utcnow()
        
        deployment = engine.deploy_with_validation(
            devices=target_devices,
            commands=args.commands,
            validation_features=['interface', 'bgp'],
            rollback_on_failure=True,
            parallel=args.parallel,
            max_workers=10
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Step 7: Record audit trail
        logger.info("recording_audit")
        
        for device in target_devices:
            change_record = deployment.change_records.get(device)
            result = 'success' if change_record and change_record.state.value == 'completed' else 'failed'
            
            audit.log_change(
                user=args.user,
                action='deploy_config',
                device=device,
                commands=args.commands,
                change_ticket=args.change_ticket,
                result=result,
                duration=execution_time,
                metadata={'deployment_id': deployment.deployment_id}
            )
        
        # Step 8: Generate reports
        logger.info("generating_reports")
        
        from reporting import ReportGenerator
        report_gen = ReportGenerator(deployment, output_dir='./reports')
        report_gen.generate_all_reports()
        
        # Step 9: Summary
        success_count = sum(
            1 for cr in deployment.change_records.values()
            if cr.state.value == 'completed'
        )
        
        logger.info(
            "deployment_complete",
            deployment_id=deployment.deployment_id,
            phase=deployment.phase.value,
            total_devices=len(target_devices),
            successful=success_count,
            failed=len(target_devices) - success_count,
            execution_time=execution_time
        )
        
        # Print summary to console
        print(f"\n{'='*70}")
        print(f"Deployment Complete: {deployment.deployment_id}")
        print(f"{'='*70}")
        print(f"Status: {deployment.phase.value}")
        print(f"Success: {success_count}/{len(target_devices)} devices")
        print(f"Execution Time: {execution_time:.2f}s")
        print(f"Reports: ./reports/{deployment.deployment_id}_*.*")
        print(f"{'='*70}\n")
        
        # Exit code based on success
        sys.exit(0 if deployment.phase == DeploymentPhase.COMPLETE else 1)
        
    except Exception as e:
        logger.critical(
            "automation_failed",
            error=str(e),
            user=args.user,
            change_ticket=args.change_ticket
        )
        
        # Send critical alert
        if 'alerting' in locals():
            alerting.send_alert(
                severity='critical',
                title='Automation System Failure',
                message=str(e),
                context={
                    'user': args.user,
                    'change_ticket': args.change_ticket
                }
            )
        
        sys.exit(1)


if __name__ == '__main__':
    main()
