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

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Process chat messages and get AI response with wellness metrics
    """
    try:
        # Check API key
        if not GROQ_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="Groq API key not configured. Please set GROQ_API_KEY environment variable."
            )
        
        # Prepare messages for Groq API
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request.message}
        ]
        
        # Add conversation history if provided
        if request.conversation_history:
            # Add only last 5 messages to avoid token limits
            for msg in request.conversation_history[-5:]:
                messages.insert(-1, msg)
        
        # Prepare request payload
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500,
            "response_format": {"type": "json_object"}
        }
        
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Call Groq API
        logger.info(f"Sending request to Groq API with model: {MODEL_NAME}")
        response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Groq API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Groq API error: {response.text}"
            )
        
        # Parse response
        result = response.json()
        ai_response_content = result["choices"][0]["message"]["content"]
        
        # Parse JSON from AI response
        try:
            parsed_response = json.loads(ai_response_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {ai_response_content}")
            # Fallback response
            parsed_response = {
                "reply": "I understand your message about health and wellness. Let me help you track your progress!",
                "data": {
                    "goal": "",
                    "diet": "",
                    "time": "",
                    "energy": "",
                    "consistency": "",
                    "insights": "Start tracking daily habits for better insights"
                }
            }
        
        # Validate response structure
        if "reply" not in parsed_response or "data" not in parsed_response:
            logger.error(f"Invalid response structure: {parsed_response}")
            raise HTTPException(
                status_code=500,
                detail="AI returned invalid response format"
            )
        
        # Ensure all data fields exist
        required_fields = ["goal", "diet", "time", "energy", "consistency", "insights"]
        for field in required_fields:
            if field not in parsed_response["data"]:
                parsed_response["data"][field] = ""
        
        logger.info(f"Successfully processed chat request: {request.message[:50]}...")
        
        return ChatResponse(
            reply=parsed_response["reply"],
            data=parsed_response["data"]
        )
        
    except requests.exceptions.Timeout:
        logger.error("Groq API request timed out")
        raise HTTPException(status_code=504, detail="AI service timeout")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {str(e)}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)