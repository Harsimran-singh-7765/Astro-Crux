"""
Advanced Vedic Astrology Calculator (Skyfield + OpenStreetMap)
Features: Real-time Geocoding, True Node (Rahu/Ketu) Calculation, Precise Ascendant
"""
import logging
import requests
import numpy as np
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from skyfield.api import load, wgs84
from skyfield.elementslib import osculating_elements_of
from skyfield.data import hipparcos
import pytz

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants ---
LAHIRI_AYANAMSA_2000 = 23.855
PRECESSION_RATE = 0.01396
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANET_NAMES = {
    'Sun': 'sun', 'Moon': 'moon', 'Mars': 'mars', 'Mercury': 'mercury',
    'Jupiter': 'jupiter barycenter', 'Venus': 'venus', 'Saturn': 'saturn barycenter'
}

# --- Helper Functions ---

def get_geo_coords(city_name: str) -> Tuple[float, float, str]:
    """
    Fetches Lat/Lon and Timezone from OpenStreetMap (Nominatim).
    """
    headers = {'User-Agent': 'VedicAstroBot/1.0 (internal-test-project)'}
    try:
        # 1. Get Coordinates
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        response = requests.get(url, headers=headers).json()
        
        if not response:
            logger.warning(f"City '{city_name}' not found. Using default (Delhi).")
            return 28.6139, 77.2090, 'Asia/Kolkata'
            
        lat = float(response[0]['lat'])
        lon = float(response[0]['lon'])
        
        # 2. Get Timezone (using a simple mapping or default to India for this demo)
        # Note: A robust solution would use a timezone lookup lib like `timezonefinder`
        # For this hackathon scope, we default to 'Asia/Kolkata' if in India range, else UTC
        # You can add `pip install timezonefinder` for exact zones if needed.
        timezone_str = 'Asia/Kolkata' if 68 < lon < 98 and 8 < lat < 38 else 'UTC'
        
        logger.info(f"Found {city_name}: {lat}, {lon} ({timezone_str})")
        return lat, lon, timezone_str
        
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        return 28.6139, 77.2090, 'Asia/Kolkata' # Default fallback

def get_ayanamsa(t) -> float:
    days_since_j2000 = t.tt - 2451545.0
    return LAHIRI_AYANAMSA_2000 + (PRECESSION_RATE * (days_since_j2000 / 365.25))

def tropical_to_sidereal(deg: float, ayanamsa: float) -> float:
    return (deg - ayanamsa) % 360

def decimal_to_dms(deg: float) -> str:
    d = int(deg)
    m = int((deg - d) * 60)
    s = int(((deg - d) * 60 - m) * 60)
    return f"{d}° {m:02d}' {s:02d}\""

def get_sign_and_degree(longitude: float) -> Tuple[str, float]:
    sign_index = int(longitude / 30)
    return SIGNS[sign_index], longitude % 30

def calculate_ascendant(t, lat, lon):
    ecliptic_tilt = np.radians(23.4392911)
    gast = t.gast
    lst_deg = (gast * 15 + lon) % 360
    ramc_rad = np.radians(lst_deg)
    lat_rad = np.radians(lat)
    
    numerator = -np.cos(ramc_rad)
    denominator = (np.sin(ramc_rad) * np.cos(ecliptic_tilt)) + (np.tan(lat_rad) * np.sin(ecliptic_tilt))
    asc_rad = np.arctan2(numerator, denominator)
    return np.degrees(asc_rad) % 360

def get_rahu_ketu_true(t, earth, moon, ecliptic_frame, ayanamsa) -> Dict[str, Dict]:
    """
    Calculates True Node (Rahu) using Skyfield's Osculating Elements.
    """
    # 1. Get Moon's position relative to Earth
    moon_position = (moon - earth).at(t)
    
    # 2. Get Orbital Elements relative to the Ecliptic
    elements = osculating_elements_of(moon_position, ecliptic_frame)
    
    # 3. Extract Longitude of Ascending Node (Rahu)
    rahu_tropical = elements.longitude_of_ascending_node.degrees
    rahu_sidereal = tropical_to_sidereal(rahu_tropical, ayanamsa)
    
    # 4. Ketu is exactly opposite (180 degrees away)
    ketu_sidereal = (rahu_sidereal + 180) % 360
    
    rahu_sign, rahu_deg = get_sign_and_degree(rahu_sidereal)
    ketu_sign, ketu_deg = get_sign_and_degree(ketu_sidereal)
    
    return {
        'Rahu': {'longitude': rahu_sidereal, 'sign': rahu_sign, 'degree': rahu_deg, 'formatted': decimal_to_dms(rahu_deg)},
        'Ketu': {'longitude': ketu_sidereal, 'sign': ketu_sign, 'degree': ketu_deg, 'formatted': decimal_to_dms(ketu_deg)}
    }

