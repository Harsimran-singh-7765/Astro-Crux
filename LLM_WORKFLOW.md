# LLM Workflow: How Acharya Answers Your Questions 🌟

## Overview
When you ask Acharya a question, it goes through a sophisticated multi-stage pipeline that combines:
1. **Chart Data Analysis** - Understanding your birth chart
2. **RAG (Retrieval-Augmented Generation)** - Fetching relevant Vedic knowledge
3. **LLM Intelligence** - Claude Gemini 2.0 Flash processing
4. **Rule-Based Logic** - Applying Vedic astrology rules
5. **Response Refinement** - Generating conversational output

---

## 📊 Complete LLM Query Flow

```
USER QUESTION
    ↓
[STT] Speech-to-Text (Deepgram)
    ↓
TRANSCRIPT (Text)
    ↓
[GAME_SESSION_MANAGER] Process User Input
    ├── Add to conversation_history
    ├── Call LLM service
    └── Stream response via TTS
    ↓
[LLM_SERVICE] Generate Response
    ├── Build system prompt
    ├── Extract chart insights
    ├── Query RAG system
    ├── Call Claude API
    └── Parse & return response
    ↓
[RESPONSE] Audio + Text + Chart Focus
    ↓
TTS (Text-to-Speech - Deepgram)
    ↓
AUDIO PLAYBACK
```

---

## 🧠 LLM Service Architecture

### File: `/app/services/llm_service.py`

#### 1. **Chart Insights Extraction**
```python
def _extract_chart_insights(chart_data: dict) -> str:
```
Parses birth chart and creates natural language insights:

**Input:** Birth chart data with planets, houses, aspects
**Output:** Formatted text like:
```
sun is in leo (house 10) at 120.45° - influences self-identity, father, authority, vitality
moon is in gemini (house 7) at 65.30° - influences mind, emotions, mother, comfort
...
Ascendant (Lagna): Libra
Key Planetary Aspects:
- Sun aspects Moon (harmonious)
- Saturn squares Venus (challenging)
```

#### 2. **RAG System Integration**
```python
def get_astro_response(session: GameSession) -> str:
```

Before calling Claude, the system:
1. **Queries astro_rules.json** for relevant rules
2. **Searches RAG knowledge base** for similar questions
3. **Combines findings** into context for Claude

**RAG Query Process:**
```python
# Example: User asks about marriage
rag_context = rag_service.query(
    query="marriage relationship 7th house venus",
    top_k=3  # Get top 3 similar entries
)
# Returns formatted context about relationships in astrology
```

#### 3. **System Prompt Construction**
The Acharya persona is defined via detailed system prompt:

```python
system_prompt = f"""You are Acharya Gemini, a master Vedic Astrologer with 30 years of practice. 
You combine ancient Jyotish wisdom with precise astronomical calculations.

YOUR PERSONALITY:
- Warm, empathetic, and conversational (like a wise grandfather)
- Grounded in mathematics: You reference actual planetary positions
- Balance mysticism with practicality
- Speak naturally in short sentences (2-4 sentences max per response)
- Use phrases like "Your chart reveals...", "The planets suggest...", "Consider this..."
- Avoid fortune-telling or definitive predictions; instead offer insights and guidance

THE SEEKER'S BIRTH CHART (Sidereal/Lahiri Ayanamsa):
Name: {name}
Birth Details: {date_time}
Location: {location}

PLANETARY POSITIONS & INSIGHTS:
{chart_insights}  ← From _extract_chart_insights()

CORE RULES:
1. ALWAYS reference specific placements when answering
2. Connect planets to the question asked
3. If a question is unrelated to astrology, gently redirect
4. Keep responses conversational and voice-friendly (no bullet points)
5. If uncertain about a placement, say "Let me examine that area of your chart more closely..."
6. Integrate Vedic concepts naturally: dashas (periods), yogas (combinations), aspects (drishti)
```

---

## 📋 astro_rules.json Structure

**File Location:** `/data/astro_rules.json`

### Purpose
Defines **rules-based mappings** for quick, accurate astrological guidance without waiting for LLM.

