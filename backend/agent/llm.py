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
    # Remove markdown blocks if present
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)

    # Find the first { and the last }
    start = text.find('{')
    end = text.rfind('}')

    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in output")

    return text[start:end+1]

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
