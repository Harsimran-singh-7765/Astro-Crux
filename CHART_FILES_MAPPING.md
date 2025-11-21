# 📊 Visual Chart - File Mapping & Components

## 🎯 Quick Reference - Where Everything Is

```
VEDIC CHART SYSTEM
├── BACKEND (Python)
│   ├── app/services/vedic_calculator.py          ← Calculations
│   ├── app/services/llm_service.py                ← Focus signals
│   ├── app/services/game_session_manager.py       ← WebSocket
│   └── app/api/v1/endpoints/game.py               ← API endpoints
│
├── FRONTEND (JavaScript/HTML/CSS)
│   ├── testing/index.html                         ← UI layout + CSS
│   └── testing/script.js                          ← Chart rendering + events
│
└── DATABASE/CONFIG
    └── app/schemas/game_schemas.py                ← Data structures
```

---

## 📁 File-by-File Breakdown

### 1️⃣ **testing/index.html** (UI & Styling)

**What it contains:**
- HTML structure for entire application
- CSS styling for all visual elements
- SVG container for Kundli chart
- Audio player element
- Microphone button
- Chat transcript area

**Key Sections:**

```html
<!-- SVG Chart Container -->
<svg id="kundliChart" viewBox="0 0 400 400" width="400" height="400"></svg>

<!-- Microphone Button -->
<button id="speakBtn" onmousedown="startRecording(event)" 
        onmouseup="stopRecording(event)" disabled>🎤 Hold to Speak</button>

<!-- Audio Player -->
<audio id="audioPlayer"></audio>

<!-- Transcript Area -->
<div id="transcript"></div>
```

**CSS Classes for Chart:**
- `.house-polygon` - Base house styling (rectangle/polygon)
- `.house-polygon.active-glow` - Gold highlight when AI discusses
- `.planet-text` - Planet name styling (cyan color)
- `.ascendant-text` - Ascendant label styling (pink color)
- `.house-text` - House number styling (gold color)
- `@keyframes houseGlow` - Smooth 0.6s animation

**Line Numbers:**
- SVG element: ~477
- CSS for houses: ~154-180
- Microphone button: ~484
- Audio player: ~490

---

### 2️⃣ **testing/script.js** (JavaScript Logic)

**Global Variables for Chart:**
```javascript
let chartData = null;           // Stores chart from backend
let isRecording = false;        // Hold-to-speak state
let socket;                     // WebSocket connection
let audioBuffer = [];           // Audio chunks from TTS
```

**Main Functions for Chart:**

| Function | Purpose | Line # |
|----------|---------|--------|
| `drawKundliChart(chart)` | Draws 4×4 square Kundli | 156 |
| `highlightHouse(num)` | Add gold glow to house | 293 |
| `removeHouseHighlight()` | Remove all glows | 305 |
| `handleJson(msg)` | Process WebSocket messages | 318 |
| `startRecording(e)` | Hold button down = start mic | 537 |
| `stopRecording(e)` | Release button = stop mic | 559 |

**Chart Drawing Logic (lines 156-292):**
```javascript
function drawKundliChart(chart) {
    // 1. Create SVG elements for 12 houses
    // 2. Position planets in correct houses
    // 3. Draw ascendant in center circle
    // 4. Layout: 4×4 grid with center area
}
```

**House Positions (Traditional North Indian):**
```javascript
const housePositions = {
    1: { x: 1, y: 0 },    // Top center
    2: { x: 2, y: 0 },    // Top right
    3: { x: 3, y: 0 },    // Top far right
    4: { x: 3, y: 1 },    // Right
    // ... (continues clockwise)
    12: { x: 0, y: 0 }    // Top left corner
};
```

**Message Handling (lines 318-345):**
```javascript
if (msg.status === "chart_data") {
    // Receives chart from backend
    drawKundliChart(msg.chart);
}
if (msg.status === "ai_focus") {
    // Receives focus signal like "HOUSE_7"
    highlightHouse(7);
}
```