### JSON Schema

```json
{
  "planet_domains": {
    "sun": {
      "significations": ["self-identity", "father", "authority", "vitality", "creativity"],
      "governs": ["10th house - Career", "Leo"]
    },
    "moon": {
      "significations": ["mind", "emotions", "mother", "comfort", "subconscious"],
      "governs": ["4th house - Home", "Cancer"]
    },
    "mercury": {
      "significations": ["communication", "intellect", "trade", "siblings", "learning"],
      "governs": ["3rd house - Communication", "Gemini", "Virgo"]
    },
    // ... more planets
  },
  
  "house_meanings": {
    "1": {
      "name": "Self & Personality",
      "rules": "Physical appearance, self, temperament",
      "positive_planets": ["sun", "jupiter"],
      "negative_planets": ["saturn", "mars"]
    },
    "7": {
      "name": "Relationships & Marriage",
      "rules": "Spouse, partnerships, public relations",
      "positive_planets": ["venus", "jupiter"],
      "negative_planets": ["saturn", "mars"]
    },
    // ... more houses
  },
  
  "planetary_aspects": {
    "sun_moon_conjunction": {
      "type": "powerful",
      "effects": "Strong will, emotional stability",
      "advice": "Channel energy constructively"
    },
    "saturn_venus_square": {
      "type": "challenging",
      "effects": "Delays in marriage, relationship lessons",
      "advice": "Patience needed, build emotional maturity"
    }
    // ... more aspects
  },
  
  "remedies": {
    "weak_venus": ["Wear white diamond", "Chant Venus mantra", "Donate white items"],
    "saturn_troubles": ["Worship Hanuman on Saturdays", "Give sesame seeds to poor"],
    "moon_weakness": ["Wear pearl", "Drink milk", "Worship the Moon"]
  },
  
  "dashas": {
    "sun_dasha": {
      "duration": "6 years",
      "effects": "Leadership, authority, health matters",
      "challenges": "Ego conflicts, health issues"
    }
    // ... more dashas
  }
}
```

### How It's Used in LLM Response

When Acharya answers, it references these rules:

```python
# Example: User asks "Why am I facing marriage delays?"

# 1. Check 7th house from chart
# 2. Find Venus position (marriage significator)
# 3. Look for Saturn aspects (delays)
# 4. Query astro_rules.json for saturn_venus_square
# 5. Incorporate remedy suggestions
# 6. Craft response using this data

Response: "Your Venus sits in the 7th house of marriage, but Saturn's 
challenging aspect suggests relationship maturity is needed. Saturn teaches 
patience. Consider wearing a blue sapphire or worshipping Hanuman on 
Saturdays - these strengthen Saturn's positive influence."
```

---

## 🔄 Complete Request-Response Cycle

### Step 1: User Speaks
```
Input: "I'm having trouble in relationships, what should I do?"
```

### Step 2: Speech-to-Text
```python
# deepgram_service.py
transcript = "I'm having trouble in relationships, what should I do?"
```

### Step 3: Process in GameSessionManager
```python
# game_session_manager.py > _process_user_transcript()
conversation_history.append(
    ConversationEntry(role="user", message=transcript)
)

response = await get_astro_response(self.session)
```

### Step 4: Build Comprehensive Context
```python
# llm_service.py > get_astro_response()

# Extract insights from birth chart
chart_insights = _extract_chart_insights(chart_data)
# "Venus in Libra 7th house... Saturn aspects 7th house..."

# Query RAG for relevant knowledge
rag_context = rag_service.query(
    query="relationships marriage troubles 7th house venus saturn",
    top_k=3
)
# Returns: Vedic wisdom about Saturn-Venus combinations, 7th house remedies, etc.

# Query astro_rules.json for specific rules
rules = load_astro_rules()
venus_info = rules["planet_domains"]["venus"]
house_7_info = rules["house_meanings"]["7"]
saturn_remedies = rules["remedies"]["saturn_troubles"]
```

### Step 5: Build Final Prompt for Claude

