# openrouter.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY not found. Add it to your .env file.")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def call_model(model: str, messages, timeout: int = 30) -> str:
    """
    messages: list of dicts like [{"role":"user", "content":"..."}]
    returns the model's text output (first choice).
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    resp = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    # defensive access
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        # fallback: return whole JSON as string for debugging
        return str(data)