---

### 3️⃣ **app/services/vedic_calculator.py** (Astronomical Calculations)

**What it does:**
- Calculates Vedic chart positions using Skyfield ephemeris
- Converts tropical (Skyfield) → sidereal (Vedic)
- Calculates Lahiri Ayanamsa
- Places planets in houses
- Returns JSON chart data

**Main Function:**
```python
def calculate_vedic_chart(birth_datetime, latitude, longitude, timezone_str='UTC') -> Dict
```

**What it returns:**
```json
{
  "meta": {
    "date": "2000-01-01 12:00:00",
    "ayanamsa": 23.85
  },
  "ascendant": {
    "sign": "Sagittarius",
    "longitude": 251.09
  },
  "planets": {
    "sun": {
      "longitude": 281.5,
      "sign": "Capricorn",
      "degree": 11.5,
      "house": 1
    },
    "moon": { ... },
    "mars": { ... }
    // 7 planets total
  },
  "houses": {
    "1": "Self & Personality",
    "2": "Wealth & Resources",
    // ... all 12 house meanings
  }
}
```

**Key Functions:**
- `calculate_ayanamsa(year)` - Line ~40
- `tropical_to_sidereal(tropical, ayanamsa)` - Line ~45
- `longitude_to_sign(longitude)` - Line ~50
- `calculate_vedic_chart()` - Line ~69
- `get_location_coordinates(city)` - Line ~120

---

### 4️⃣ **app/services/llm_service.py** (AI Response Signals)

**What it does:**
- Generates Vedic astrology responses from LLM
- Embeds focus signals in responses: `[FOCUS:HOUSE_7]`
- Extracts and cleans focus signals

**Key Functions:**
```python
def extract_focus_signal(response_text: str) -> str
    # Extracts "HOUSE_7" from "[FOCUS:HOUSE_7] Your relationships..."
    # Returns: "HOUSE_7" or ""

def clean_response_text(response_text: str) -> str
    # Removes "[FOCUS:HOUSE_7]" before sending to TTS
    # Returns: "Your relationships..."
```

**Signal Format:**
```
LLM Output:     "[FOCUS:HOUSE_7] Your relationships are active..."
Extract:        "HOUSE_7"
Clean:          "Your relationships are active..."
Frontend:       Highlight House 7, Play audio
```

---

### 5️⃣ **app/services/game_session_manager.py** (WebSocket Orchestration)

**What it does:**
- Manages real-time WebSocket communication
- Sends chart data on session start
- Extracts focus signals and sends to frontend
- Handles microphone recording

**Key Methods:**
- `_process_user_transcript()` - Lines ~160-180
  - Extracts focus signal
  - Cleans text for TTS
  - Sends both to frontend

**Messages Sent to Frontend:**
```json
{
  "status": "chart_data",
  "chart": { ... full chart JSON ... }
}

{
  "status": "ai_focus",
  "focus": "HOUSE_7"
}

{
  "status": "ai_response_text",
  "text": "Your relationships are active..."
}
```

---

### 6️⃣ **app/api/v1/endpoints/game.py** (API Endpoints)

**Endpoints:**
```python
POST /api/v1/start          # Calculates chart, returns session_id
WS /api/v1/game/ws/{id}    # WebSocket connection for live session
```

**Flow:**
```
1. User enters birth details
2. POST /api/v1/start
3. Backend calls calculate_vedic_chart()
4. Returns session_id
5. Frontend opens WebSocket /ws/{session_id}
6. Backend sends chart_data message
7. Frontend renders chart with drawKundliChart()
```

---

### 7️⃣ **app/schemas/game_schemas.py** (Data Structures)

**Defines:**
```python
class GameSession:
    session_id: str
    user_id: str
    chart_data: dict          # Contains full Vedic chart
    conversation_history: list
```

---

## 🔄 Data Flow Diagram

