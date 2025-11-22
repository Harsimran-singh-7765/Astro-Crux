"""
Enhanced Vedic Astrology Calculator using Skyfield
Calculates Sidereal positions with Lahiri Ayanamsa
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from skyfield.api import load, wgs84
import pytz

logger = logging.getLogger(__name__)

# Lahiri Ayanamsa (as of 2000-01-01)
LAHIRI_AYANAMSA_2000 = 23.85
PRECESSION_RATE = 0.0138889 

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

HOUSE_MEANINGS = {
    1: "Self & Personality",
    2: "Wealth & Resources",
    3: "Communication & Siblings",
    4: "Home & Family",
    5: "Creativity & Children",
    6: "Health & Service",
    7: "Relationships & Marriage",
    8: "Longevity & Transformation",
    9: "Fortune & Spirituality",
    10: "Career & Public Image",
    11: "Gains & Friendships",
    12: "Losses & Spirituality"
}

PLANET_NAMES = {
    'sun': 'Sun', 'moon': 'Moon', 'mercury': 'Mercury', 'venus': 'Venus',
    'mars': 'Mars', 'jupiter': 'Jupiter barycenter', 'saturn': 'Saturn barycenter',
}

def calculate_ayanamsa(year: float) -> float:
    """
    Calculate Lahiri Ayanamsa for a given year.
    Based on the precession of equinoxes.
    """
    # At Jan 1, 2000 (J2000.0): Lahiri Ayanamsa = 23.8530°
    # Precession rate = 50.2885" per year ≈ 0.0139° per year
    years_since_2000 = year - 2000.0
    ayanamsa = LAHIRI_AYANAMSA_2000 + (PRECESSION_RATE * years_since_2000)
    return ayanamsa

def tropical_to_sidereal(tropical_longitude: float, ayanamsa: float) -> float:
    sidereal = tropical_longitude - ayanamsa
    return sidereal % 360

def longitude_to_sign(longitude: float) -> Tuple[str, float]:
    sign_index = int(longitude / 30)
    degree_in_sign = longitude % 30
    return SIGNS[sign_index], degree_in_sign

def calculate_house_cusps(asc_longitude: float) -> Dict[str, Dict]:
    # Equal House System
    houses = {}
    for i in range(1, 13):
        cusp_longitude = (asc_longitude + (i - 1) * 30) % 360
        sign, degree = longitude_to_sign(cusp_longitude)
        houses[str(i)] = {'sign': sign, 'longitude': cusp_longitude}
    return houses

def get_house_for_planet(planet_longitude: float, asc_longitude: float) -> int:
    relative_position = (planet_longitude - asc_longitude) % 360
    house_number = int(relative_position / 30) + 1
    return house_number if house_number <= 12 else 1

def calculate_vedic_chart(birth_datetime: datetime, latitude: float, longitude: float, timezone_str: str = 'UTC') -> Dict[str, Any]:
    try:
        ts = load.timescale()
        eph = load('de421.bsp')
        
        # Handle timezone
        tz = pytz.timezone(timezone_str)
        if birth_datetime.tzinfo is None:
            birth_datetime = tz.localize(birth_datetime)
        
        t = ts.from_datetime(birth_datetime)
        location = wgs84.latlon(latitude, longitude)
        
        # Calculate ayanamsa
        year = birth_datetime.year + (birth_datetime.month / 12.0)
        ayanamsa = calculate_ayanamsa(year)
        
        logger.info(f"[Calc] Birth: {birth_datetime}, Lat: {latitude}, Lon: {longitude}")
        logger.info(f"[Calc] Ayanamsa: {ayanamsa:.2f}°, Year: {year:.2f}")
        
        # Calculate all planets
        planets = {}
        earth = eph['earth']
        
        for key, planet_name in PLANET_NAMES.items():
            planet = eph[planet_name]
            astrometric = earth.at(t).observe(planet)
            lat, lon, distance = astrometric.ecliptic_latlon()
            
            tropical_lon = lon.degrees
            sidereal_lon = tropical_to_sidereal(tropical_lon, ayanamsa)
            sign, degree = longitude_to_sign(sidereal_lon)
            
            planets[key] = {
                'longitude': sidereal_lon,
                'sign': sign,
                'degree': degree,
            }
            logger.info(f"[Calc] {key}: {sign} {degree:.2f}° (sidereal: {sidereal_lon:.2f}°)")
        
        # Calculate Ascendant properly using observer location
        astrometric = earth.at(t).observe(eph['sun'])
        sun_lat, sun_lon, sun_dist = astrometric.ecliptic_latlon()
        
        # Get local sidereal time (GAST at observer's location)
        # GAST = Greenwich Apparent Sidereal Time
        gast = t.gast  # Hours
        
        # Local Sidereal Time = GAST + (longitude in hours)
        lst_hours = (gast + longitude / 15.0) % 24
        lst_degrees = lst_hours * 15  # Convert hours to degrees
        
        logger.info(f"[Calc] GAST: {gast:.4f}h, LST: {lst_hours:.4f}h ({lst_degrees:.2f}°)")
        
        # Tropical ascendant is the LST
        asc_tropical = lst_degrees % 360
        asc_sidereal = tropical_to_sidereal(asc_tropical, ayanamsa)
        asc_sign, asc_degree = longitude_to_sign(asc_sidereal)
        
        logger.info(f"[Calc] Ascendant (Tropical): {asc_tropical:.2f}°, (Sidereal): {asc_sidereal:.2f}° = {asc_sign} {asc_degree:.2f}°")
        
        # Calculate houses
        houses = calculate_house_cusps(asc_sidereal)
        
        # Assign planets to houses
        for p in planets.values():
            p['house'] = get_house_for_planet(p['longitude'], asc_sidereal)
        
        logger.info(f"[Calc] ✅ Chart calculated successfully")
        
        return {
            'meta': {'date': str(birth_datetime), 'ayanamsa': ayanamsa},
            'planets': planets,
            'houses': houses,
            'ascendant': {'sign': asc_sign, 'longitude': asc_sidereal, 'degree': asc_degree}
        }
    except Exception as e:
        logger.error(f"[Calc] ❌ Error calculating chart: {e}", exc_info=True)
        raise e

def get_location_coordinates(city: str) -> Tuple[float, float, str]:
    # Simple lookup for Hackathon
    cities = {
        'delhi': (28.6139, 77.2090, 'Asia/Kolkata'),
        'mumbai': (19.0760, 72.8777, 'Asia/Kolkata'),
        'bangalore': (12.9716, 77.5946, 'Asia/Kolkata'),
        'london': (51.5074, -0.1278, 'Europe/London'),
        'new york': (40.7128, -74.0060, 'America/New_York'),
    }
    return cities.get(city.lower(), (28.6139, 77.2090, 'Asia/Kolkata'))