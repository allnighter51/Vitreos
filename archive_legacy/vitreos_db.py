
import sqlite3
import logging
from typing import Dict, Any, TypedDict, List, Tuple
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot  # type: ignore[reportUnknownVariableType]

logger = logging.getLogger(__name__)

# TypedDict for database row results
class HardwareLogRow(TypedDict):
    timestamp: str
    cpu_temp: float
    cpu_usage: float
    gpu_temp: float
    gpu_usage: float
    ram_usage: float

class ProcessRuleRow(TypedDict):
    process_name: str
    rule_type: str
    rule_value: str

class VitreosDB:
    """
    Manages the SQLite database connection and executes queries in a dedicated
    background thread to prevent blocking the main UI.
    """

    class DatabaseWorker(QObject):
        """
        A dedicated QObject worker that lives in a separate QThread. It receives
        data via signals and performs all database write operations.
        """
        log_entry_requested = pyqtSignal(dict)

        def __init__(self, db_connection: sqlite3.Connection) -> None:
            super().__init__()
            self.connection: sqlite3.Connection = db_connection

        @pyqtSlot(dict)  # type: ignore[reportUntypedFunctionDecorator]
        def write_log_entry(self, stats_dict: Dict[str, Any]) -> None:
            """
            This slot receives a dictionary of hardware stats and writes them
            to the 'hardware_log' table in the database. This operation runs
            in the background thread.

            Args:
                stats_dict: A dictionary containing the latest hardware stats.
            """
            try:
                cursor: sqlite3.Cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO hardware_log (timestamp, cpu_temp, cpu_usage, gpu_temp, gpu_usage, ram_usage)
                    VALUES (datetime('now'), ?, ?, ?, ?, ?)
                """, (
                    stats_dict.get('cpu_temp', 0.0),
                    stats_dict.get('cpu_usage', 0.0),
                    stats_dict.get('gpu_temp', 0.0),
                    stats_dict.get('gpu_usage', 0.0),
                    stats_dict.get('ram_usage', 0.0),
                ))
                self.connection.commit()
                logger.debug("Successfully logged hardware stats to the database.")
            except Exception as e:
                logger.error(f"Database worker failed to write log entry: {e}")

    def __init__(self, db_path: str = "vitreos_history.db") -> None:
        """
        Initializes the database, creates the necessary tables, and starts the
        background worker thread for handling database operations.
        """
        # Use check_same_thread=False to allow the connection to be used
        # by the background worker thread.
        self.connection: sqlite3.Connection = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

        # Set up the background thread and worker
        self.db_thread: QThread = QThread()
        self.db_worker: VitreosDB.DatabaseWorker = self.DatabaseWorker(self.connection)
        self.db_worker.moveToThread(self.db_thread)

        # Connect the worker's slot to the signal that will carry the data
        self.db_worker.log_entry_requested.connect(self.db_worker.write_log_entry)  # type: ignore[arg-type]

        self.db_thread.start()
        logger.info("Database worker thread started successfully.")

    def create_tables(self) -> None:
        """
        Creates the 'hardware_log' and 'process_rules' tables if they don't already exist.
        """
        try:
            cursor: sqlite3.Cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hardware_log (
                    timestamp TEXT PRIMARY KEY,
                    cpu_temp REAL,
                    cpu_usage REAL,
                    gpu_temp REAL,
                    gpu_usage REAL,
                    ram_usage REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS process_rules (
                    process_name TEXT PRIMARY KEY,
                    rule_type TEXT NOT NULL,
                    rule_value TEXT NOT NULL
                )
            """)
            self.connection.commit()
            logger.info("Database tables verified and created if they didn't exist.")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")

    def log_stats(self, stats_dict: Dict[str, Any]) -> None:
        """
        Public method to be called from the main thread. It emits a signal
        to the background worker to log the provided hardware stats.
        """
        self.db_worker.log_entry_requested.emit(stats_dict)
    
    def log_event(self, event_type: str, message: str, severity: str) -> None:
        """
        Log a security or system event to the database.
        """
        # Placeholder for event logging - can be expanded
        logger.info(f"Event logged: {event_type} - {message} ({severity})")
    
    def save_process_rule(self, process_name: str, rule_type: str, rule_value: str) -> None:
        """
        Save or update a process tuning rule in the database.
        
        Args:
            process_name: The lowercase process name (e.g., 'discord.exe')
            rule_type: Either 'PRIORITY' or 'AFFINITY'
            rule_value: For PRIORITY: 'HIGH' or 'BELOW_NORMAL'. For AFFINITY: comma-separated core list (e.g., '6,7')
        """
        try:
            cursor: sqlite3.Cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO process_rules (process_name, rule_type, rule_value)
                VALUES (?, ?, ?)
            """, (process_name.lower(), rule_type, rule_value))
            self.connection.commit()
            logger.info(f"Saved process rule: {process_name} -> {rule_type}={rule_value}")
        except Exception as e:
            logger.error(f"Failed to save process rule: {e}")
    
    def get_all_process_rules(self) -> Dict[str, Tuple[str, str]]:
        """
        Retrieve all saved process rules from the database.
        
        Returns:
            Dictionary mapping process_name -> (rule_type, rule_value)
            Example: {'discord.exe': ('PRIORITY', 'BELOW_NORMAL'), 'r5apex.exe': ('PRIORITY', 'HIGH')}
        """
        rules: Dict[str, Tuple[str, str]] = {}
        try:
            cursor: sqlite3.Cursor = self.connection.cursor()
            cursor.execute("SELECT process_name, rule_type, rule_value FROM process_rules")
            rows: List[Tuple[str, str, str]] = cursor.fetchall()
            for process_name, rule_type, rule_value in rows:
                rules[process_name] = (rule_type, rule_value)
            logger.info(f"Loaded {len(rules)} process rules from database")
        except Exception as e:
            logger.error(f"Failed to load process rules: {e}")
        return rules
    
    def delete_process_rule(self, process_name: str) -> None:
        """
        Delete a process rule from the database.
        
        Args:
            process_name: The lowercase process name to remove
        """
        try:
            cursor: sqlite3.Cursor = self.connection.cursor()
            cursor.execute("DELETE FROM process_rules WHERE process_name = ?", (process_name.lower(),))
            self.connection.commit()
            logger.info(f"Deleted process rule: {process_name}")
        except Exception as e:
            logger.error(f"Failed to delete process rule: {e}")

    def close(self) -> None:
        """
        Cleans up resources by stopping the thread and closing the database
        connection.
        """
        self.db_thread.quit()
        self.db_thread.wait()
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed.")
