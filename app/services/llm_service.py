import logging
import json
import re
from google import genai
from google.genai import types
from app.core.config import settings
from app.schemas.game_schemas import GameSession

logger = logging.getLogger(__name__)

try:
    llm_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
except Exception as e:
    logger.error(f"Error configuring GenAI client: {e}")

def _format_history(history):
    """Format conversation history for context"""
    return "\n".join([f"{entry.role.upper()}: {entry.message}" for entry in history])

def _extract_chart_insights(chart_data: dict) -> str:
    """
    Parse the chart data and extract key insights in natural language.
    This makes it easier for the LLM to reference specific placements.
    """
    insights = []
    
    # Extract planets
    if 'planets' in chart_data:
        planets = chart_data['planets']
        for planet, data in planets.items():
            sign = data.get('sign', 'Unknown')
            house = data.get('house', 'Unknown')
            degree = data.get('longitude', 0)
            
            insights.append(
                f"{planet} is in {sign} (House {house}) at {degree:.2f}° - "
                f"This placement influences {_get_planet_domain(planet)}"
            )
    
    # Extract houses
    if 'houses' in chart_data:
        houses = chart_data['houses']
        insights.append(f"\nAscendant (Lagna): {houses.get('1', {}).get('sign', 'Unknown')}")
    
    # Extract yogas or special combinations
    if 'aspects' in chart_data:
        insights.append("\nKey Planetary Aspects:")
        for aspect in chart_data.get('aspects', [])[:3]:  # Top 3 aspects
            insights.append(f"- {aspect}")
    
    return "\n".join(insights)

def _get_planet_domain(planet: str) -> str:
    """Return the domain each planet governs"""
    domains = {
        'Sun': 'self-identity, father, authority, vitality',
        'Moon': 'mind, emotions, mother, comfort',
        'Mars': 'energy, courage, conflicts, siblings',
        'Mercury': 'communication, intellect, trade',
        'Jupiter': 'wisdom, fortune, children, spirituality',
        'Venus': 'relationships, beauty, luxury, creativity',
        'Saturn': 'discipline, delays, karma, longevity',
        'Rahu': 'obsessions, foreign lands, unconventional paths',
        'Ketu': 'detachment, spirituality, past karma'
    }
    return domains.get(planet, 'life areas')

def _build_system_prompt(session: GameSession) -> str:
    """
    Construct the core system prompt that defines Acharya Gemini's persona
    and gives him access to the chart data in a structured way.
    """
    chart_insights = _extract_chart_insights(session.chart_data)
    name = session.chart_data.get('meta', {}).get('name', 'Seeker')
    
    system_prompt = f"""You are Acharya Gemini, a master Vedic Astrologer with 30 years of practice. You combine ancient Jyotish wisdom with precise astronomical calculations.

YOUR PERSONALITY:
- Warm, empathetic, and conversational (like a wise grandfather)
- Grounded in mathematics: You reference actual planetary positions
- Balance mysticism with practicality
- Speak naturally in short sentences (2-4 sentences max per response)
- Use phrases like "Your chart reveals...", "The planets suggest...", "Consider this..."
- Avoid fortune-telling or definitive predictions; instead offer insights and guidance

THE SEEKER'S BIRTH CHART (Sidereal/Lahiri Ayanamsa):
Name: {name}
Birth Details: {session.chart_data.get('meta', {}).get('date_time', 'Unknown')}
Location: {session.chart_data.get('meta', {}).get('location', 'Unknown')}

PLANETARY POSITIONS & INSIGHTS:
{chart_insights}

CORE RULES:
1. ALWAYS reference specific placements when answering ("Since your Mars is in Scorpio in the 3rd house...")
2. Connect planets to the question asked (Career → Jupiter, Saturn, 10th house; Relationships → Venus, 7th house)
3. If a question is unrelated to astrology, gently redirect: "Let's explore your chart instead..."
4. Keep responses conversational and voice-friendly (no bullet points or lists)
5. If uncertain about a placement, say "Let me examine that area of your chart more closely..."
6. Integrate Vedic concepts naturally: dashas (periods), yogas (combinations), aspects (drishti)

EXAMPLE GOOD RESPONSES:
❌ "Venus is in your 7th house" (too dry)
✅ "Your Venus sits in the 7th house of partnerships, suggesting you attract harmony through relationships, though Saturn's aspect may bring maturity slowly."

❌ "You will be successful" (fortune-telling)
✅ "With Jupiter in your 10th house, career growth comes through teaching or guiding others. The current dasha supports this."

CONVERSATION STYLE:
- Start with acknowledgment: "Ah, you're asking about..." 
- Middle: Reference 1-2 specific placements
- End: Offer actionable insight or a reflective question
- Length: 2-3 sentences maximum (this is voice chat!)

Remember: You are a guide, not a fortune-teller. Empower {name} to understand their cosmic blueprint."""
    
    return system_prompt

def get_astro_response(session: GameSession) -> str:
    """
    Generates a response based on the Vedic Chart + Conversation History.
    Enhanced with structured chart insights and persona prompt.
    """
    system_prompt = _build_system_prompt(session)
    conversation_history = _format_history(session.conversation_history)
    
    # Get the latest user message
    latest_question = ""
    if session.conversation_history:
        latest_question = session.conversation_history[-1].message
    
    # Construct the full prompt
    full_prompt = f"""{system_prompt}

CONVERSATION SO FAR:
{conversation_history}

CURRENT QUESTION: {latest_question}

Respond as Acharya Gemini in 2-3 natural sentences. Reference specific planetary positions from the chart above."""

    try:
        response = llm_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,  # Balance between creativity and consistency
                top_p=0.9,
                top_k=40,
                max_output_tokens=150,  # Force brevity for voice
            )
        )
        
        response_text = response.text.strip()
        
        # Safety check: If response is too long, truncate naturally
        sentences = response_text.split('. ')
        if len(sentences) > 3:
            response_text = '. '.join(sentences[:3]) + '.'
        
        return response_text
        
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return "The cosmic signals are unclear right now. Please ask me again."

def extract_focus_signal(response_text: str) -> str:
    """
    Extract the focus signal from the LLM response.
    Looks for patterns like [FOCUS:HOUSE_7] or [FOCUS:PLANET_MARS]
    
    Returns: Signal string (e.g., "HOUSE_7", "PLANET_MARS") or empty string if not found
    """
    match = re.search(r'\[FOCUS:([A-Z_0-9]+)\]', response_text)
    if match:
        signal = match.group(1)
        logger.info(f"[LLM] Focus signal extracted: {signal}")
        return signal
    return ""

def clean_response_text(response_text: str) -> str:
    """
    Remove focus signals from response text before sending to TTS.
    
    Returns: Cleaned response text without [FOCUS:...] tags
    """
    cleaned = re.sub(r'\[FOCUS:[A-Z_0-9]+\]\s*', '', response_text)
    return cleaned.strip()

def validate_chart_data(chart_data: dict) -> bool:
    """
    Validate that the chart data has the minimum required structure.
    Returns True if valid, False otherwise.
    """
    required_keys = ['planets', 'houses', 'meta']
    
    if not all(key in chart_data for key in required_keys):
        logger.error("Chart data missing required keys")
        return False
    
    if not chart_data['planets'] or len(chart_data['planets']) < 7:
        logger.error("Insufficient planetary data")
        return False
    
    return True