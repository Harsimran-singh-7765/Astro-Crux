from fastapi import APIRouter, WebSocket, HTTPException
from pydantic import BaseModel
import uuid
from app.schemas.game_schemas import GameSession
from app.services.game_session_manager import GameSessionManager

# --- CHANGE 1: Import the new Engine Singleton ---
# Ensure astroengine.py is inside app/services/
from app.services.astro_engine import astro_engine 

router = APIRouter()
active_sessions = {}

class StartSessionRequest(BaseModel):
    name: str
    date: str
    time: str
    location: str

@router.post("/start")
async def start_session(request: StartSessionRequest):
    """
    Starts a game session using the new AstroEngine.
    """
    # --- CHANGE 2: Simplified Logic ---
    # We no longer need to manually get lat/lon or parse datetime here.
    # The astro_engine handles OpenStreetMap lookup and Timezone conversion.
    
    chart_data = astro_engine.generate_vedic_chart(
        date_str=request.date,
        time_str=request.time,
        location_str=request.location
    )

    # Check if the engine reported an error
    if "error" in chart_data:
        raise HTTPException(status_code=400, detail="Could not calculate chart. Please check the location.")

    # Add the user's name to the metadata
    chart_data['meta']['name'] = request.name

    # Create the session (Same as before)
    session_id = str(uuid.uuid4())
    session = GameSession(
        session_id=session_id,
        user_id="user",
        chart_data=chart_data,
        conversation_history=[]
    )
    active_sessions[session_id] = session
    
    return {"session_id": session_id, "message": "Chart Ready"}

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    if session_id not in active_sessions:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    session = active_sessions[session_id]
    
    # Initialize the Manager
    manager = GameSessionManager(websocket, session_id)
    manager.session = session
    
    await manager.run()