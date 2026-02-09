from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
import json
from typing import Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AroMi AI Agent Backend", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[list] = None

class ChatResponse(BaseModel):
    reply: str
    data: dict

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY environment variable not set")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.3-70b-versatile"

# System prompt to enforce JSON response format
SYSTEM_PROMPT = """You are AroMi, a health and wellness AI assistant. Your task is to analyze user messages about their health and wellness and respond in a specific JSON format.

RULES:
1. ALWAYS respond with VALID JSON only - no other text, no markdown
2. Extract health/wellness metrics from user's message
3. For missing information, use empty string ""
4. Keep conversational replies friendly, motivational, and supportive
5. Never provide medical diagnosis - encourage professional consultation

RESPONSE FORMAT (JSON only):
{
  "reply": "Your friendly conversational reply here",
  "data": {
    "goal": "e.g., 'Weight management' or 'Better sleep'",
    "diet": "e.g., 'Balanced' or 'Needs improvement'",
    "time": "e.g., 'Morning person' or 'Night owl'",
    "energy": "e.g., 'High', 'Medium', 'Low'",
    "consistency": "e.g., 'Regular', 'Intermittent', 'Starting'",
    "insights": "One actionable insight based on conversation"
  }
}

EXAMPLES:
User: "I slept for 7 hours last night and ate a healthy breakfast"
Response: {"reply": "Great job on the 7 hours of sleep and healthy breakfast! Consistency with sleep and nutrition is key for energy levels throughout the day.", "data": {"goal": "", "diet": "Healthy", "time": "Morning routine", "energy": "Medium", "consistency": "Regular", "insights": "Maintain consistent sleep schedule"}}

User: "I want to lose 5kg in the next month"
Response: {"reply": "That's an achievable goal! Remember that sustainable weight loss is about 0.5-1kg per week. Let's focus on balanced nutrition and regular exercise.", "data": {"goal": "Lose 5kg", "diet": "Needs planning", "time": "", "energy": "", "consistency": "Starting", "insights": "Combine cardio and strength training 3-4x weekly"}}

User: "I feel tired all the time"
Response: {"reply": "I'm sorry to hear you're feeling tired. Let's explore some factors - how's your sleep quality, hydration, and stress levels been recently?", "data": {"goal": "Increase energy", "diet": "", "time": "", "energy": "Low", "consistency": "", "insights": "Review sleep patterns and hydration"}}

IMPORTANT: Response must be parseable JSON. No extra text before or after."""

@app.get("/")
async def root():
    return {"status": "healthy", "service": "AroMi AI Agent Backend"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
@app.post("/chat")
def chat(req: ChatRequest):
    if not GROQ_API_KEY:
        return {
            "reply": "AI service is not configured yet.",
            "data": {}
        }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": req.message},
                ],
                "temperature": 0.6,
                "max_tokens": 500,
            },
            timeout=20
        )

        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)

    except Exception as e:
        return {
            "reply": "Something went wrong, please try again.",
            "data": {},
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)