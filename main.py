"""
Mini Cloud Platform Simulator - Main Application
A simple FastAPI-based cloud platform simulator for hackathon purposes.
Refactored to only expose ArmorIQ-authorized endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from system import logger
from mcp import infra, alerts

app = FastAPI(
    title="Mini Cloud Platform Simulator",
    description="Refactored MCP with ArmorIQ Governance",
    version="0.2.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include only authorized routers
app.include_router(infra.router)
app.include_router(alerts.router)

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Mini Cloud Platform Simulator"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Mini Cloud Platform Simulator (ArmorIQ Mode)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
