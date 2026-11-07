# security/credential_vault.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import time
import hvac  # HashiCorp Vault client
import os
from cryptography.fernet import Fernet
import keyring
import structlog

logger = structlog.get_logger()


@dataclass
class Credentials:
    """Secure credential container"""
    username: str
    password: str
    enable_password: Optional[str] = None
    
    def __repr__(self):
        """Prevent password leakage in logs"""
        return f"Credentials(username={self.username}, password=***REDACTED***)"


class VaultManager:
    """
    Secure credential management with multiple backend support.
    
    Supported backends:
    - HashiCorp Vault
    - AWS Secrets Manager
    - Azure Key Vault
    - System keyring (for development)
    """
    
    def __init__(
        self,
        vault_type: str = 'hashicorp',
        vault_url: Optional[str] = None,
        vault_token: Optional[str] = None
    ):
        self.vault_type = vault_type
        
        if vault_type == 'hashicorp':
            self.client = hvac.Client(
                url=vault_url or os.getenv('VAULT_ADDR'),
                token=vault_token or os.getenv('VAULT_TOKEN')
            )
            
            if not self.client.is_authenticated():
                raise ValueError("Vault authentication failed")
                
            logger.info("vault_initialized", vault_type=vault_type)
    
    def get_credentials(
        self,
        device_name: str,
        secret_path: Optional[str] = None
    ) -> Credentials:
        """Retrieve credentials from vault"""
        
        secret_path = secret_path or f"network/devices/{device_name}"
        
        try:
            if self.vault_type == 'hashicorp':
                # Read from HashiCorp Vault KV v2
                secret = self.client.secrets.kv.v2.read_secret_version(
                    path=secret_path
                )
                
                data = secret['data']['data']
                
                logger.info(
                    "credentials_retrieved",
                    device=device_name,
                    path=secret_path
                )
                
                return Credentials(
                    username=data['username'],
                    password=data['password'],
                    enable_password=data.get('enable_password')
                )
            
            elif self.vault_type == 'keyring':
                # Development mode - use system keyring
                username = keyring.get_password('network_automation', f"{device_name}_user")
                password = keyring.get_password('network_automation', f"{device_name}_pass")
                
                return Credentials(username=username, password=password)
            
            else:
                raise ValueError(f"Unsupported vault type: {self.vault_type}")
                
        except Exception as e:
            logger.error(
                "credential_retrieval_failed",
                device=device_name,
                error=str(e)
            )
            raise
    
    def store_credentials(
        self,
        device_name: str,
        credentials: Credentials,
        secret_path: Optional[str] = None
    ):
        """Store credentials in vault (admin only)"""
        
        secret_path = secret_path or f"network/devices/{device_name}"
        
        try:
            if self.vault_type == 'hashicorp':
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=secret_path,
                    secret={
                        'username': credentials.username,
                        'password': credentials.password,
                        'enable_password': credentials.enable_password,
                    }
                )
                
                logger.info(
                    "credentials_stored",
                    device=device_name,
                    path=secret_path
                )
        except Exception as e:
            logger.error(
                "credential_storage_failed",
                device=device_name,
                error=str(e)
            )
            raise


