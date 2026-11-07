"""
Initialize the backup database schema
Run once: python init_db.py
"""

import sqlite3
import os

def init_database(db_file='backup.db'):
    """Create database tables for backup tracking"""
    
    # Create connection
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Table 1: Backup metadata
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_name TEXT NOT NULL,
        backup_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        config_size INTEGER,
        config_hash TEXT,
        changed BOOLEAN DEFAULT 0,
        status TEXT,
        filepath TEXT
    )
    ''')
    
    # Table 2: Compliance history
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS compliance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_name TEXT NOT NULL,
        check_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        compliance_score REAL,
        issues TEXT,
        status TEXT
    )
    ''')
    
    # Table 3: Changes detected
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_name TEXT NOT NULL,
        change_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        previous_backup_id INTEGER,
        new_backup_id INTEGER,
        lines_added INTEGER,
        lines_removed INTEGER,
        summary TEXT,
        FOREIGN KEY(previous_backup_id) REFERENCES backups(id),
        FOREIGN KEY(new_backup_id) REFERENCES backups(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✓ Database initialized: {db_file}")

if __name__ == "__main__":
    init_database()
