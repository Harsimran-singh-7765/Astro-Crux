#!/usr/bin/env python3
"""
Test script to verify Vedic chart calculations
Testing with a known date: 22/09/2006 should be Virgo Sun
"""
import sys
sys.path.insert(0, '/home/harsimran/projects/astro-crux')

from datetime import datetime
from app.services.vedic_calculator import calculate_vedic_chart, get_location_coordinates

# Test case: 22/09/2006 - should be Virgo Sun
print("=" * 80)
print("TEST: Birth Date 22/09/2006 (Should be Virgo Sun)")
print("=" * 80)

# Create datetime (using noon as default time)
birth_date = datetime(2006, 9, 22, 12, 0, 0)  # Sept 22, 2006 at 12:00 PM

# Get Delhi coordinates (default)
lat, lon, tz = get_location_coordinates("delhi")

print(f"\n📍 Location: Delhi")
print(f"   Latitude: {lat}°")
print(f"   Longitude: {lon}°")
print(f"   Timezone: {tz}")

print(f"\n🕐 Birth Date & Time: {birth_date}")

# Calculate chart
try:
    chart = calculate_vedic_chart(birth_date, lat, lon, tz)
    
    print(f"\n✅ Chart Calculated Successfully!")
    print(f"\n🌍 Ayanamsa: {chart['meta']['ayanamsa']:.4f}°")
    
    print(f"\n☀️ SUN:")
    sun = chart['planets']['sun']
    print(f"   Sign: {sun['sign']} {sun['degree']:.2f}°")
    print(f"   Sidereal Longitude: {sun['longitude']:.2f}°")
    print(f"   House: {sun.get('house', 'N/A')}")
    
    print(f"\n🌙 MOON:")
    moon = chart['planets']['moon']
    print(f"   Sign: {moon['sign']} {moon['degree']:.2f}°")
    print(f"   Sidereal Longitude: {moon['longitude']:.2f}°")
    print(f"   House: {moon.get('house', 'N/A')}")
    
    print(f"\n🔺 ASCENDANT (Lagna):")
    asc = chart['ascendant']
    print(f"   Sign: {asc['sign']} {asc['degree']:.2f}°")
    print(f"   Sidereal Longitude: {asc['longitude']:.2f}°")
    
    print(f"\n📊 All Planets:")
    for planet_key, planet_data in chart['planets'].items():
        print(f"   {planet_key.upper():10} → {planet_data['sign']:12} {planet_data['degree']:6.2f}° (House {planet_data.get('house', '?')})")
    
    print("\n" + "=" * 80)
    print("✅ EXPECTED: Sun should be in Virgo")
    print(f"✅ ACTUAL: Sun is in {sun['sign']}")
    
    if sun['sign'] == 'Virgo':
        print("✓ TEST PASSED!")
    else:
        print("✗ TEST FAILED! Sun should be Virgo but got " + sun['sign'])
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