# --- Main Calculation ---

def calculate_vedic_chart(city_name: str, birth_datetime: datetime) -> Dict[str, Any]:
    try:
        # 1. Dynamic Location Lookup
        lat, lon, timezone_str = get_geo_coords(city_name)
        
        # 2. Initialize Skyfield
        ts = load.timescale()
        eph = load('de421.bsp')
        earth, moon = eph['earth'], eph['moon']
        
        # Load Ecliptic Frame for Node Calculation
        from skyfield.data.spice import inertial_frames
        ecliptic_frame = inertial_frames['ECLIPJ2000']

        # 3. Time Handling
        tz = pytz.timezone(timezone_str)
        if birth_datetime.tzinfo is None:
            birth_datetime = tz.localize(birth_datetime)
        t = ts.from_datetime(birth_datetime)
        
        # 4. Ayanamsa & Ascendant
        ayanamsa = get_ayanamsa(t)
        asc_tropical = calculate_ascendant(t, lat, lon)
        asc_sidereal = tropical_to_sidereal(asc_tropical, ayanamsa)
        asc_sign, asc_deg = get_sign_and_degree(asc_sidereal)

        chart = {
            'meta': {'location': f"{city_name} ({lat}, {lon})", 'datetime': str(birth_datetime)},
            'ascendant': {'sign': asc_sign, 'formatted': decimal_to_dms(asc_deg)},
            'planets': {}
        }

        # 5. Calculate 7 Major Planets
        for label, kernel_name in PLANET_NAMES.items():
            astrometric = earth.at(t).observe(eph[kernel_name])
            _, lon_ecl, _ = astrometric.ecliptic_latlon()
            sid_lon = tropical_to_sidereal(lon_ecl.degrees, ayanamsa)
            sign, deg = get_sign_and_degree(sid_lon)
            
            # House Calculation (Whole Sign)
            asc_idx = SIGNS.index(asc_sign)
            pl_idx = SIGNS.index(sign)
            house = (pl_idx - asc_idx + 12) % 12 + 1
            
            chart['planets'][label] = {
                'sign': sign, 'formatted': decimal_to_dms(deg), 'house': house
            }

        # 6. Calculate Rahu & Ketu (True Node)
        nodes = get_rahu_ketu_true(t, earth, moon, ecliptic_frame, ayanamsa)
        
        # Add Nodes to chart with House logic
        for node_name, data in nodes.items():
            node_idx = SIGNS.index(data['sign'])
            house = (node_idx - asc_idx + 12) % 12 + 1
            chart['planets'][node_name] = {
                'sign': data['sign'], 
                'formatted': data['formatted'], 
                'house': house
            }

        return chart

    except Exception as e:
        logger.error(f"Calculation Error: {e}")
        return {"error": str(e)}

# --- Usage ---
if __name__ == "__main__":
    # Example: Dynamic lookup for Mumbai
    bday = datetime(2003, 11, 20, 10, 30) # Year, Month, Day, Hour, Minute
    chart = calculate_vedic_chart("Mumbai", bday)
    
    print(f"\n--- Kundali for {chart['meta']['location']} ---")
    print(f"Ascendant (Lagna): {chart['ascendant']['sign']} {chart['ascendant']['formatted']}")
    print("-" * 45)
    print(f"{'Planet':<10} | {'Sign':<12} | {'Degree':<12} | {'House':<5}")
    print("-" * 45)
    for p, d in chart['planets'].items():
        print(f"{p:<10} | {d['sign']:<12} | {d['formatted']:<12} | {d['house']:<5}")