# src/config_backup.py
import json
from datetime import datetime, timezone
from pathlib import Path

class ConfigurationBackup:
    """Backup device configuration before changes."""
    
    def __init__(self, device, backup_dir="config_backups"):
        self.device = device
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backup_file = None
    
    def backup_running_config(self):
        """Backup current running configuration."""
        try:
            config = self.device.send_command("show running-config")
            
            # Create backup file
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = self.backup_dir / f"{self.device.host}_{timestamp}.cfg"
            
            with open(filename, 'w') as f:
                f.write(config)
            
            self.backup_file = filename
            
            return {
                "status": "success",
                "filename": str(filename),
                "lines": len(config.split('\n'))
            }
        
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def get_config_checksum(self):
        """Get MD5 checksum of running configuration."""
        try:
            import hashlib
            config = self.device.send_command("show running-config")
            checksum = hashlib.md5(config.encode()).hexdigest()
            return checksum
        except Exception as e:
            return None