```python
full_prompt = f"""
{system_prompt}  # Acharya persona + chart data

RETRIEVED KNOWLEDGE (from RAG):
{rag_context}

APPLICABLE RULES (from astro_rules.json):
- Venus significations: {venus_info['significations']}
- 7th House rules: {house_7_info['rules']}
- Saturn remedies: {saturn_remedies}

CONVERSATION SO FAR:
USER: I'm having trouble in relationships, what should I do?

CURRENT QUESTION: I'm having trouble in relationships, what should I do?

Respond as Acharya Gemini in 2-3 natural sentences, referencing specific planetary placements.
"""
```

### Step 6: Claude Processes & Responds

```python
response = llm_client.models.generate_content(
    model="gemini-2.0-flash",
    contents=full_prompt,
    config={
        "temperature": 0.7,
        "top_p": 0.9,
        "max_output_tokens": 150
    }
)
```

### Step 7: Extract House/Planet Mentions
```python
# Detect which houses/planets were mentioned
houses_mentioned = detect_house_mentions(response)  # [7]
planets_mentioned = detect_planet_mentions(response)  # ['Venus', 'Saturn']

# Send chart focus update to frontend
await _send_json({
    "status": "chart_focus",
    "houses": [7],
    "planets": ['Venus', 'Saturn']
})
```

### Step 8: Text-to-Speech

```python
# deepgram_service.py > text_to_speech_stream()
cleaned_response = clean_response_text(response)
# "Your Venus sits in the 7th house of partnerships. Saturn's aspect..."

# Stream audio back to client
async for audio_chunk in text_to_speech_stream(cleaned_response):
    await websocket.send_bytes(audio_chunk)
```

### Step 9: Display & Highlight on Frontend

```javascript
// Frontend receives multiple messages
1. { status: "ai_response_text", text: "Your Venus sits..." }
   → Display in chat

2. { status: "chart_focus", houses: [7], planets: ["Venus", "Saturn"] }
   → Highlight house 7
   → Show Venus and Saturn planets in house 7

3. Binary audio chunks
   → Play audio via WebAudioAPI
```

---

## 🎯 Example End-to-End Flow

### User Question
```
"I'm 30 years old but haven't married yet. 
My friend's birth chart shows they got married at 25. 
Why is my life different?"
```

### System Processing

**1. Chart Analysis:**
```
User's 7th house (marriage): Venus in Saturn sign, Saturn aspects
Friend's 7th house: Venus without Saturn aspect
```

**2. RAG Retrieval:**
```
Query: "marriage delay Saturn 7th house Venus remedies"
Results:
- "Saturn in/aspecting 7th house indicates maturity before marriage"
- "Venus in Saturn signs: delays but stronger partnerships"
- "Recommended: Chant Hanuman Chalisa, wear sapphire"
```

**3. astro_rules.json Application:**
```
saturn_venus_square: {
  "type": "challenging",
  "effects": "Delays in marriage, relationship lessons",
  "advice": "Patience needed, build emotional maturity"
}

remedies.saturn_troubles: [
  "Worship Hanuman on Saturdays",
  "Give sesame seeds to poor",
  "Chant Saturn Mantra"
]
```

**4. Claude Response:**
```
"Your Venus sits in the 7th house of marriage, but Saturn's challenging 
influence suggests the universe is teaching you partnership maturity. 
Rather than a delay, see this as Saturn preparing you for a deeper, 
more stable relationship. Worshipping Hanuman on Saturdays and wearing 
a blue sapphire can strengthen Saturn's protective energy in your chart."
```

**5. Frontend Display:**
- Chat message appears
- House 7 glows with highlight
- Venus and Saturn planets shown in house 7
- Audio plays: Acharya's voice speaking the response

---

## 🔌 Key Integration Points

### 1. **game_session_manager.py**
- Receives user transcript
- Calls `get_astro_response(session)`
- Detects houses/planets mentioned
- Sends multiple message types to frontend

### 2. **llm_service.py**
- Core intelligence hub
- Builds comprehensive prompts
- Integrates RAG results
- Applies astro_rules.json
- Calls Claude API
- Returns formatted response

