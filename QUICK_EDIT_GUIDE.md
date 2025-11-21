# 🎯 QUICK REFERENCE - Edit Chart Files

## 📍 Where to Edit Based on What You Want to Change

### 1. **Change Chart Layout (Diamond → Hexagon → Other)**
```
File: testing/script.js
Lines: 156-292 (function drawKundliChart)

Key Section:
const housePositions = {
    1: { x: 1, y: 0 },    ← Change x,y coordinates
    2: { x: 2, y: 0 },
    // ...
};

Tip: x, y are grid coordinates (0-3 for 4×4 grid)
     Modify to create different layouts
```

---

### 2. **Change Chart Colors (Gold → Blue/Purple/etc)**
```
File: testing/index.html
Lines: 154-210 (CSS styling)

Key Section:
.house-polygon.active-glow {
    fill: rgba(251, 191, 36, 0.3);     ← Change this (gold)
    stroke: var(--gold);                ← Or this
}

Color Values: rgba(R, G, B, opacity)
- Gold: rgba(251, 191, 36, 0.3)
- Blue: rgba(59, 130, 246, 0.3)
- Purple: rgba(168, 85, 247, 0.3)
- Green: rgba(34, 197, 94, 0.3)
```

---

### 3. **Change Animation Speed (0.6s → Faster/Slower)**
```
File: testing/index.html
Line: 172

Find: animation: houseGlow 0.6s ease-out;
Change: 0.6s → any value (e.g., 0.3s for fast, 1.5s for slow)
```

---

### 4. **Change Planet Names (Sun/Moon/Mars → Sanskrit/Symbols/etc)**
```
File: app/services/vedic_calculator.py
Line: 35

Current:
PLANET_NAMES = {
    'sun': 'Sun',
    'moon': 'Moon',
    'mars': 'Mars',
    // ...
}

Change to:
'sun': 'Surya',      ← Sanskrit name
'moon': '☽',         ← Symbol
'mars': '♂',         ← Symbol
```

---

### 5. **Change House Meanings (Self/Wealth/Career/etc)**
```
File: app/services/vedic_calculator.py
Lines: 25-36

Current:
HOUSE_MEANINGS = {
    1: "Self & Personality",
    2: "Wealth & Resources",
    3: "Communication & Siblings",
    // ...
}

These are returned in chart data and shown to users
```

---

### 6. **Change Highlight Duration (4 seconds → 2/6/etc)**
```
File: testing/script.js
Line: 301

Current:
setTimeout(() => {
    removeHouseHighlight();
}, 4000);  ← Change this (milliseconds)

Change to:
2000 (2 seconds)
6000 (6 seconds)
10000 (10 seconds)
```

---

### 7. **Change Focus Signal Format**
```
File: app/services/llm_service.py
Lines: 167-170

Current pattern: [FOCUS:HOUSE_7]

To change:
Edit regex: \[FOCUS:([A-Z_0-9]+)\]

Examples:
- [FOCUS:HOUSE_7] ← Current
- <FOCUS>HOUSE_7</FOCUS> ← Change pattern
- {FOCUS: HOUSE_7} ← Change pattern
```

---

### 8. **Change WebSocket Message Format**
```
File: app/services/game_session_manager.py
Lines: 160-180

Current messages:
{
  "status": "chart_data",
  "chart": {...}
}

{
  "status": "ai_focus",
  "focus": "HOUSE_7"
}

To change: Add new fields or modify structure
Also update script.js handleJson() to parse new format
```

---

### 9. **Add More Planets (currently 7)**
```
File: app/services/vedic_calculator.py
Lines: 35-37

Current:
PLANET_NAMES = {
    'sun': 'Sun',
    'moon': 'Moon',
    'mercury': 'Mercury',
    'venus': 'Venus',
    'mars': 'Mars',
    'jupiter': 'Jupiter barycenter',
    'saturn': 'Saturn barycenter',
}

To add Rahu/Ketu or Nodes:
'rahu': 'Rahu barycenter',
'ketu': 'Ketu barycenter',
```

---

### 10. **Change Grid Size (4×4 → 3×3 / 5×5)**
```
File: testing/script.js
Line: 166

Current:
const cellSize = outerSize / 4;  ← 4×4 grid

To change:
const cellSize = outerSize / 3;  ← 3×3 grid
const cellSize = outerSize / 5;  ← 5×5 grid

Note: Will need to adjust housePositions accordingly!
```

---

