"""
Kundli Comparerer Service
Compares two birth charts and generates compatibility analysis.
"""

import logging
import json
from typing import List, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from app.core.config import settings
from app.services.rag_service import rag_service
from app.services.vedic_calculator import calculate_vedic_chart

logger = logging.getLogger(__name__)

# Initialize Gemini
try:
    llm_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
except Exception as e:
    logger.error(f"GenAI Client Error: {e}")

# --- Structured Output Schema ---
class CompatibilityScore(BaseModel):
    """Compatibility metrics between two charts."""
    overall: float = Field(description="Overall compatibility 0-100", ge=0, le=100)
    emotional: float = Field(description="Emotional compatibility 0-100", ge=0, le=100)
    intellectual: float = Field(description="Intellectual compatibility 0-100", ge=0, le=100)
    financial: float = Field(description="Financial compatibility 0-100", ge=0, le=100)
    physical: float = Field(description="Physical compatibility 0-100", ge=0, le=100)

class ComparisonUIControl(BaseModel):
    """UI metadata for comparison visualization."""
    chart1_highlights: List[int] = Field(description="Houses to highlight in first chart", default=[])
    chart2_highlights: List[int] = Field(description="Houses to highlight in second chart", default=[])
    synastry_aspects: List[str] = Field(description="Key aspects between charts", default=[])

class ComparisonResponse(BaseModel):
    """The structured output for Kundli comparison."""
    summary: str = Field(description="Executive summary of compatibility")
    emotional_analysis: str = Field(description="Analysis of emotional compatibility")
    intellectual_analysis: str = Field(description="Analysis of intellectual compatibility")
    financial_analysis: str = Field(description="Analysis of financial compatibility")
    physical_analysis: str = Field(description="Analysis of physical/sensual compatibility")
    challenges: str = Field(description="Key challenges in the relationship")
    strengths: str = Field(description="Key strengths in the relationship")
    recommendations: str = Field(description="Remedies and recommendations")
    scores: CompatibilityScore = Field(description="Numerical compatibility scores")
    ui: ComparisonUIControl = Field(description="UI control metadata")

# --- Helper Functions ---

def _extract_chart_for_comparison(chart_data: dict, name: str) -> str:
    """Extract key information from chart for comparison context."""
    try:
        sun_sign = chart_data.get('planets', {}).get('sun', {}).get('sign', 'Unknown')
        moon_sign = chart_data.get('planets', {}).get('moon', {}).get('sign', 'Unknown')
        asc_sign = chart_data.get('ascendant', {}).get('sign', 'Unknown')
        
        planets = chart_data.get('planets', {})
        
        summary = f"""
NAME: {name}
Ascendant: {asc_sign}
Sun Sign: {sun_sign}
Moon Sign: {moon_sign}

PLANETS IN HOUSES:
"""
        for planet, data in planets.items():
            house = data.get('house', 'N/A')
            sign = data.get('sign', 'N/A')
            summary += f"- {planet.capitalize()}: {house} House in {sign}\n"
        
        return summary
    except Exception as e:
        logger.error(f"Error extracting chart: {e}")
        return json.dumps(chart_data)

def _calculate_gunas_matching(chart1: dict, chart2: dict) -> dict:
    """
    Calculate the 8 Gunas (Ashta Kuta) matching score.
    Total possible: 36 points
    """
    moon1_sign = chart1.get('planets', {}).get('moon', {}).get('sign', '')
    moon2_sign = chart2.get('planets', {}).get('moon', {}).get('sign', '')
    
    # Simplified guna calculation (full implementation would be more complex)
    # This is a placeholder that returns basic structure
    return {
        "varna": 3,      # Caste - max 1
        "vashya": 2,     # Nature control - max 2
        "tara": 3,       # Star constellation - max 3
        "yoni": 4,       # Physical attraction - max 4
        "graha_maitri": 5,  # Planetary friendship - max 5
        "bhuta": 4,      # Element - max 5
        "nadi": 8,       # Pulse/Health - max 8
        "rashyadhipati": 2,  # Lord of the sign - max 2
        "total": 31,
        "max_possible": 36
    }

