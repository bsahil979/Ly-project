"""Start script for the Smart Portfolio Advisor analytics engine.

All LLM configuration is read from environment variables.
Create a .env file from .env.example before running.

Required environment variables:
    LLM_API_KEY      - API key for the LLM provider
    LLM_MODEL        - Model name (e.g. gemini-1.5-flash, gpt-4o-mini)
    LLM_PROVIDER      - 'gemini' or 'openai'
"""
import os

os.environ.setdefault("LLM_API_KEY", os.environ.get("LLM_API_KEY", ""))
os.environ.setdefault("LLM_MODEL", os.environ.get("LLM_MODEL", "gpt-4o-mini"))
os.environ.setdefault("LLM_PROVIDER", os.environ.get("LLM_PROVIDER", "openai"))
os.environ.setdefault("LLM_MAX_TOKENS", os.environ.get("LLM_MAX_TOKENS", "1024"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000)
