"""
Mini Cloud Platform Simulator - Main Application
A simple FastAPI-based cloud platform simulator for hackathon purposes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp import users, infra, data, alerts
from system import logger

app = FastAPI(
    title="Mini Cloud Platform Simulator",
    description="A lightweight cloud platform simulator with in-memory state",
    version="0.1.0",
)

# Enable CORS for easy frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(users.router)
app.include_router(infra.router)
app.include_router(data.router)
app.include_router(alerts.router)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Mini Cloud Platform Simulator"}


@app.get("/stats")
def stats():
    """Get platform statistics."""
    from system import state
    return {
        "users": len(state.users),
        "resources": len(state.infrastructure),
        "data_objects": len(state.data_store),
        "alerts": len(state.alerts),
        "unresolved_alerts": len([a for a in state.alerts.values() if not a["resolved"]]),
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Mini Cloud Platform Simulator")
    uvicorn.run(app, host="0.0.0.0", port=8000)
