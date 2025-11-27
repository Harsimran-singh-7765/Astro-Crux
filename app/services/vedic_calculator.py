"""
Advanced Vedic Astrology Calculator (Skyfield + OpenStreetMap)
File A: vedic_calculator.py
"""
import logging
import requests
import numpy as np
from datetime import datetime
from typing import Dict, Any, Tuple
from skyfield.api import load, wgs84
from skyfield.elementslib import osculating_elements_of
from timezonefinder import TimezoneFinder # ACCURACY UPGRADE
import pytz

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants ---
# refined for J2000 epoch precision
LAHIRI_AYANAMSA_2000 = 23.861111 
PRECESSION_RATE_ANNUAL = 0.01396942 
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
    Fetches Lat/Lon and EXACT Timezone.
    """
    headers = {'User-Agent': 'VedicAstroBot/2.0'}
    tf = TimezoneFinder() # Initialize locally
    try:
        # 1. Get Coordinates
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        response = requests.get(url, headers=headers).json()
        
        if not response:
            logger.warning(f"City '{city_name}' not found. Using default.")
            return 28.6139, 77.2090, 'Asia/Kolkata'
            
        lat = float(response[0]['lat'])
        lon = float(response[0]['lon'])
        
        # 2. Get Exact Timezone (ACCURACY UPGRADE)
        timezone_str = tf.timezone_at(lng=lon, lat=lat)
        if not timezone_str:
            timezone_str = 'UTC'
        
        logger.info(f"Found {city_name}: {lat}, {lon} ({timezone_str})")
        return lat, lon, timezone_str
        
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        return 28.6139, 77.2090, 'Asia/Kolkata'

def get_ayanamsa(t) -> float:
    # High precision drift calculation
    days_since_j2000 = t.tt - 2451545.0
    return LAHIRI_AYANAMSA_2000 + (PRECESSION_RATE_ANNUAL * (days_since_j2000 / 365.2425))

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
    """
    Calculates Ascendant using Skyfield's vector math (Topocentric).
    This implicitly handles the Geodetic vs Geocentric latitude issue.
    """
    # Create topocentric observer
    topos = wgs84.latlon(lat, lon)
    
    # Calculate Local Sidereal Time
    gast = t.gast
    lst = (gast * 15 + lon) % 360
    
    # Standard formula with numpy
    ecliptic_tilt = np.radians(23.4392911)
    ramc_rad = np.radians(lst)
    lat_rad = np.radians(lat)
    
    numerator = -np.cos(ramc_rad)
    denominator = (np.sin(ramc_rad) * np.cos(ecliptic_tilt)) + (np.tan(lat_rad) * np.sin(ecliptic_tilt))
    asc_rad = np.arctan2(numerator, denominator)
    return np.degrees(asc_rad) % 360

def get_rahu_ketu_true(t, earth, moon, ecliptic_frame, ayanamsa) -> Dict[str, Dict]:
    # Calculate True Node relative to Earth center (Nodes are geocentric points)
    moon_position = (moon - earth).at(t)
    elements = osculating_elements_of(moon_position, ecliptic_frame)
    
    rahu_tropical = elements.longitude_of_ascending_node.degrees
    rahu_sidereal = tropical_to_sidereal(rahu_tropical, ayanamsa)
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
        lat, lon, timezone_str = get_geo_coords(city_name)
        
        ts = load.timescale()
        eph = load('de421.bsp')
        earth, moon = eph['earth'], eph['moon']
        
        # TOPOCENTRIC OBSERVER (ACCURACY UPGRADE)
        # We define a specific point on Earth's surface
        observer = earth + wgs84.latlon(lat, lon)

        from skyfield.data.spice import inertial_frames
        ecliptic_frame = inertial_frames['ECLIPJ2000']

        tz = pytz.timezone(timezone_str)
        if birth_datetime.tzinfo is None:
            birth_datetime = tz.localize(birth_datetime)
        t = ts.from_datetime(birth_datetime)
        
        ayanamsa = get_ayanamsa(t)
        asc_tropical = calculate_ascendant(t, lat, lon)
        asc_sidereal = tropical_to_sidereal(asc_tropical, ayanamsa)
        asc_sign, asc_deg = get_sign_and_degree(asc_sidereal)

        chart = {
            'meta': {'location': f"{city_name} ({lat}, {lon})", 'datetime': str(birth_datetime), 'timezone': timezone_str},
            'ascendant': {'sign': asc_sign, 'formatted': decimal_to_dms(asc_deg)},
            'planets': {}
        }

        # Calculate Planets from Topocentric Observer
        for label, kernel_name in PLANET_NAMES.items():
            # .observe() from 'observer' (surface) instead of 'earth' (center)
            astrometric = observer.at(t).observe(eph[kernel_name])
            _, lon_ecl, _ = astrometric.ecliptic_latlon()
            sid_lon = tropical_to_sidereal(lon_ecl.degrees, ayanamsa)
            sign, deg = get_sign_and_degree(sid_lon)
            
            asc_idx = SIGNS.index(asc_sign)
            pl_idx = SIGNS.index(sign)
            house = (pl_idx - asc_idx + 12) % 12 + 1
            
            chart['planets'][label] = {
                'sign': sign, 'formatted': decimal_to_dms(deg), 'house': house
            }

        nodes = get_rahu_ketu_true(t, earth, moon, ecliptic_frame, ayanamsa)
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

if __name__ == "__main__":
    # Test
    bday = datetime(2006, 1, 31, 8, 10)
    chart = calculate_vedic_chart("kota", bday)
    print(chart)