def get_kundli_comparison(chart1: dict, chart2: dict, name1: str, name2: str) -> dict:
    """
    Main function to generate kundli comparison analysis.
    
    Args:
        chart1: First birth chart (dict)
        chart2: Second birth chart (dict)
        name1: First person's name
        name2: Second person's name
    
    Returns:
        Structured comparison response (dict)
    """
    try:
        logger.info(f"🔍 Comparing charts: {name1} vs {name2}")
        
        # A. Extract Chart Information
        chart1_summary = _extract_chart_for_comparison(chart1, name1)
        chart2_summary = _extract_chart_for_comparison(chart2, name2)
        
        # B. Calculate Gunas Matching
        gunas = _calculate_gunas_matching(chart1, chart2)
        
        # C. RAG: Retrieve compatibility knowledge
        query = f"Compatibility between {chart1.get('planets', {}).get('sun', {}).get('sign')} and {chart2.get('planets', {}).get('sun', {}).get('sign')}"
        retrieved_context = rag_service.get_relevant_context(query)
        
        # D. Build Prompt
        prompt = f"""
You are Acharya Gemini, an expert Vedic astrologer specializing in Relationship Analysis.
Your task is to compare two birth charts and provide a comprehensive compatibility analysis.

### PERSON 1 (Chart 1)
{chart1_summary}

### PERSON 2 (Chart 2)
{chart2_summary}

### GUNAS MATCHING (Ashta Kuta)
Total Score: {gunas['total']}/36 points
- Varna (Caste): {gunas['varna']}/1
- Vashya (Nature Control): {gunas['vashya']}/2
- Tara (Star): {gunas['tara']}/3
- Yoni (Physical Attraction): {gunas['yoni']}/4
- Graha Maitri (Planetary Friendship): {gunas['graha_maitri']}/5
- Bhuta (Element): {gunas['bhuta']}/5
- Nadi (Health): {gunas['nadi']}/8
- Rashyadhipati (Sign Lord): {gunas['rashyadhipati']}/2

### VEDIC KNOWLEDGE BASE
{retrieved_context}

### ANALYSIS INSTRUCTIONS
1. **Summary**: Provide a brief 2-3 sentence overview of their cosmic compatibility
2. **Emotional Compatibility**: How well do their emotional natures align? (Analyze Moon signs)
3. **Intellectual Compatibility**: Do their minds work in harmony? (Analyze Mercury positions)
4. **Financial Compatibility**: Will they prosper together? (Analyze Jupiter & 2nd/10th houses)
5. **Physical Compatibility**: Is there natural attraction? (Analyze Venus/Mars positions)
6. **Challenges**: What are the main friction points? (Analyze aspects, Saturn placements)
7. **Strengths**: What makes this pairing strong? (Analyze benefic aspects, trines)
8. **Recommendations**: What remedies/practices would strengthen the bond?

**Response Style:**
- Be direct and honest. Not all combinations are perfect, and that's normal.
- Provide actionable insights, not just poetic descriptions.
- Ground analysis in Vedic principles (dashas, aspects, element harmony).
- Keep it mystical but practical.

**Scoring Guidelines:**
- Overall: Weighted average of all dimensions (use gunas score as baseline)
- 85-100: Exceptionally compatible - destiny seems aligned
- 70-84: Very good - strong foundation with minor adjustments needed
- 55-69: Moderate - requires effort but deeply rewarding
- 40-54: Challenging - significant work needed but not impossible
- Below 40: Extremely difficult - suggests careful consideration
"""

        # E. Call Gemini with JSON Mode
        response = llm_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ComparisonResponse,
                temperature=0.8  # Slightly creative for nuanced analysis
            )
        )
        
        # F. Parse Response
        if hasattr(response, 'parsed') and response.parsed:
            result = response.parsed
        else:
            clean_json = response.text.replace("```json", "").replace("```", "")
            result = ComparisonResponse.model_validate_json(clean_json)

        logger.info(f"✅ Comparison complete - Overall score: {result.scores.overall}")
        
        return result.model_dump()

    except Exception as e:
        logger.error(f"Comparison Error: {e}", exc_info=True)
        return {
            "summary": "The stars appear clouded. Let me focus again.",
            "emotional_analysis": "Unable to calculate",
            "intellectual_analysis": "Unable to calculate",
            "financial_analysis": "Unable to calculate",
            "physical_analysis": "Unable to calculate",
            "challenges": "Unable to calculate",
            "strengths": "Unable to calculate",
            "recommendations": "Please try again",
            "scores": {
                "overall": 0,
                "emotional": 0,
                "intellectual": 0,
                "financial": 0,
                "physical": 0
            },
            "ui": {
                "chart1_highlights": [],
                "chart2_highlights": [],
                "synastry_aspects": []
            }
        }
