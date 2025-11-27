"""
Complete Game Endpoint - Connects Deepgram + RAG + Gemini + Vedic Calculator
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import Dict, Optional
import logging

from app.services.vedic_calculator import calculate_vedic_chart
from app.services.game_session_manager import GameSessionManager
from app.schemas.game_schemas import GameSession

logger = logging.getLogger(__name__)

router = APIRouter()
active_sessions: Dict[str, GameSession] = {}


class StartSessionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    time: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    location: str = Field(..., min_length=1, max_length=200)


@router.post("/start")
async def start_session(request: StartSessionRequest):
    """
    Initialize a new astrology reading session.
    Calculates Vedic chart and creates GameSession object.
    """
    try:
        logger.info(f"📥 Start request: name={request.name}, date={request.date}, time={request.time}, location={request.location}")
        
        # 1. Parse datetime
        birth_dt = datetime.strptime(f"{request.date} {request.time}", "%Y-%m-%d %H:%M")
        logger.info(f"✅ DateTime parsed: {birth_dt}")
        
        # 2. Calculate Vedic chart
        chart_data = calculate_vedic_chart(request.location, birth_dt)
        
        if 'error' in chart_data:
            raise HTTPException(status_code=400, detail=f"Chart calculation failed: {chart_data['error']}")
        
        logger.info(f"✅ Chart calculated successfully")
        
        # 3. Add user metadata to chart
        chart_data['meta']['name'] = request.name
        chart_data['meta']['birth_date'] = request.date
        chart_data['meta']['birth_time'] = request.time
        
        # 4. Create GameSession object (your existing schema)
        session_id = str(uuid.uuid4())
        session = GameSession(
            session_id=session_id,
            user_id=request.name,  # Or generate proper user_id
            chart_data=chart_data,
            conversation_history=[]
        )
        
        # 5. Store session
        active_sessions[session_id] = session
        logger.info(f"✅ Session created: {session_id}")
        
        # 6. Return response
        return {
            "session_id": session_id,
            "message": f"Chart ready for {request.name}",
            "chart_preview": {
                'ascendant': chart_data['ascendant']['sign'],
                'location': chart_data['meta']['location'],
                'planet_count': len(chart_data['planets'])
            }
        }
        
    except ValueError as e:
        logger.error(f"❌ ValueError: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid date/time format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Session creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint using your GameSessionManager.
    Handles Deepgram STT/TTS, Gemini AI, and RAG.
    """
    # 1. Validate session exists
    if session_id not in active_sessions:
        logger.error(f"❌ Session {session_id} not found")
        await websocket.close(code=1008, reason="Session not found")
        return
    
    # 2. Accept WebSocket connection
    await websocket.accept()
    logger.info(f"🟢 WebSocket connected for session {session_id}")
    
    # 3. Get session and create manager
    session = active_sessions[session_id]
    manager = GameSessionManager(websocket, session_id)
    
    # 4. Inject session into manager (as per your game_session_manager.py logic)
    manager.session = session
    
    # 5. Run the game session (handles everything: STT, LLM, TTS, UI updates)
    try:
        await manager.run()
    except WebSocketDisconnect:
        logger.info(f"🔴 WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for session {session_id}: {e}", exc_info=True)
    finally:
        # Cleanup - optionally keep session for reconnection
        # del active_sessions[session_id]
        logger.info(f"🧹 Cleaned up session {session_id}")


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Retrieve session data for debugging."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    return {
        'session_id': session_id,
        'user_id': session.user_id,
        'conversation_length': len(session.conversation_history),
        'chart_summary': {
            'ascendant': session.chart_data['ascendant']['sign'],
            'name': session.chart_data['meta'].get('name', 'Unknown')
        }
    }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Clean up a session."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del active_sessions[session_id]
    logger.info(f"🗑️ Deleted session {session_id}")
    return {"message": "Session deleted successfully"}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "services": {
            "deepgram": "enabled",
            "gemini": "enabled",
            "rag": "hyde-based",
            "vedic_calculator": "skyfield"
        }
    }


@router.post("/debug-start")
async def debug_start(data: dict):
    """Debug endpoint to see raw request data."""
    logger.info(f"🔍 DEBUG - Received: {data}")
    return {"received": data}