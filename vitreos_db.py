"""SQLite database module for Vitreos hardware history logging"""

import sqlite3
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VitreosDatabase:
    """Manages SQLite database for hardware monitoring history"""
    
    def __init__(self, db_path: str = "vitreos_history.db"):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        self._initialize_database()
        logger.info(f"VitreosDatabase initialized at {self.db_path}")
    
    def _initialize_database(self):
        """Create database and tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.isolation_level = None  # Autocommit mode
            cursor = conn.cursor()
            
            # Create hardware_logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hardware_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_temp REAL NOT NULL,
                    gpu_temp REAL NOT NULL,
                    power_draw REAL NOT NULL
                )
            ''')
            
            conn.close()
            logger.info("Database tables created/verified")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
    
    def insert_hardware_log(self, cpu_temp: float, gpu_temp: float, power_draw: float):
        """Insert hardware stats record into database (thread-safe)"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create new connection for this operation (thread-safe)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO hardware_logs (timestamp, cpu_temp, gpu_temp, power_draw)
                VALUES (?, ?, ?, ?)
            ''', (timestamp, cpu_temp, gpu_temp, power_draw))
            
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            logger.error(f"Failed to insert hardware log: {e}")
    
    def get_recent_logs(self, limit: int = 100) -> list:
        """Retrieve recent hardware logs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, cpu_temp, gpu_temp, power_draw
                FROM hardware_logs
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            return rows
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve logs: {e}")
            return []
    
    def clear_old_logs(self, days: int = 30):
        """Delete logs older than specified days (maintenance)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM hardware_logs
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            conn.commit()
            deleted_count = cursor.rowcount
            conn.close()
            
            logger.info(f"Deleted {deleted_count} old hardware logs")
        except sqlite3.Error as e:
            logger.error(f"Failed to clear old logs: {e}")
