import logging
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.config import settings
from app.schemas.game_schemas import GameSession
from app.services.rag_service import rag_service
from app.services.dasha_calculator import get_current_dasha

logger = logging.getLogger(__name__)

# Initialize Gemini
try:
    llm_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
except Exception as e:
    logger.error(f"GenAI Client Error: {e}")

# --- 1. Schemas ---
class UIControl(BaseModel):
    highlight_houses: List[int] = Field(default=[])
    highlight_planets: List[str] = Field(default=[])
    transit_date: Optional[str] = Field(default=None)
    suggested_remedy: Optional[str] = Field(default=None)

class AstroResponse(BaseModel):
    speech: str = Field(description="Natural language response. No emojis. Professional tone.")
    ui: UIControl = Field(description="UI control metadata.")

# --- 2. Helpers ---
def _format_history(history):
    return "\n".join([f"{entry.role.upper()}: {entry.message}" for entry in history])

def _format_chart_human_readable(chart_data: dict) -> str:
    """
    Converts raw JSON into a prioritized list so the LLM sees HOUSES first.
    Format: "Planet Name: House X (Sign Y)"
    """
    try:
        lines = []
        # 1. Ascendant
        asc = chart_data.get('ascendant', {})
        lines.append(f"ASCENDANT (Lagna): House 1 ({asc.get('sign', 'Unknown')})")
        
        # 2. Planets
        planets = chart_data.get('planets', {})
        for name, data in planets.items():
            # Capitalize name (e.g. "sun" -> "Sun")
            p_name = name.title()
            house = data.get('house', '?')
            sign = data.get('sign', '?')
            lines.append(f"- {p_name}: Placed in HOUSE {house} ({sign})")
            
        return "\n".join(lines)
    except Exception:
        return str(chart_data)

def _get_dasha_context(chart_data: dict) -> str:
    try:
        moon_lon = chart_data.get('planets', {}).get('moon', {}).get('longitude', 0)
        dasha_info = get_current_dasha(moon_lon, "2000-01-01") 
        return f"Current Dasha Lord: {dasha_info.get('birth_dasha_lord')} (This planet is currently dictating the user's timeline)."
    except Exception:
        return "Dasha Context: Unknown"

# --- 3. Main Logic ---

def get_astro_response(session: GameSession) -> dict:
    try:
        user_query = session.conversation_history[-1].message if session.conversation_history else "General reading"
        
        # 1. RAG
        logger.info(f"🔍 Searching Texts for: {user_query}")
        retrieved_context = rag_service.get_relevant_context(user_query)
        
        # 2. Formatted Chart (House First)
        chart_summary = _format_chart_human_readable(session.chart_data)
        
        # 3. Time
        dasha_summary = _get_dasha_context(session.chart_data)

        # 4. The "Professional" Prompt
        prompt = f"""
        You are Acharya Gemini, a Vedic Astrologer. 
        You speak with the gravity of a sage, not a chatbot.

        ### 1. THE USER'S KUNDLI (DATA)
        {chart_summary}
        *NOTE: 'House 6' = Enemies/Service/Job. 'House 10' = Career/Status. 'House 12' = Loss/Foreign.*

        ### 2. TIMING (DASHA)
        {dasha_summary}

        ### 3. ANCIENT RULES (RAG)
        {retrieved_context}

        ### 4. HISTORY
        {_format_history(session.conversation_history)}

        ### 5. STRICT INSTRUCTIONS
        User Question: "{user_query}"
        ### INSTRUCTIONS
        User Question: "{user_query}"
        
        1. **Keep it Short:** You are on a Voice Call. Speak in **max 3-4 sentences**.
        2. **Be Direct:** No bullet points. No "Let's examine...". Just give the answer.
        3. **Structure:** [Observation] -> [Judgment] -> [Remedy].
        4. **Visuals:** Fill the UI fields (Houses/Planets/Remedy).
        
        **Tone:** Mystical, Empathetic, Concise.
        
        **Tone & Style:**
        - **NO EMOJIS.** Do not use 💊, ✨, or any icons.
        - **Speak in Terms of Houses (Bhavas):** Do not just say "Mercury in Sagittarius." Say "Mercury is sitting in your 12th House of Loss..."
        - **Be Diagnostic:** Explain the *logic*. Why is the job delayed? (e.g., "Because the Lord of your 10th house is weak...").
        - **Remedies:** If you suggest a remedy, explain *why* it works. (e.g., "This mantra strengthens Jupiter to remove the 12th house negativity").

        **Structure:**
        1. **Observation:** "I see [Planet] is in your [House Number]..."
        2. **Consequence:** "Since this is the house of [Meaning], it is causing..."
        3. **Remedy:** "To fix this, I suggest [Remedy]..."

        **Visuals:**
        - Fill `suggested_remedy` if applicable.
        - Add House numbers to `highlight_houses`.
        """

        # C. Call Gemini
        response = llm_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AstroResponse,
                temperature=0.6 
            )
        )
        
        # D. Parse
        if hasattr(response, 'parsed') and response.parsed:
             result = response.parsed
        else:
             clean_json = response.text.replace("```json", "").replace("```", "")
             result = AstroResponse.model_validate_json(clean_json)

        logger.info(f"🗣️ Acharya: {result.speech}")
        
        return result.model_dump()

    except Exception as e:
        logger.error(f"LLM Logic Error: {e}")
        return {
            "speech": "I am analyzing the planetary positions. Please allow me a moment to recalculate.",
            "ui": {"highlight_houses": [], "highlight_planets": []}
        }