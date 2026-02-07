"""
Central persistent state manager for the Mini Cloud Platform Simulator.
Loads and saves state to JSON files in backend/data/.
"""

import os
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

# Configure Data Directory
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

logger = logging.getLogger("system.state")

class SystemState:
    """Singleton state manager with JSON persistence."""
    
    _instance: Optional["SystemState"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        
        # File paths
        self.files = {
            "users": os.path.join(DATA_DIR, "users.json"),
            "services": os.path.join(DATA_DIR, "services.json"),
            "databases": os.path.join(DATA_DIR, "db.json"),
            "alerts": os.path.join(DATA_DIR, "alerts.json"),
            "security": os.path.join(DATA_DIR, "security.json")
        }
        
        # Load or Initialize Data
        self._load_data()

    def _load_data(self):
        """Load data from JSON files or init defaults."""
        self.users = self._load_file("users", self._default_users())
        self.services = self._load_file("services", self._default_services())
        self.databases = self._load_file("databases", self._default_databases())
        self.alerts = self._load_file("alerts", [])
        self.security = self._load_file("security", self._default_security())
        
    def _load_file(self, key: str, default: Any) -> Any:
        path = self.files[key]
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {key}: {e}")
                return default
        else:
            self._save_file(key, default)
            return default

    def _save_file(self, key: str, data: Any):
        path = self.files[key]
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save {key}: {e}")

    def _persist(self, key: str):
        """Save specific dataset to file."""
        if key == "users":
            self._save_file("users", self.users)
        elif key == "services":
            self._save_file("services", self.services)
        elif key == "databases":
            self._save_file("databases", self.databases)
        elif key == "alerts":
            self._save_file("alerts", self.alerts)
        elif key == "security":
            self._save_file("security", self.security)

    # --- Defaults ---

    def _default_users(self):
        now = datetime.now().isoformat()
        return {
            "root": {"id": "root", "name": "Root", "email": "root@platform.local", "role": "superadmin", "created_at": now},
            "alice": {"id": "alice", "name": "Alice", "email": "alice@platform.local", "role": "admin", "created_at": now},
            "bob": {"id": "bob", "name": "Bob", "email": "bob@platform.local", "role": "junior", "created_at": now},
        }

    def _default_services(self):
        now = datetime.now().isoformat()
        return {
            "auth": {"id": "auth", "name": "Authentication Service", "status": "running", "port": 8001, "health": "healthy", "started_at": now},
            "payments": {"id": "payments", "name": "Payments Service", "status": "running", "port": 8002, "health": "healthy", "started_at": now},
            "db": {"id": "db", "name": "Database Service", "status": "running", "port": 5432, "health": "healthy", "started_at": now},
        }

    def _default_databases(self):
        now = datetime.now().isoformat()
        return {
            "prod_db": {"id": "prod_db", "name": "Production Database", "type": "postgresql", "status": "healthy", "size_mb": 1024, "last_backup": (datetime.now() - timedelta(hours=2)).isoformat(), "created_at": now},
        }

    def _default_security(self):
        return {
            "audit_log": [],
            "locked_accounts": [],
            "keys": {"api_key_v1": "active"}
        }

    # --- Accessors & Modifiers ---

    # USERS
    def get_users(self) -> dict: return self.users
    def get_user(self, user_id: str) -> Optional[dict]: return self.users.get(user_id)
    def add_user(self, user_id: str, data: dict):
        with self._lock:
            data["id"] = user_id
            data["created_at"] = datetime.now().isoformat()
            self.users[user_id] = data
            self._persist("users")
            return data
    def update_user(self, user_id: str, updates: dict):
        with self._lock:
            if user_id in self.users:
                self.users[user_id].update(updates)
                self._persist("users")
                return self.users[user_id]
            return None
    def delete_user(self, user_id: str):
        with self._lock:
            if user_id in self.users:
                del self.users[user_id]
                self._persist("users")
                return True
            return False

    # SERVICES
    def get_services(self) -> dict: return self.services
    def get_service(self, service_id: str) -> Optional[dict]: return self.services.get(service_id)
    def update_service(self, service_id: str, updates: dict):
        with self._lock:
            if service_id in self.services:
                self.services[service_id].update(updates)
                self._persist("services")
                return self.services[service_id]
            return None

    # DATABASES
    def get_databases(self) -> dict: return self.databases
    def get_database(self, db_id: str) -> Optional[dict]: return self.databases.get(db_id)
    def update_database(self, db_id: str, updates: dict):
        with self._lock:
            if db_id in self.databases:
                self.databases[db_id].update(updates)
                self._persist("databases")
                return self.databases[db_id]
            return None
    
<<<<<<< Updated upstream
    # ----- Alert Methods -----
    def get_alerts(self) -> list:
        return self.alerts
    
    def get_alert(self, alert_id: str) -> Optional[dict]:
        """Get a specific alert by ID."""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                return alert
        return None

    def add_alert(self, alert: dict) -> dict:
=======
    # ALERTS
    def get_alerts(self) -> list: return self.alerts
    def add_alert(self, alert: dict):
>>>>>>> Stashed changes
        with self._lock:
            alert["id"] = f"alert_{len(self.alerts) + 1}"
            alert["created_at"] = datetime.now().isoformat()
            alert["resolved"] = False
            self.alerts.append(alert)
            self._persist("alerts")
            return alert
    def resolve_alert(self, alert_id: str):
        with self._lock:
            for alert in self.alerts:
                if alert["id"] == alert_id:
                    alert["resolved"] = True
                    alert["resolved_at"] = datetime.now().isoformat()
                    self._persist("alerts")
                    return alert
            return None
    
    # SECURITY
    def log_audit(self, entry: dict):
        with self._lock:
            entry["timestamp"] = datetime.now().isoformat()
            self.security["audit_log"].append(entry)
            self._persist("security")

    def get_audit_log(self, limit: int = 50):
        return self.security["audit_log"][-limit:]

    def lock_account(self, user_id: str):
        with self._lock:
            if user_id not in self.security["locked_accounts"]:
                self.security["locked_accounts"].append(user_id)
                self._persist("security")

    def unlock_account(self, user_id: str):
        with self._lock:
            if user_id in self.security["locked_accounts"]:
                self.security["locked_accounts"].remove(user_id)
                self._persist("security")
            
    def is_locked(self, user_id: str) -> bool:
        return user_id in self.security["locked_accounts"]

# Global singleton instance
state = SystemState()
