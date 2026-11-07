"""
Enterprise Configuration Backup with Nornir
Includes: Database logging, change detection, compliance checking
"""

import sqlite3
import hashlib
import difflib
import os
from datetime import datetime
from nornir.core.task import Task, Result
from nornir_netmiko.tasks import netmiko_send_command
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# TASK 1: Retrieve Configuration
# ============================================================================

def backup_config(task: Task) -> Result:
    """
    Retrieve running configuration from device
    
    Returns config data without saving (that's Task 2)
    """
    device_name = task.host.name
    device_ip = task.host.hostname
    
    logger.info(f"[{device_name}] Retrieving configuration...")
    
    try:
        result = task.run(
            netmiko_send_command,
            command_string="show running-config",
            use_textfsm=False,
            name="Get running config"
        )
        
        config = result[0].result
        
        if isinstance(config, str) and len(config) > 100:
            # Calculate config hash for change detection
            config_hash = hashlib.sha256(config.encode()).hexdigest()
            logger.info(f"[{device_name}] ✓ Retrieved {len(config):,} bytes")
            
            return Result(
                host=task.host,
                result={
                    'success': True,
                    'config': config,
                    'size': len(config),
                    'hash': config_hash,
                    'timestamp': datetime.now()
                }
            )
        else:
            logger.warning(f"[{device_name}] Config data invalid")
            return Result(
                host=task.host,
                result={'success': False, 'error': 'Invalid config data'},
                failed=True
            )
            
    except Exception as e:
        logger.error(f"[{device_name}] ✗ Connection failed: {str(e)}")
        return Result(
            host=task.host,
            result={'success': False, 'error': str(e)},
            failed=True
        )

# ============================================================================
# TASK 2: Save Configuration and Log to Database
# ============================================================================

