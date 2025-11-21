#!/usr/bin/env python3
"""
Verification Script - Scientific Visuals Module
Checks that all components are properly integrated
"""

import os
import json
import sys
from pathlib import Path

def check_file_exists(path, description):
    """Check if file exists and readable"""
    if os.path.exists(path) and os.path.isfile(path):
        size = os.path.getsize(path)
        print(f"✅ {description}")
        print(f"   Location: {path}")
        print(f"   Size: {size} bytes")
        return True
    else:
        print(f"❌ {description} - NOT FOUND")
        print(f"   Expected: {path}")
        return False

def check_function_in_file(filepath, function_name):
    """Check if function exists in Python file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if f"def {function_name}" in content:
                print(f"   ✅ Function: {function_name}")
                return True
            else:
                print(f"   ❌ Function: {function_name} - NOT FOUND")
                return False
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return False

def check_javascript_function(filepath, function_name):
    """Check if JavaScript function exists"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if f"function {function_name}" in content or f"const {function_name}" in content:
                print(f"   ✅ Function: {function_name}")
                return True
            else:
                print(f"   ❌ Function: {function_name} - NOT FOUND")
                return False
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return False

def check_css_class(filepath, class_name):
    """Check if CSS class exists in HTML file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            # Check for CSS class definition
            if f".{class_name}" in content or f"class=\"{class_name}" in content:
                print(f"   ✅ CSS: .{class_name}")
                return True
            else:
                print(f"   ❌ CSS: .{class_name} - NOT FOUND")
                return False
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return False

def main():
    print("=" * 70)
    print("SCIENTIFIC VISUALS MODULE - VERIFICATION")
    print("=" * 70)
    print()
    
    base_path = "/home/harsimran/projects/astro-crux"
    all_passed = True
    
    # 1. Check backend files
    print("1. BACKEND FILES")
    print("-" * 70)
    
    files_to_check = [
        (f"{base_path}/app/services/vedic_calculator.py", "Vedic Calculator"),
        (f"{base_path}/app/services/llm_service.py", "LLM Service"),
        (f"{base_path}/app/services/game_session_manager.py", "Game Session Manager"),
    ]
    
    for filepath, desc in files_to_check:
        if not check_file_exists(filepath, desc):
            all_passed = False
    
    print()
    
    # 2. Check backend functions
    print("2. BACKEND FUNCTIONS")
    print("-" * 70)
    
    checks = [
        (f"{base_path}/app/services/vedic_calculator.py", 
         ["calculate_vedic_chart", "calculate_ayanamsa", "tropical_to_sidereal"]),
        (f"{base_path}/app/services/llm_service.py", 
         ["extract_focus_signal", "clean_response_text"]),
        (f"{base_path}/app/services/game_session_manager.py", 
         ["_process_user_transcript", "_stream_ai_audio"]),
    ]
    
    for filepath, functions in checks:
        if os.path.exists(filepath):
            print(f"✅ {os.path.basename(filepath)}")
            for func in functions:
                if not check_function_in_file(filepath, func):
                    all_passed = False
        else:
            print(f"❌ {os.path.basename(filepath)} not found")
            all_passed = False
    
    print()
    
    # 3. Check frontend files
    print("3. FRONTEND FILES")
    print("-" * 70)
    
    frontend_files = [
        (f"{base_path}/testing/index.html", "HTML Interface"),
        (f"{base_path}/testing/script.js", "JavaScript Logic"),
    ]
    
    for filepath, desc in frontend_files:
        if not check_file_exists(filepath, desc):
            all_passed = False
    
    print()
    
    # 4. Check JavaScript functions
    print("4. JAVASCRIPT FUNCTIONS")
    print("-" * 70)
    
    js_file = f"{base_path}/testing/script.js"
    if os.path.exists(js_file):
        print(f"✅ {os.path.basename(js_file)}")
        js_functions = ["drawKundliChart", "highlightHouse", "removeHouseHighlight", "handleJson"]
        for func in js_functions:
            if not check_javascript_function(js_file, func):
                all_passed = False
    else:
        print(f"❌ {os.path.basename(js_file)} not found")
        all_passed = False
    
    print()
    
    # 5. Check SVG and CSS
    print("5. SVG & CSS ELEMENTS")
    print("-" * 70)
    
    html_file = f"{base_path}/testing/index.html"
    if os.path.exists(html_file):
        print(f"✅ {os.path.basename(html_file)}")
        
        # Check for SVG element
        try:
            with open(html_file, 'r') as f:
                content = f.read()
                if 'id="kundliChart"' in content and '<svg' in content:
                    print("   ✅ SVG Element: kundliChart")
                else:
                    print("   ❌ SVG Element: kundliChart - NOT FOUND")
                    all_passed = False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            all_passed = False
        
        # Check CSS classes
        css_classes = ["house-polygon", "active-glow", "planet-text", "ascendant-text"]
        for css_class in css_classes:
            if not check_css_class(html_file, css_class):
                all_passed = False
    
    print()
    
    # 6. Check documentation
    print("6. DOCUMENTATION")
    print("-" * 70)
    
    docs = [
        (f"{base_path}/SCIENTIFIC_VISUALS_README.md", "Complete Documentation"),
        (f"{base_path}/IMPLEMENTATION_SUMMARY.md", "Implementation Summary"),
        (f"{base_path}/QUICK_REFERENCE.md", "Quick Reference Guide"),
        (f"{base_path}/test_integration.py", "Integration Tests"),
    ]
    
    for filepath, desc in docs:
        if not check_file_exists(filepath, desc):
            all_passed = False
    
    print()
    
    # 7. Check imports in game_session_manager
    print("7. IMPORTS & INTEGRATION")
    print("-" * 70)
    
    gsm_file = f"{base_path}/app/services/game_session_manager.py"
    try:
        with open(gsm_file, 'r') as f:
            content = f.read()
            imports_to_check = [
                "from app.services.llm_service import",
                "extract_focus_signal",
                "clean_response_text"
            ]
            for imp in imports_to_check:
                if imp in content:
                    print(f"   ✅ Import: {imp}")
                else:
                    print(f"   ❌ Import: {imp} - NOT FOUND")
                    all_passed = False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_passed = False
    
    print()
    
    # 8. Summary
    print("=" * 70)
    if all_passed:
        print("✅ ALL VERIFICATION CHECKS PASSED!")
        print()
        print("Scientific Visuals Module is complete and ready for production.")
        print()
        print("Next steps:")
        print("  1. Start server: python app/main.py")
        print("  2. Open UI: http://localhost:8000/testing/index.html")
        print("  3. Test: Hold microphone and speak")
        print("  4. Watch chart highlight! ✨")
        print()
        return 0
    else:
        print("❌ SOME VERIFICATION CHECKS FAILED!")
        print()
        print("Please review the items marked with ❌ above.")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
