import logging
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.config import settings
from app.schemas.game_schemas import GameSession
# Import the RAG service that holds BPHS
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

# Initialize Gemini
try:
    llm_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
except Exception as e:
    logger.error(f"GenAI Client Error: {e}")

# --- 1. Define Structured Output Schema (The Protocol) ---
class UIControl(BaseModel):
    """Hidden commands to control the frontend visuals."""
    highlight_houses: List[int] = Field(
        description="List of house numbers (1-12) to highlight based on the answer. E.g. [7, 1] for self & marriage.",
        default=[]
    )
    highlight_planets: List[str] = Field(
        description="List of planets mentioned in the answer. E.g. ['Sun', 'Saturn'].",
        default=[]
    )
    transit_date: Optional[str] = Field(
        description="YYYY-MM-DD date if discussing a future/past event (Time Travel). Use ONLY for predictions.",
        default=None
    )
    suggested_remedy: Optional[str] = Field(
        description="Name of a remedy/mantra if suggested. E.g., 'Surya Mantra' or 'Blue Sapphire'.",
        default=None
    )

class AstroResponse(BaseModel):
    """The strict output format for the Astrologer."""
    speech: str = Field(description="The natural language response to speak to the user. Keep it wise, mystical, but under 3 sentences.")
    ui: UIControl = Field(description="UI control metadata.")

# --- 2. Helper Functions ---

def _format_history(history):
    return "\n".join([f"{entry.role.upper()}: {entry.message}" for entry in history])

def _extract_chart_insights(chart_data: dict) -> str:
    """
    Flatten the complex chart JSON into a readable summary for the LLM.
    We convert the dictionary to a pretty-printed JSON string so Gemini reads it clearly.
    """
    try:
        # We assume chart_data is the structure returned by vedic_calculator
        return json.dumps(chart_data, indent=2, default=str)
    except Exception:
        return str(chart_data)

# --- 3. Main Logic ---

def get_astro_response(session: GameSession) -> dict:
    """
    Orchestrates: RAG (Book) + Math (Chart) -> Gemini -> JSON Output
    """
    try:
        # A. Context Preparation
        user_query = session.conversation_history[-1].message if session.conversation_history else "General reading"
        
        # 1. RAG: Search BPHS/Books for rules using HyDE logic
        logger.info(f"🔍 Searching Ancient Texts for: {user_query}")
        retrieved_context = rag_service.get_relevant_context(user_query)
        
        # 2. Chart: Get user's calculated math
        chart_summary = _extract_chart_insights(session.chart_data)

        # B. Prompt Engineering
        prompt = f"""
        You are Acharya Gemini, a Vedic Astrologer.
        
        USER'S KUNDLI (CALCULATED POSITIONS):
        {chart_summary}
        
        ANCIENT TEXTS (AUTHORITATIVE RULES FROM BPHS/SARAVALI):
        {retrieved_context}
        
        CONVERSATION HISTORY:
        {_format_history(session.conversation_history)}
        
        INSTRUCTIONS:
        1. **Analyze:** Compare the User's Chart with the Ancient Rules provided above.
        2. **Speak:** Answer the user's question. 
           - Be kind, mystical, and accurate.
           - Quote the text if applicable (e.g., "The ancient texts say...").
           - Do not be fatalistic; always offer guidance.
        3. **Visuals (UI Control):** - If you mention a specific House (e.g. 7th) or Planet (e.g. Sun), add it to `highlight_houses`/`highlight_planets`.
           - If you predict a specific future time, set `transit_date`.
           - If you suggest a fix, set `suggested_remedy`.
        
        User Question: {user_query}
        """

        # C. Call Gemini with JSON Mode
        response = llm_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AstroResponse,
                temperature=0.6 # Balanced for creativity + facts
            )
        )
        
        # D. Parse Response
        if hasattr(response, 'parsed') and response.parsed:
             result = response.parsed
        else:
             # Fallback manual parse if the SDK doesn't parse automatically
             clean_json = response.text.replace("```json", "").replace("```", "")
             result = AstroResponse.model_validate_json(clean_json)

        logger.info(f"🗣️ Acharya: {result.speech}")
        logger.info(f"🎨 UI Actions: {result.ui}")

        # Return dictionary for GameSessionManager
        return result.model_dump()

    except Exception as e:
        logger.error(f"LLM Logic Error: {e}")
        # Fail-safe response structure so the app doesn't crash
        return {
            "speech": "The cosmic frequencies are currently interrupted. Please ask me again.",
            "ui": {
                "highlight_houses": [], 
                "highlight_planets": [],
                "transit_date": None,
                "suggested_remedy": None
            }
        }