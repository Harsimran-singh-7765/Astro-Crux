import logging
from datetime import datetime
import pytz
from skyfield.api import load, wgs84
from skyfield.framelib import ecliptic_frame
from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)

# 1. Initialize Geolocation
geolocator = Nominatim(user_agent="astro-crux-hackathon")

# 2. Load NASA Data (downloads de421.bsp once)
ts = load.timescale()
planets = load('de421.bsp')

class AstroEngine:
    """
    The Scientific Core (Skyfield Edition).
    Uses NASA JPL data to calculate planetary positions.
    Manually applies Lahiri Ayanamsa for Vedic Accuracy.
    """
    
    def __init__(self):
        self.zodiac_signs = [
            "Aries (Mesha)", "Taurus (Vrishabha)", "Gemini (Mithuna)", "Cancer (Karka)",
            "Leo (Simha)", "Virgo (Kanya)", "Libra (Tula)", "Scorpio (Vrishchika)",
            "Sagittarius (Dhanu)", "Capricorn (Makara)", "Aquarius (Kumbha)", "Pisces (Meena)"
        ]

    def _get_lahiri_ayanamsa(self, time_obj):
        """
        Calculates the approximate Lahiri Ayanamsa shift.
        Standard Ayanamsa for 2000 AD is ~23.85 degrees.
        Speed is approx 50.29 arcseconds per year.
        """
        # Get year as float
        year = time_obj.J
        # Simple formula for hackathon: 23.85 + (Year - 2000) * 0.0139
        shift = 23.85 + (year - 2000.0) * 0.01396
        return shift

    def get_coordinates(self, location_name: str):
        """Converts city name to lat/lon."""
        try:
            location = geolocator.geocode(location_name)
            if location:
                return location.latitude, location.longitude
            return None, None
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return 28.6139, 77.2090 # Default Delhi

    def generate_vedic_chart(self, date_str: str, time_str: str, location_str: str):
        """
        Generates a Vedic Chart using Skyfield (Tropical -> Sidereal).
        """
        # 1. Parse Time
        local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        # Assume IST for simplicity in hackathon (or convert using pytz)
        ist = pytz.timezone('Asia/Kolkata')
        local_dt = ist.localize(local_dt)
        
        # 2. Setup Skyfield Time and Observer
        t = ts.from_datetime(local_dt)
        lat, lon = self.get_coordinates(location_str)
        observer = wgs84.latlon(lat, lon)
        
        # 3. Calculate Ayanamsa
        ayanamsa = self._get_lahiri_ayanamsa(t)
        
        # 4. Calculate Positions
        earth = planets['earth']
        bodies = {
            'Sun': planets['sun'],
            'Moon': planets['moon'],
            'Mars': planets['mars'],
            'Mercury': planets['mercury'],
            'Jupiter': planets['jupiter_barycenter'],
            'Venus': planets['venus'],
            'Saturn': planets['saturn_barycenter']
        }
        
        vedic_data = {}
        
        for name, body in bodies.items():
            # Get astrometric position relative to earth
            astrometric = earth.at(t).observe(body)
            
            # Convert to Ecliptic Lat/Lon (Tropical Zodiac)
            lat, lon, distance = astrometric.frame_latlon(ecliptic_frame)
            tropical_deg = lon.degrees
            
            # Convert to Vedic (Sidereal)
            sidereal_deg = (tropical_deg - ayanamsa) % 360
            
            # Determine Sign
            sign_index = int(sidereal_deg // 30)
            degree_in_sign = sidereal_deg % 30
            sign_name = self.zodiac_signs[sign_index]
            
            vedic_data[name] = {
                "sign": sign_name,
                "degree": f"{degree_in_sign:.2f}",
                "full_degree": f"{sidereal_deg:.2f}"
            }

        return {
            "meta": {
                "location": location_str,
                "datetime": str(local_dt),
                "ayanamsa_used": f"{ayanamsa:.2f}"
            },
            "planets": vedic_data
        }

# Singleton
astro_engine = AstroEngine()