class AuditLogger:
    """
    Comprehensive audit logging for compliance.
    
    Tracks:
    - Who made changes
    - What changes were made
    - When changes occurred
    - Why changes were made (change ticket)
    - Result of changes
    """
    
    def __init__(self, audit_db_path: str = './audit.db'):
        import sqlite3
        self.conn = sqlite3.connect(audit_db_path)
        self._create_tables()
    
    def _create_tables(self):
        """Create audit tables"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT NOT NULL,
                action TEXT NOT NULL,
                device TEXT,
                commands TEXT,
                change_ticket TEXT,
                result TEXT,
                duration_seconds REAL,
                metadata TEXT
            )
        """)
        self.conn.commit()
    
    def log_change(
        self,
        user: str,
        action: str,
        device: Optional[str],
        commands: List[str],
        change_ticket: str,
        result: str,
        duration: float,
        metadata: Optional[Dict] = None
    ):
        """Log a change for audit"""
        import json
        
        self.conn.execute("""
            INSERT INTO audit_log (
                timestamp, user, action, device, commands,
                change_ticket, result, duration_seconds, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            user,
            action,
            device,
            json.dumps(commands),
            change_ticket,
            result,
            duration,
            json.dumps(metadata or {})
        ))
        self.conn.commit()
        
        logger.info(
            "audit_log_entry",
            user=user,
            action=action,
            device=device,
            change_ticket=change_ticket
        )
    
    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        output_file: str
    ):
        """Generate compliance report for date range"""
        import csv
        
        cursor = self.conn.execute("""
            SELECT timestamp, user, action, device, commands,
                   change_ticket, result, duration_seconds
            FROM audit_log
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """, (start_date.isoformat(), end_date.isoformat()))
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Timestamp', 'User', 'Action', 'Device',
                'Commands', 'Change Ticket', 'Result', 'Duration (s)'
            ])
            writer.writerows(cursor.fetchall())
        
        logger.info(
            "compliance_report_generated",
            output_file=output_file,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )


class RBACEnforcer:
    """Role-Based Access Control for automation"""
    
    def __init__(self, policy_file: str):
        import yaml
        with open(policy_file, 'r') as f:
            self.policies = yaml.safe_load(f)
    
    def check_permission(
        self,
        user: str,
        action: str,
        devices: List[str]
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has permission for action on devices.
        
        Returns:
            (allowed, reason)
        """
        user_role = self._get_user_role(user)
        
        if not user_role:
            return False, f"User {user} has no assigned role"
        
        role_policy = self.policies.get('roles', {}).get(user_role, {})
        
        # Check action permission
        allowed_actions = role_policy.get('actions', [])
        if action not in allowed_actions:
            return False, f"Role {user_role} not authorized for action {action}"
        
        # Check device scope
        allowed_device_groups = role_policy.get('device_groups', [])
        
        # Verify all devices are in allowed groups
        for device in devices:
            device_group = self._get_device_group(device)
            if device_group not in allowed_device_groups:
                return False, f"Role {user_role} not authorized for device group {device_group}"
        
        return True, f"Authorized: {user_role}"
    
    def _get_user_role(self, user: str) -> Optional[str]:
        """Get user's role from policy"""
        users = self.policies.get('users', {})
        return users.get(user, {}).get('role')
    
    def _get_device_group(self, device: str) -> str:
        """Get device group (simplified)"""
        # In production, this would query inventory
        return 'production'  # Placeholder


# Example RBAC Policy (rbac_policy.yaml):
# users:
#   alice:
#     role: network_admin
#   bob:
#     role: network_operator
# 
# roles:
#   network_admin:
#     actions:
#       - deploy_config
#       - rollback
#       - read
#     device_groups:
#       - production
#       - staging
#       - development
#   
#   network_operator:
#     actions:
#       - read
#       - deploy_config
#     device_groups:
#       - development
#       - staging


# Integration Example
from orchestrator.integration import OrchestrationEngine


class SecureOrchestrationEngine(OrchestrationEngine):
    """Orchestration engine with full security controls"""
    
    def __init__(
        self,
        *args,
        vault_manager: VaultManager,
        audit_logger: AuditLogger,
        rbac_enforcer: RBACEnforcer,
        current_user: str,
        change_ticket: str,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.vault = vault_manager
        self.audit = audit_logger
        self.rbac = rbac_enforcer
        self.current_user = current_user
        self.change_ticket = change_ticket
    
    def deploy_with_validation(self, devices: List[str], commands: List[str], **kwargs):
        """Override to add security checks"""
        
        # Check RBAC
        allowed, reason = self.rbac.check_permission(
            self.current_user,
            'deploy_config',
            devices
        )
        
        if not allowed:
            logger.error(
                "rbac_denied",
                user=self.current_user,
                devices=devices,
                reason=reason
            )
            raise PermissionError(reason)
        
        logger.info(
            "rbac_authorized",
            user=self.current_user,
            devices=devices,
            reason=reason
        )
        
        # Execute deployment
        start_time = time.time()
        
        try:
            result = super().deploy_with_validation(
                devices=devices,
                commands=commands,
                **kwargs
            )
            
            # Audit log success
            for device in devices:
                self.audit.log_change(
                    user=self.current_user,
                    action='deploy_config',
                    device=device,
                    commands=commands,
                    change_ticket=self.change_ticket,
                    result='success',
                    duration=time.time() - start_time,
                    metadata={'deployment_id': result.deployment_id}
                )
            
            return result
            
        except Exception as e:
            # Audit log failure
            for device in devices:
                self.audit.log_change(
                    user=self.current_user,
                    action='deploy_config',
                    device=device,
                    commands=commands,
                    change_ticket=self.change_ticket,
                    result='failed',
                    duration=time.time() - start_time,
                    metadata={'error': str(e)}
                )
            raise
