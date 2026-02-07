import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Header, status
from pydantic import BaseModel
from .llm import generate_plan
import dotenv

dotenv.load_dotenv()

app = FastAPI(title="ArmorIQ Agent Service")

AGENT_API_KEY = os.getenv("AGENT_API_KEY", "default-insecure-key")

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != AGENT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key

class RunRequest(BaseModel):
    input: str

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ArmorIQ Agent"}

@app.post("/run", dependencies=[Depends(verify_api_key)])
def run_agent(request: RunRequest):
    """
    Takes an input prompt and returns a generated plan using Ollama.
    """
    plan = generate_plan(request.input)
    return plan

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