```
User Input (Birth Details)
    ↓
[POST /api/v1/start]
    ↓
vedic_calculator.calculate_vedic_chart()
    ↓ Returns: {"ascendant": {...}, "planets": {...}, "houses": {...}}
    ↓
GameSession stores chart_data
    ↓
[WebSocket connection established]
    ↓
Backend sends: {"status": "chart_data", "chart": {...}}
    ↓
Frontend receives in handleJson()
    ↓
drawKundliChart(chart)
    ↓
SVG rendered: 12 houses + planets + ascendant
    ↓
User asks question (hold microphone)
    ↓
LLM responds with [FOCUS:HOUSE_7] embedded
    ↓
Backend extracts signal, cleans text
    ↓
Sends: {"status": "ai_focus", "focus": "HOUSE_7"}
    ↓
Frontend calls highlightHouse(7)
    ↓
House 7 glows gold ✨
```

---

## 🎨 Visual Chart Components Location

### HTML/CSS (testing/index.html)
- **SVG Container**: Line ~477
- **House Styling**: Lines 154-180
- **Animation Keyframes**: Lines 173-184
- **Planet/Ascendant Text**: Lines 185-210

### JavaScript (testing/script.js)
- **Chart Drawing**: Lines 156-292
- **House Highlighting**: Lines 293-311
- **Message Handler**: Lines 318-345
- **Microphone Logic**: Lines 537-580

### Python Backend
- **Chart Calculation**: vedic_calculator.py (69-120)
- **Signal Extraction**: llm_service.py (167-190)
- **WebSocket Sends**: game_session_manager.py (160-180)
- **API Entry**: game.py (12-35)

---

## 📋 File Modification Checklist

To make changes to the chart system, modify:

### To change chart layout:
- [ ] `testing/script.js` - `housePositions` object (lines 170-194)
- [ ] `testing/script.js` - `drawKundliChart()` function (lines 156-292)

### To change chart styling:
- [ ] `testing/index.html` - CSS classes (lines 154-210)

### To change planets/signs:
- [ ] `vedic_calculator.py` - PLANET_NAMES dict (line ~35)
- [ ] `vedic_calculator.py` - SIGNS list (line ~20)
- [ ] `vedic_calculator.py` - HOUSE_MEANINGS dict (line ~25)

### To change focus signals:
- [ ] `llm_service.py` - Extract pattern (line ~170)
- [ ] `script.js` - Signal parsing in handleJson() (line ~330)

### To change animation:
- [ ] `testing/index.html` - @keyframes houseGlow (lines 173-184)
- [ ] `testing/script.js` - Highlight duration (line ~301, currently 4000ms)

---

## 🚀 To Make Your Own Changes

**Example: Change highlight color from gold to blue**

1. Open: `testing/index.html`
2. Find: `.house-polygon.active-glow` (line ~166)
3. Change: `fill: rgba(251, 191, 36, 0.3);` → `fill: rgba(100, 200, 255, 0.3);`
4. Change: `stroke: var(--gold);` → `stroke: rgba(100, 200, 255, 1);`

**Example: Change animation speed from 0.6s to 1s**

1. Open: `testing/index.html`
2. Find: `animation: houseGlow 0.6s ease-out;` (line ~172)
3. Change: `0.6s` → `1s`

**Example: Change grid from 4×4 to 3×4**

1. Open: `testing/script.js`
2. Find: `const cellSize = outerSize / 4;` (line ~166)
3. Change: `/4` → `/3`
4. Also update `housePositions` object accordingly

---

## 📞 Summary

| Task | File | Lines |
|------|------|-------|
| Chart Layout | script.js | 156-292 |
| Chart Styling | index.html | 154-210 |
| Calculations | vedic_calculator.py | 40-120 |
| Signals | llm_service.py | 167-190 |
| WebSocket | game_session_manager.py | 160-180 |
| API | game.py | 12-35 |

**Everything you need to customize is in these files!** 🎯
