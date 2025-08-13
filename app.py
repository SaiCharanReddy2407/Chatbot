from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

# FastAPI app
app = FastAPI(title="PowerApps ↔ Railway ↔ Groq Bridge", version="1.0.0")

# CORS - allow calls from Power Apps (you can restrict origins to your tenant domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str
    system: str | None = None
    model: str | None = "llama-3.1-70b-versatile"
    temperature: float | None = 0.2
    max_tokens: int | None = 512

class ChatResponse(BaseModel):
    text: str
    model: str
    usage: dict | None = None
    raw: dict | None = None

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Missing GROQ_API_KEY env var on server.")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = []
    if req.system:
        messages.append({"role": "system", "content": req.system})
    messages.append({"role": "user", "content": req.prompt})

    payload = {
        "model": req.model or "llama-3.1-70b-versatile",
        "messages": messages,
        "temperature": req.temperature if req.temperature is not None else 0.2,
        "max_tokens": req.max_tokens if req.max_tokens is not None else 512,
        "stream": False
    }

    # Groq uses an OpenAI-compatible endpoint path
    url = "https://api.groq.com/openai/v1/chat/completions"

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()

        # Extract assistant message
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            content = ""

        return {
            "text": content,
            "model": data.get("model", payload["model"]),
            "usage": data.get("usage"),
            "raw": data
        }
    except requests.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))