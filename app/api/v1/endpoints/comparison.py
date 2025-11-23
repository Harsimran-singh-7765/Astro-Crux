from fastapi import APIRouter, WebSocket
from pydantic import BaseModel
import uuid
from app.services.vedic_calculator import calculate_vedic_chart, get_location_coordinates
from app.services.comparison_session_manager import ComparisonSessionManager
from datetime import datetime

router = APIRouter()
active_comparison_sessions = {}

class PersonData(BaseModel):
    name: str
    date: str
    time: str
    location: str

class StartComparisonRequest(BaseModel):
    person1: PersonData
    person2: PersonData

@router.post("/start")
async def start_comparison(request: StartComparisonRequest):
    """
    Start a new Kundli comparison session.
    Pre-calculates both charts and returns session ID.
    """
    try:
        # Calculate both charts
        birth_dt1 = datetime.strptime(f"{request.person1.date} {request.person1.time}", "%Y-%m-%d %H:%M")
        lat1, lon1, tz1 = get_location_coordinates(request.person1.location)
        chart1 = calculate_vedic_chart(birth_dt1, lat1, lon1, tz1)
        chart1['meta']['name'] = request.person1.name

        birth_dt2 = datetime.strptime(f"{request.person2.date} {request.person2.time}", "%Y-%m-%d %H:%M")
        lat2, lon2, tz2 = get_location_coordinates(request.person2.location)
        chart2 = calculate_vedic_chart(birth_dt2, lat2, lon2, tz2)
        chart2['meta']['name'] = request.person2.name

        # Create session
        session_id = str(uuid.uuid4())
        active_comparison_sessions[session_id] = {
            "chart1": chart1,
            "chart2": chart2,
            "person1_name": request.person1.name,
            "person2_name": request.person2.name
        }
        
        return {
            "session_id": session_id,
            "message": "Charts calculated. Ready for comparison.",
            "chart1": chart1,
            "chart2": chart2
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to calculate charts"
        }

@router.websocket("/ws/{session_id}")
async def websocket_comparison_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for streaming comparison analysis."""
    if session_id not in active_comparison_sessions:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    session_data = active_comparison_sessions[session_id]
    
    manager = ComparisonSessionManager(websocket, session_id)
    
    # Create a mock message with the pre-calculated data
    comparison_message = {
        "person1": {
            "name": session_data["person1_name"],
            "chart": session_data["chart1"]
        },
        "person2": {
            "name": session_data["person2_name"],
            "chart": session_data["chart2"]
        }
    }
    
    # Store for manager to use
    manager.comparison_data = comparison_message
    await manager.run()