### 11. **Change SVG Container Size**
```
File: testing/index.html
Line: 477

Current:
<svg id="kundliChart" viewBox="0 0 400 400" 
     width="400" height="400"></svg>

To make bigger/smaller:
<svg id="kundliChart" viewBox="0 0 500 500" 
     width="500" height="500"></svg>

Tip: Keep viewBox and width/height proportional
```

---

### 12. **Change House Text Style (H1, H2 → 1, 2 / House 1, House 2)**
```
File: testing/script.js
Line: 217

Current:
text.textContent = `${i}`;  ← Shows "1", "2", etc

Change to:
text.textContent = `H${i}`;           ← Shows "H1", "H2"
text.textContent = `House ${i}`;      ← Shows "House 1"
text.textContent = ['', 'I', 'II', 'III', ...][i];  ← Roman numerals
```

---

### 13. **Change Planet Abbreviation Length**
```
File: testing/script.js
Line: 313

Current:
planetText.textContent = planetName.substring(0, 2).toUpperCase();

This shows: "SU" (Sun), "MO" (Moon), "MA" (Mars), etc

Change to:
.substring(0, 1)  ← Show just "S", "M"
.substring(0, 3)  ← Show "Sun", "Moo", "Mar"
```

---

### 14. **Add New House Meanings or Descriptions**
```
File: app/services/llm_service.py
Line: 50 (in system prompt)

Add context about house meanings:
HOUSE_MEANINGS = {
    1: "Self, appearance, identity, physical body",
    2: "Wealth, finances, food, family, speech",
    // ...
}

Include these in system prompt so LLM knows what to discuss
```

---

### 15. **Change Zodiac Signs (if needed)**
```
File: app/services/vedic_calculator.py
Lines: 19-21

Current:
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

Change to other languages:
Hindi: ["Mesha", "Vrishabha", "Mithuna", ...]
Sanskrit symbols: ["♈", "♉", "♊", ...]
```

---

## 📋 File Editing Checklist

| Change Type | File | Lines | Difficulty |
|------------|------|-------|------------|
| Layout | script.js | 156-292 | Medium |
| Colors | index.html | 154-210 | Easy |
| Speed | index.html | 172 | Easy |
| Planets | vedic_calculator.py | 35 | Easy |
| Houses | vedic_calculator.py | 25 | Easy |
| Signals | llm_service.py | 167 | Medium |
| Messages | game_session_manager.py | 160 | Hard |
| Duration | script.js | 301 | Easy |
| Grid Size | script.js | 166 | Medium |
| Text | script.js | 217, 313 | Easy |

---

## 🔄 Testing Changes

After editing any file:

1. **Python files** (vedic_calculator.py, llm_service.py, etc):
   ```bash
   python test_integration.py  # Verify backend
   ```

2. **JavaScript files** (script.js):
   - Open browser developer console (F12)
   - Look for errors
   - Check console.log outputs

3. **HTML/CSS files** (index.html):
   - Refresh browser (Ctrl+R or Cmd+R)
   - Check if layout/colors changed as expected

4. **Full integration**:
   - Start server: `python app/main.py`
   - Open UI: `http://localhost:8000/testing/index.html`
   - Test full flow: Birth details → Chart render → Hold to speak → House highlight

---

## ⚡ Examples of Common Changes

### Example 1: Make chart twice as fast
```
File: testing/index.html
Line: 172

OLD: animation: houseGlow 0.6s ease-out;
NEW: animation: houseGlow 0.3s ease-out;
```

### Example 2: Change highlight from gold to purple
```
File: testing/index.html
Lines: 166-168

OLD:
.house-polygon.active-glow {
    fill: rgba(251, 191, 36, 0.3);
    stroke: var(--gold);

NEW:
.house-polygon.active-glow {
    fill: rgba(168, 85, 247, 0.3);
    stroke: rgba(168, 85, 247, 1);
```

### Example 3: Change planet display from "SU" to full "Sun"
```
File: testing/script.js
Line: 313

OLD: planetText.textContent = planetName.substring(0, 2).toUpperCase();
NEW: planetText.textContent = planetName;
```

### Example 4: Make houses bigger (5×5 grid instead of 4×4)
```
File: testing/script.js
Line: 166

OLD: const cellSize = outerSize / 4;
NEW: const cellSize = outerSize / 5;

Also update housePositions with new x,y coordinates!
```

---

All files and line numbers are accurate for the current implementation! 🎯
