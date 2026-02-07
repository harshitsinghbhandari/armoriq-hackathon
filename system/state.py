"""
Central in-memory state manager for the Mini Cloud Platform Simulator.
Singleton-style class with sample data and getter/update methods.
"""

from datetime import datetime, timedelta
from typing import Optional
import threading


class SystemState:
    """Singleton state manager for all platform data."""
    
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
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize with sample data."""
        now = datetime.now().isoformat()
        
        # Users: role-based access
        self.users = {
            "root": {
                "id": "root",
                "name": "Root",
                "email": "root@platform.local",
                "role": "superadmin",
                "created_at": now,
            },
            "alice": {
                "id": "alice",
                "name": "Alice",
                "email": "alice@platform.local",
                "role": "admin",
                "created_at": now,
            },
            "bob": {
                "id": "bob",
                "name": "Bob",
                "email": "bob@platform.local",
                "role": "junior",
                "created_at": now,
            },
        }
        
        # Services: running microservices
        self.services = {
            "auth": {
                "id": "auth",
                "name": "Authentication Service",
                "status": "running",
                "port": 8001,
                "health": "healthy",
                "started_at": now,
            },
            "payments": {
                "id": "payments",
                "name": "Payments Service",
                "status": "running",
                "port": 8002,
                "health": "healthy",
                "started_at": now,
            },
            "db": {
                "id": "db",
                "name": "Database Service",
                "status": "running",
                "port": 5432,
                "health": "healthy",
                "started_at": now,
            },
        }
        
        # Databases: storage instances
        last_backup = (datetime.now() - timedelta(hours=2)).isoformat()
        self.databases = {
            "prod_db": {
                "id": "prod_db",
                "name": "Production Database",
                "type": "postgresql",
                "status": "healthy",
                "size_mb": 1024,
                "last_backup": last_backup,
                "created_at": now,
            },
        }
        
        # Alerts: system notifications
        self.alerts = []
    
    # ----- User Methods -----
    def get_users(self) -> dict:
        return self.users
    
    def get_user(self, user_id: str) -> Optional[dict]:
        return self.users.get(user_id)
    
    def add_user(self, user_id: str, data: dict) -> dict:
        with self._lock:
            data["id"] = user_id
            data["created_at"] = datetime.now().isoformat()
            self.users[user_id] = data
            return data
    
    def update_user(self, user_id: str, updates: dict) -> Optional[dict]:
        with self._lock:
            if user_id not in self.users:
                return None
            self.users[user_id].update(updates)
            return self.users[user_id]
    
    def delete_user(self, user_id: str) -> bool:
        with self._lock:
            if user_id in self.users:
                del self.users[user_id]
                return True
            return False
    
    # ----- Service Methods -----
    def get_services(self) -> dict:
        return self.services
    
    def get_service(self, service_id: str) -> Optional[dict]:
        return self.services.get(service_id)
    
    def add_service(self, service_id: str, data: dict) -> dict:
        with self._lock:
            data["id"] = service_id
            data["started_at"] = datetime.now().isoformat()
            self.services[service_id] = data
            return data
    
    def update_service(self, service_id: str, updates: dict) -> Optional[dict]:
        with self._lock:
            if service_id not in self.services:
                return None
            self.services[service_id].update(updates)
            return self.services[service_id]
    
    def delete_service(self, service_id: str) -> bool:
        with self._lock:
            if service_id in self.services:
                del self.services[service_id]
                return True
            return False
    
    # ----- Database Methods -----
    def get_databases(self) -> dict:
        return self.databases
    
    def get_database(self, db_id: str) -> Optional[dict]:
        return self.databases.get(db_id)
    
    def add_database(self, db_id: str, data: dict) -> dict:
        with self._lock:
            data["id"] = db_id
            data["created_at"] = datetime.now().isoformat()
            self.databases[db_id] = data
            return data
    
    def update_database(self, db_id: str, updates: dict) -> Optional[dict]:
        with self._lock:
            if db_id not in self.databases:
                return None
            self.databases[db_id].update(updates)
            return self.databases[db_id]
    
    def delete_database(self, db_id: str) -> bool:
        with self._lock:
            if db_id in self.databases:
                del self.databases[db_id]
                return True
            return False
    
    # ----- Alert Methods -----
    def get_alerts(self) -> list:
        return self.alerts
    
    def add_alert(self, alert: dict) -> dict:
        with self._lock:
            alert["id"] = f"alert_{len(self.alerts) + 1}"
            alert["created_at"] = datetime.now().isoformat()
            alert["resolved"] = False
            self.alerts.append(alert)
            return alert
    
    def resolve_alert(self, alert_id: str) -> Optional[dict]:
        with self._lock:
            for alert in self.alerts:
                if alert["id"] == alert_id:
                    alert["resolved"] = True
                    alert["resolved_at"] = datetime.now().isoformat()
                    return alert
            return None
    
    def clear_resolved_alerts(self) -> int:
        with self._lock:
            before = len(self.alerts)
            self.alerts = [a for a in self.alerts if not a["resolved"]]
            return before - len(self.alerts)


# Global singleton instance - import this in MCP modules
state = SystemState()
