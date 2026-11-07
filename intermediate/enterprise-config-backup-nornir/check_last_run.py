# Check when last backup ran
import sqlite3
from datetime import datetime

conn = sqlite3.connect("backup.db")
cursor = conn.cursor()

cursor.execute('''
    SELECT device_name, MAX(backup_timestamp) as last_backup
    FROM backups
    GROUP BY device_name
    ORDER BY last_backup DESC
    LIMIT 20
''')

for device, last_backup in cursor.fetchall():
    timestamp = datetime.fromisoformat(last_backup)
    age_hours = (datetime.now() - timestamp).total_seconds() / 3600
    status = "✓ Current" if age_hours < 25 else "⚠ Overdue"
    print(f"{device:<20} {timestamp} {status}")
