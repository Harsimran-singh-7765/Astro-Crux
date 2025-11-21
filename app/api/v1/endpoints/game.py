from fastapi import APIRouter, WebSocket
from pydantic import BaseModel
import uuid
from datetime import datetime
from app.schemas.game_schemas import GameSession
from app.services.vedic_calculator import calculate_vedic_chart, get_location_coordinates
from app.services.game_session_manager import GameSessionManager

router = APIRouter()
active_sessions = {}

class StartSessionRequest(BaseModel):
    name: str
    date: str
    time: str
    location: str

@router.post("/start")
async def start_session(request: StartSessionRequest):
    birth_dt = datetime.strptime(f"{request.date} {request.time}", "%Y-%m-%d %H:%M")
    lat, lon, tz = get_location_coordinates(request.location)
    chart_data = calculate_vedic_chart(birth_dt, lat, lon, tz)
    chart_data['meta']['name'] = request.name

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

    await websocket.accept()  # <-- accept HERE only
    session = active_sessions[session_id]
    manager = GameSessionManager(websocket, session_id)
    manager.session = session
    await manager.run()
