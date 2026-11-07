# query_backups.py
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("backup.db")
cursor = conn.cursor()

print("Recent Backups:")
cursor.execute('''
    SELECT device_name, backup_timestamp, config_size, changed
    FROM backups
    WHERE backup_timestamp > datetime('now', '-7 days')
    ORDER BY backup_timestamp DESC
    LIMIT 20
''')

for row in cursor.fetchall():
    device, timestamp, size, changed = row
    status = "📝 Changed" if changed else "✓ Unchanged"
    print(f"{device:<15} {timestamp:<20} {size:>10,} bytes  {status}")

print("\n\nCompliance Scores:")
cursor.execute('''
    SELECT device_name, compliance_score, MAX(check_timestamp)
    FROM compliance
    GROUP BY device_name
    ORDER BY compliance_score DESC
''')

for row in cursor.fetchall():
    device, score, timestamp = row
    print(f"{device:<15} {score:>6.1f}/100  ({timestamp})")

conn.close()