def save_config(task: Task, config_data: dict, backup_dir: str = "configs", db_file: str = "backup.db") -> Result:
    """
    Save configuration to file and database
    Tracks: size, hash, timestamp, change status
    """
    device_name = task.host.name
    this_config = config_data.get(device_name)
    
    if not this_config or not this_config.get('success'):
        logger.warning(f"[{device_name}] Skipping save (config retrieval failed)")
        return Result(
            host=task.host,
            result={'success': False, 'reason': 'config_retrieval_failed'},
            failed=True
        )
    
    try:
        # Save to filesystem. Each run gets its own timestamped file:
        # detect_changes diffs against the previous run's file, so
        # overwriting one fixed filename would compare the config with itself
        os.makedirs(backup_dir, exist_ok=True)
        safe_name = device_name.replace('.', '-')
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_name}_{stamp}_running-config.txt"
        filepath = os.path.join(backup_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(this_config['config'])
        
        file_size = os.path.getsize(filepath)
        
        # Log to database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get previous backup to detect change
        cursor.execute('''
            SELECT id, config_hash FROM backups
            WHERE device_name = ?
            ORDER BY id DESC LIMIT 1
        ''', (device_name,))
        
        previous = cursor.fetchone()
        changed = False
        
        if previous:
            # Compare with previous
            previous_hash = previous[1]
            changed = (previous_hash != this_config['hash'])
        
        # Insert new backup record
        cursor.execute('''
            INSERT INTO backups (device_name, config_size, config_hash, changed, status, filepath)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (device_name, file_size, this_config['hash'], changed, 'success', filepath))
        
        backup_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        status_msg = "CHANGED" if changed else "unchanged"
        logger.info(f"[{device_name}] ✓ Saved ({status_msg}): {file_size:,} bytes")
        
        return Result(
            host=task.host,
            result={
                'success': True,
                'filepath': filepath,
                'size': file_size,
                'backup_id': backup_id,
                'changed': changed
            }
        )
        
    except Exception as e:
        logger.error(f"[{device_name}] Save failed: {str(e)}")
        return Result(
            host=task.host,
            result={'success': False, 'error': str(e)},
            failed=True
        )

# ============================================================================
# TASK 3: Detect Changes
# ============================================================================

def detect_changes(task: Task, current_config: dict, db_file: str = "backup.db") -> Result:
    """
    Compare current config with previous backup
    Calculate added/removed lines
    """
    device_name = task.host.name
    this_config = current_config.get(device_name)
    
    if not this_config:
        logger.warning(f"[{device_name}] Skipping change detection (no config)")
        return Result(
            host=task.host,
            result={'success': False, 'reason': 'config_retrieval_failed'},
            failed=True
        )
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get previous config
        cursor.execute('''
            SELECT b.id, b.filepath FROM backups b
            WHERE b.device_name = ? AND b.id < (
                SELECT MAX(id) FROM backups WHERE device_name = ?
            )
            ORDER BY b.id DESC LIMIT 1
        ''', (device_name, device_name))
        
        previous = cursor.fetchone()
        conn.close()
        
        if not previous:
            logger.info(f"[{device_name}] No previous backup (this is first)")
            return Result(
                host=task.host,
                result={
                    'success': True,
                    'changed': False,
                    'lines_added': 0,
                    'lines_removed': 0,
                    'summary': 'First backup'
                }
            )
        
        # Load previous config
        previous_id, previous_filepath = previous
        with open(previous_filepath, 'r') as f:
            previous_config = f.read()
        
        # Compare configs
        previous_lines = previous_config.splitlines()
        current_lines = this_config.splitlines()
        
        # Calculate difference
        differ = difflib.unified_diff(previous_lines, current_lines, lineterm='')
        diff_lines = list(differ)
        
        added = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        removed = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
        
        # Summarize changes
        if added == 0 and removed == 0:
            summary = "No changes"
            changed = False
        else:
            summary = f"+{added} lines, -{removed} lines"
            changed = True
        
        logger.info(f"[{device_name}] Changes detected: {summary}")
        
        return Result(
            host=task.host,
            result={
                'success': True,
                'changed': changed,
                'lines_added': added,
                'lines_removed': removed,
                'summary': summary,
                'previous_backup_id': previous_id
            }
        )
        
    except Exception as e:
        logger.error(f"[{device_name}] Change detection failed: {str(e)}")
        return Result(
            host=task.host,
            result={'success': False, 'error': str(e)},
            failed=True
        )

# ============================================================================
# TASK 4: Compliance Checking
# ============================================================================

def compliance_check(task: Task, config: dict, db_file: str = "backup.db") -> Result:
    """
    Check for common compliance issues:
    - Missing banner
    - Weak logging
    - Missing ACLs
    etc.
    """
    device_name = task.host.name
    config_text = config.get(device_name)

    if not config_text:
        # No config to check: don't score an empty string as "non-compliant"
        logger.warning(f"[{device_name}] Skipping compliance check (no config)")
        return Result(
            host=task.host,
            result={'success': False, 'reason': 'config_retrieval_failed'},
            failed=True
        )

    config_lower = config_text.lower()
    issues = []
    score = 100
    
    # Check for security configurations
    security_checks = {
        'banner motd': ('Missing MOTD banner', 10),
        'logging': ('Missing syslog configuration', 15),
        'enable secret': ('Weak enable password (not using secret)', 20),
        'access-list': ('No ACLs configured', 10),
        'ntp': ('Missing NTP configuration', 5),
        'snmp-server host': ('SNMP not configured', 5),
    }
    
    for check_key, (issue_desc, penalty) in security_checks.items():
        if check_key not in config_lower:
            issues.append(issue_desc)
            score -= penalty
    
    score = max(0, score)  # Don't go below 0
    
    try:
        # Store compliance check in database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        issues_str = "; ".join(issues) if issues else "All checks passed"
        
        cursor.execute('''
            INSERT INTO compliance (device_name, compliance_score, issues, status)
            VALUES (?, ?, ?, ?)
        ''', (device_name, score, issues_str, 'completed'))
        
        conn.commit()
        conn.close()
        
        logger.info(f"[{device_name}] Compliance score: {score}/100")
        
        return Result(
            host=task.host,
            result={
                'success': True,
                'score': score,
                'issues': issues,
                'passed_checks': len(security_checks) - len(issues)
            }
        )
        
    except Exception as e:
        logger.error(f"[{device_name}] Compliance check failed: {str(e)}")
        return Result(
            host=task.host,
            result={'success': False, 'error': str(e)},
            failed=True
        )

# ============================================================================
# TASK 5: Generate Summary Report
# ============================================================================

def generate_report(task: Task, all_results: dict) -> Result:
    """
    Generate text report of backup operation
    """
    device_name = task.host.name
    
    try:
        device_results = all_results.get(device_name, {})
        
        report_lines = [
            f"\n{'=' * 70}",
            f"Device: {device_name}",
            f"{'=' * 70}",
        ]
        
        # Config info
        if 'save_config' in device_results:
            save_info = device_results['save_config']
            if save_info.get('success'):
                report_lines.append(f"✓ Config saved: {save_info.get('size', 0):,} bytes")
            else:
                report_lines.append(f"✗ Config save failed: {save_info.get('error')}")
        
        # Change detection
        if 'detect_changes' in device_results:
            change_info = device_results['detect_changes']
            if change_info.get('success'):
                status = "CHANGED" if change_info.get('changed') else "unchanged"
                report_lines.append(f"Changes: {change_info.get('summary')}")
        
        # Compliance
        if 'compliance_check' in device_results:
            compliance_info = device_results['compliance_check']
            if compliance_info.get('success'):
                score = compliance_info.get('score', 0)
                report_lines.append(f"Compliance Score: {score}/100")
                if compliance_info.get('issues'):
                    report_lines.append(f"Issues: {len(compliance_info['issues'])}")
        
        report = "\n".join(report_lines)
        
        return Result(
            host=task.host,
            result={
                'success': True,
                'report': report
            }
        )
        
    except Exception as e:
        return Result(
            host=task.host,
            result={'success': False, 'error': str(e)},
            failed=True
        )
