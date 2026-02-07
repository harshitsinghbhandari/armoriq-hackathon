import os
import re
import json
import ollama
import dotenv
from .prompts import SYSTEM_PROMPT

dotenv.load_dotenv()

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

def extract_json(text: str) -> str:
    """Extract first JSON object from model output."""
    text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in output")
    return match.group(0)

def generate_plan(prompt: str) -> dict:
    """
    Generates a plan using Ollama based on the input prompt.
    The input prompt is treated as the user message, combined with the system prompt.
    """
    try:
        response = ollama.chat(model=MODEL, messages=[
            {
                'role': 'system',
                'content': SYSTEM_PROMPT,
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        text = response['message']['content'].strip()
        clean_json = extract_json(text)
        return json.loads(clean_json)
    except Exception as e:
        print(f"❌ LLM Error (Ollama): {e}")
        return {"goal": "Error", "steps": [], "error": str(e)}
