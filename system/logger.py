"""
Thread-safe audit logger for the Mini Cloud Platform Simulator.
Appends JSON lines to audit.log with automatic timestamps.
"""

import json
import threading
from datetime import datetime
from pathlib import Path

# Lock for thread-safe file writes
_lock = threading.Lock()

# Log file path (same directory as main.py)
LOG_FILE = Path(__file__).parent.parent / "audit.log"


def log_event(event: dict) -> dict:
    """
    Log an event to audit.log as a JSON line.
    
    Args:
        event: Dictionary with event data (type, action, details, etc.)
    
    Returns:
        The logged event with timestamp added
    """
    # Add timestamp
    event["timestamp"] = datetime.now().isoformat()
    
    # Thread-safe write
    with _lock:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(event) + "\n")
    
    return event


def log_action(action: str, user: str = "system", **details) -> dict:
    """
    Convenience wrapper for logging actions.
    
    Args:
        action: Action name (e.g., "user.created", "service.stopped")
        user: User who performed the action
        **details: Additional key-value pairs
    
    Returns:
        The logged event
    """
    event = {
        "action": action,
        "user": user,
        **details,
    }
    return log_event(event)


def get_logs(limit: int = 100) -> list[dict]:
    """
    Read recent log entries.
    
    Args:
        limit: Maximum number of entries to return (most recent first)
    
    Returns:
        List of log entries
    """
    if not LOG_FILE.exists():
        return []
    
    with _lock:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
    
    # Parse JSON lines, most recent first
    logs = []
    for line in reversed(lines[-limit:]):
        try:
            logs.append(json.loads(line.strip()))
        except json.JSONDecodeError:
            continue
    
    return logs


def clear_logs() -> int:
    """
    Clear all logs. Returns count of deleted entries.
    """
    if not LOG_FILE.exists():
        return 0
    
    with _lock:
        with open(LOG_FILE, "r") as f:
            count = len(f.readlines())
        LOG_FILE.unlink()
    
    return count


# ============================================================
# Example Usage (run this file directly to test)
# ============================================================
if __name__ == "__main__":
    # Log some sample events
    log_action("user.login", user="alice", ip="192.168.1.100")
    log_action("service.started", user="root", service_id="auth")
    log_action("database.backup", user="system", db_id="prod_db", size_mb=512)
    
    log_event({
        "type": "alert",
        "severity": "high",
        "message": "CPU usage exceeded 90%",
        "resource_id": "vm_1",
    })
    
    # Read logs back
    print("Recent logs:")
    for entry in get_logs(limit=5):
        print(f"  {entry}")
