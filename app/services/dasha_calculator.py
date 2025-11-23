import math

def get_current_dasha(moon_longitude: float, birth_date: str) -> dict:
    """
    Calculates the current Maha Dasha based on Moon's position.
    (Simplified Vimshottari Logic for Hackathon)
    """
    # 1. Nakshatra Constellations (13.33 degrees each)
    nakshatra_span = 13.333333
    nakshatra_idx = int(moon_longitude / nakshatra_span)
    
    # Degree into the nakshatra
    degree_into = moon_longitude % nakshatra_span
    percent_passed = degree_into / nakshatra_span
    
    # 2. Dasha Sequence (Fixed Order)
    # Each Nakshatra maps to a planet. This is a simplified mapping cycle.
    # Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
    dasha_order = [
        ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
        ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)
    ]
    
    # Find starting dasha based on nakshatra index (There are 27 nakshatras)
    # Cycle repeats every 9 nakshatras
    start_dasha_idx = nakshatra_idx % 9
    current_lord, duration = dasha_order[start_dasha_idx]
    
    # Calculate balance at birth
    balance_years = duration * (1 - percent_passed)
    
    # NOTE: For a full implementation, you need to add the user's age to this 
    # to find the *current* dasha. 
    # For Hackathon, just returning the "Birth Dasha" or "Nakshatra Lord" is often enough context 
    # to make the AI sound smart: "You were born under the influence of X..."
    
    return {
        "nakshatra_number": nakshatra_idx + 1,
        "birth_dasha_lord": current_lord,
        "balance_years": round(balance_years, 2)
    }