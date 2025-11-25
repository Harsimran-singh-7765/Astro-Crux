## Astro-Crux: The AI Vedic Astrologer
> "Where NASA Data meets Ancient Wisdom."
> A real-time, voice-interactive AI Astrologer that calculates planetary positions mathematically and interprets them using Ancient Vedic texts (BPHS) via RAG.
> 
## What is Astro-Crux?
Astro-Crux is not just a chatbot; it is a Computational Astrologer.
Unlike standard AI that hallucinates predictions, Astro-Crux is grounded in a Tri-Layer Truth System:
 * The Math: Uses Skyfield (NASA JPL Data) to calculate the exact Sidereal (Lahiri) positions of planets.
 * The Knowledge: Uses RAG (Retrieval Augmented Generation) with HyDE to consult the Brihat Parashara Hora Shastra (BPHS) in real-time.
 * The Experience: Highlights specific houses on the UI while speaking, creating a seamless Audio-Visual experience.


## Key Features (Current Implementation)
🧠 1. The "Sage" Brain (HyDE RAG)
We don't just search for keywords. We use Hypothetical Document Embeddings (HyDE).
 * User: "Why is my career stuck?"
 * AI Hallucination: Generates a theoretical Vedic rule about the 10th house.
 * Vector Search: Uses that theory to find the exact verse in the BPHS book.
 * Result: Precise, book-backed answers.
 2. NASA-Grade Math
 * Calculates Lahiri Ayanamsa for Vedic accuracy.
 * Determines precise House Cusps and Planetary Degrees.
 * No random guesses; if the AI says "Sun is in Aries," it is astronomically correct.
 3. Real-Time Voice Interaction
 * Speech-to-Text: Deepgram Nova-2 for instant transcription.
 * Text-to-Speech: Low-latency streaming voice that sounds like a calm, wise Acharya.
 * Fillers: Handles silence intelligently to keep the conversation flowing.
 4. Visual Intelligence (Backend-Driven UI)
The backend sends Structured JSON commands alongside the audio.
 * If Acharya says: "Your 7th House is afflicted..."
 * The UI automatically Glows/Highlights the 7th House on the chart.
 Architecture Flow
graph TD
    User((User Voice)) --> |WebSocket| STT[Deepgram STT]
    STT --> |Transcript| Manager[Game Session Manager]
    
    subgraph "The Knowledge Engine"
        Manager --> |Date/Time| Math[Vedic Calculator (Skyfield)]
        Math --> |Planetary Positions| LLM
        
        Manager --> |Query| HyDE[HyDE Generator]
        HyDE --> |Hypothetical Answer| VectorDB[(ChromaDB - BPHS)]
        VectorDB --> |Ancient Verses| LLM
    end
    
    subgraph "The Brain"
        LLM[Gemini 2.0 Flash] --> |Analysis| Response
    end
    
    Response --> |"Speech"| TTS[Deepgram TTS] --> Audio
    Response --> |"UI Action"| Frontend[Visual Highlight]

🛠️ Tech Stack
 * Backend: Python, FastAPI, Uvicorn, WebSockets.
 * AI Model: Google Gemini 2.0 Flash (via google-genai SDK).
 * Vector Database: ChromaDB (Persistent local storage).
 * Embeddings: all-MiniLM-L6-v2 (Sentence Transformers).
 * Astronomy: skyfield, pytz.
 * Audio: Deepgram API (Streaming).
📂 Project Structure
astro-crux/
├── app/
│   ├── services/
│   │   ├── astro_engine.py       # The Math (Skyfield/Vedic Calc)
│   │   ├── rag_service.py        # The Brain (ChromaDB + HyDE)
│   │   ├── llm_service.py        # The Personality (Gemini Prompt)
│   │   └── game_session_manager.py # The Conductor (WebSocket Logic)
│   ├── api/v1/endpoints/game.py  # WebSocket Endpoint
│   └── main.py                   # App Entry Point
├── data/
│   └── books/
│       └── bphs.txt              # The Ancient Text Source
├── scripts/
│   └── ingest_books.py           # Script to vectorize books
└── requirements.txt

 Setup & Installation
1. Clone & Environment
git clone https://github.com/your-username/astro-crux.git
cd astro-crux
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

2. Install Dependencies
Note: We use the CPU version of Torch to save space.
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

3. Set up Environment Variables
Create a .env file:
GOOGLE_API_KEY="your_gemini_key"
DEEPGRAM_API_KEY="your_deepgram_key"
MONGODB_URI="your_mongo_url"

4. Ingest the Knowledge Base (Crucial!)
This step reads bphs.txt and creates the Vector Database.
python scripts/ingest_books.py

Wait for "✅ Library Ready!" message.
5. Run the Server
uvicorn app.main:app --reload

Frontend running on localhost:3000 (or similar).
🧪 Testing
To test the RAG brain without the frontend:
python scripts/test_rag.py

This will simulate a question like "What happens if Sun is in 1st House?" and show the retrieved text from the book.
🔮 Future Roadmap
 * [ ] Dasha System: Integrating Vimshottari Dasha for timing predictions.
 * [ ] Remedial Mode: Auto-playing Mantra audio when a remedy is suggested.
 * [ ] Kundli Matching: Comparing two charts for relationship analysis.
 * [ ] PDF Export: Generating a downloadable "Divine Report" after the session.