### 3. **rag_service.py**
- Retrieves similar Vedic wisdom
- Provides context for Claude
- Indexes knowledge base entries

### 4. **vedic_calculator.py**
- Calculates accurate birth chart
- Provides: planets, houses, aspects
- Used in chart_insights extraction

### 5. **deepgram_service.py**
- STT: Converts speech to text
- TTS: Converts response to speech

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER ASKS QUESTION                       │
└────────────────────┬────────────────────────────────────────┘
                     │ Audio
                     ↓
           ┌──────────────────┐
           │ Deepgram STT     │
           │ (Speech→Text)    │
           └────────┬─────────┘
                    │ "What about my marriage?"
                    ↓
         ┌──────────────────────┐
         │ GameSessionManager   │
         │ _process_transcript()│
         └──────────┬───────────┘
                    │
         ┌──────────────────────────────┐
         │    LLM SERVICE               │
         ├──────────────────────────────┤
         │ 1. Extract Chart Insights    │
         │ 2. Query RAG System          │
         │ 3. Load astro_rules.json     │
         │ 4. Build System Prompt       │
         │ 5. Call Claude API           │
         │ 6. Parse Response            │
         └──────────┬───────────────────┘
                    │ "Your Venus in 7th..."
                    ↓
         ┌──────────────────────┐
         │ Detect Houses/Planets│
         └──────────┬───────────┘
                    │
       ┌────────────┴──────────────┐
       │                           │
       ↓ Text                      ↓ Chart Focus
  Display in Chat            Highlight House 7
                             Show Venus, Saturn
                    │
       ┌────────────┴──────────────┐
       │                           │
       ↓                           ↓
    Deepgram TTS          Frontend Display
    (Text→Speech)         (Glowing houses)
       │                           │
       ↓ Audio                     ↓ Visual
   WebAudioAPI            SVG Polygon Highlight
   Play audio             Planet names in house
```

---

## ⚙️ Configuration & Parameters

### LLM Parameters
```python
temperature=0.7      # Balanced creativity + consistency
top_p=0.9           # Diverse but focused responses
top_k=40            # Consider top 40 tokens
max_output_tokens=150 # Force brevity for voice
```

### RAG Parameters
```python
top_k=3             # Retrieve 3 most similar entries
similarity_threshold=0.6  # Relevance filter
```

### Chart Calculation
```python
ayanamsa="Lahiri"   # Vedic sidereal system
house_system="Equal" # Equal house division
```

---

## 🔍 Debugging & Logging

All stages log their activity:

```
[LLM] Building system prompt for user: "marriage question"
[LLM] Chart insights extracted: 7 planetary entries
[RAG] Querying: "marriage 7th house venus saturn"
[RAG] Retrieved 3 entries with similarity > 0.6
[LLM] Loaded astro_rules.json: 47 rules
[LLM] Calling Claude: prompt tokens = 1240
[LLM] Response received: 156 characters
[LLM] Houses detected: [7], Planets detected: ['Venus', 'Saturn']
[TTS] Generating audio for: "Your Venus sits..."
[TTS] Audio generated: 2840 bytes
```

---

## 🚀 Optimization Tips

1. **Cache Chart Insights** - Don't recalculate if chart unchanged
2. **Pre-index RAG** - Index knowledge base once on startup
3. **Load astro_rules.json** - Cache in memory, not disk access
4. **Batch Similar Questions** - Group similar queries for efficiency
5. **Use Claude's Streaming** - Stream tokens as they arrive

---

## Summary

Acharya's intelligence comes from:
1. **Accurate Chart Calculation** (Vedic sidereal)
2. **Rich Knowledge Base** (RAG + astro_rules.json)
3. **Conversational AI** (Claude with domain-specific prompt)
4. **Real-time House Detection** (Frontend visualization)
5. **Voice I/O** (Seamless audio experience)

This creates a **solution-driven, personalized, Vedically-grounded Acharya** that understands each user's unique chart and provides actionable guidance! 🌟
