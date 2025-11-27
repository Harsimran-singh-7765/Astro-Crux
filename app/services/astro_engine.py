"""
astroengine.py
Enhanced Vedic Astrology Engine
Features: True Node Calculation (Rahu/Ketu), Trigonometric Ascendant, & OpenStreetMap Geocoding
"""
import logging
import requests
import numpy as np
import pytz
from datetime import datetime
from skyfield.api import load, wgs84
from skyfield.elementslib import osculating_elements_of
from skyfield.data import hipparcos

logger = logging.getLogger(__name__)

# --- Load Static NASA Data Once (Module Level) ---
ts = load.timescale()
eph = load('de421.bsp')
earth = eph['earth']
moon = eph['moon']

class AstroEngine:
    """
    The Scientific Core (Skyfield + NumPy Edition).
    Calculates precise Vedic positions including Ascendant and True Nodes.
    """
    
    def __init__(self):
        self.SIGNS = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        
        self.PLANET_MAPPING = {
            'Sun': eph['sun'],
            'Moon': eph['moon'],
            'Mars': eph['mars'],
            'Mercury': eph['mercury'],
            'Jupiter': eph['jupiter barycenter'],
            'Venus': eph['venus'],
            'Saturn': eph['saturn barycenter']
        }

        # Lahiri Ayanamsa Constants (J2000)
        self.LAHIRI_2000 = 23.855
        self.PRECESSION_RATE = 0.01396

    def _get_geo_coords(self, city_name: str):
        """
        Fetches Lat/Lon/Timezone from OpenStreetMap (Nominatim) using Requests.
        """
        headers = {'User-Agent': 'VedicAstroBot/1.0'}
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
            response = requests.get(url, headers=headers).json()
            
            if not response:
                logger.warning(f"Location '{city_name}' not found. Defaulting to Delhi.")
                return 28.6139, 77.2090, 'Asia/Kolkata'
            
            lat = float(response[0]['lat'])
            lon = float(response[0]['lon'])
            
            # Simple timezone approximation logic
            # (In production, use the `timezonefinder` library here)
            timezone_str = 'Asia/Kolkata' if 68 < lon < 98 and 8 < lat < 38 else 'UTC'
            
            return lat, lon, timezone_str
            
        except Exception as e:
            logger.error(f"Geocoding API Error: {e}")
            return 28.6139, 77.2090, 'Asia/Kolkata' # Default Fallback

    def _calculate_ayanamsa(self, t):
        """Calculates Lahiri Ayanamsa for the given time."""
        days_since_j2000 = t.tt - 2451545.0
        return self.LAHIRI_2000 + (self.PRECESSION_RATE * (days_since_j2000 / 365.25))

    def _tropical_to_sidereal(self, deg, ayanamsa):
        return (deg - ayanamsa) % 360

    def _get_sign_data(self, longitude):
        """Returns structured dictionary for a given longitude."""
        idx = int(longitude / 30)
        degree_in_sign = longitude % 30
        
        d = int(degree_in_sign)
        m = int((degree_in_sign - d) * 60)
        s = int(((degree_in_sign - d) * 60 - m) * 60)
        
        return {
            "sign": self.SIGNS[idx],
            "degree": degree_in_sign,
            "dms": f"{d}° {m}' {s}\"",
            "full_degree": longitude
        }

    def _calculate_ascendant(self, t, lat, lon):
        """
        Calculates the accurate Ascendant (Lagna) using Trigonometry.
        """
        # 1. Calculate RAMC (Right Ascension of the Meridian)
        gast = t.gast
        lst_deg = (gast * 15 + lon) % 360
        ramc_rad = np.radians(lst_deg)
        
        # 2. Obliquity of Ecliptic & Latitude
        ecliptic_tilt = np.radians(23.4392911)
        lat_rad = np.radians(lat)
        
        # 3. Arctan Formula
        numerator = -np.cos(ramc_rad)
        denominator = (np.sin(ramc_rad) * np.cos(ecliptic_tilt)) + (np.tan(lat_rad) * np.sin(ecliptic_tilt))
        
        asc_rad = np.arctan2(numerator, denominator)
        asc_deg = np.degrees(asc_rad) % 360
        return asc_deg

    def _get_rahu_ketu(self, t, ayanamsa):
        """
        Calculates True Nodes using Moon's osculating elements.
        """
        from skyfield.data.spice import inertial_frames
        ecliptic_frame = inertial_frames['ECLIPJ2000']
        
        moon_pos = (moon - earth).at(t)
        elements = osculating_elements_of(moon_pos, ecliptic_frame)
        
        rahu_trop = elements.longitude_of_ascending_node.degrees
        rahu_sid = self._tropical_to_sidereal(rahu_trop, ayanamsa)
        ketu_sid = (rahu_sid + 180) % 360
        
        return {
            'Rahu': self._get_sign_data(rahu_sid),
            'Ketu': self._get_sign_data(ketu_sid)
        }

    def generate_vedic_chart(self, date_str: str, time_str: str, location_str: str):
        """
        Main entry point. Generates full Kundali data.
        """
        # 1. Get Coordinates & Timezone
        lat, lon, tz_str = self._get_geo_coords(location_str)
        
        # 2. Parse Time
        local_tz = pytz.timezone(tz_str)
        try:
            dt_str = f"{date_str} {time_str}"
            local_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            local_dt = local_tz.localize(local_dt)
        except ValueError:
            # Fallback for different date formats if needed
            local_dt = datetime.now(local_tz)

        # 3. Create Skyfield Time
        t = ts.from_datetime(local_dt)
        
        # 4. Calculate Ayanamsa & Ascendant
        ayanamsa = self._calculate_ayanamsa(t)
        asc_tropical = self._calculate_ascendant(t, lat, lon)
        asc_sidereal = self._tropical_to_sidereal(asc_tropical, ayanamsa)
        asc_data = self._get_sign_data(asc_sidereal)
        
        # 5. Calculate Planets
        vedic_planets = {}
        
        # Determine Ascendant Sign Index for House Calculation
        asc_sign_index = self.SIGNS.index(asc_data['sign'])

        # -- Major Planets --
        for name, body in self.PLANET_MAPPING.items():
            astrometric = earth.at(t).observe(body)
            _, lon_ecl, _ = astrometric.ecliptic_latlon()
            
            sid_lon = self._tropical_to_sidereal(lon_ecl.degrees, ayanamsa)
            p_data = self._get_sign_data(sid_lon)
            
            # House Calculation
            p_sign_index = self.SIGNS.index(p_data['sign'])
            house = (p_sign_index - asc_sign_index + 12) % 12 + 1
            
            p_data['house'] = house
            vedic_planets[name] = p_data

        # -- Rahu & Ketu --
        nodes = self._get_rahu_ketu(t, ayanamsa)
        for name, n_data in nodes.items():
            n_sign_index = self.SIGNS.index(n_data['sign'])
            house = (n_sign_index - asc_sign_index + 12) % 12 + 1
            n_data['house'] = house
            vedic_planets[name] = n_data

        return {
            "meta": {
                "location_name": location_str,
                "lat": lat,
                "lon": lon,
                "datetime": str(local_dt),
                "ayanamsa": f"{ayanamsa:.4f}",
                "timezone": tz_str
            },
            "ascendant": asc_data,
            "planets": vedic_planets
        }

# Singleton Instance
astro_engine = AstroEngine()