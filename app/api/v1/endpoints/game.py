"""
Fixed FastAPI Router for Vedic Astrology Game
Resolves import issues and improves logic
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import Dict, Optional
import logging

# Assuming your project structure, adjust paths as needed
# If vedic_calculator is in the same directory, use relative import
try:
    from app.services.vedic_calculator import calculate_vedic_chart, get_geo_coords
except ImportError:
    # Fallback for testing or different structure
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from app.services.vedic_calculator import calculate_vedic_chart, get_geo_coords

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple in-memory session storage (use Redis/DB for production)
active_sessions: Dict[str, dict] = {}


class StartSessionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')  # YYYY-MM-DD
    time: str = Field(..., pattern=r'^\d{2}:\d{2}$')  # HH:MM
    location: str = Field(..., min_length=1, max_length=200)


class SessionResponse(BaseModel):
    session_id: str
    message: str
    chart_preview: Optional[dict] = None


@router.post("/start", response_model=SessionResponse)
async def start_session(request: StartSessionRequest):
    """
    Initialize a new astrology reading session with user's birth details.
    """
    try:
        # 1. Parse datetime
        birth_dt = datetime.strptime(f"{request.date} {request.time}", "%Y-%m-%d %H:%M")
        
        # 2. Calculate Vedic chart using the documented function signature
        chart_data = calculate_vedic_chart(request.location, birth_dt)
        
        # 3. Check for calculation errors
        if 'error' in chart_data:
            raise HTTPException(status_code=400, detail=f"Chart calculation failed: {chart_data['error']}")
        
        # 4. Add user metadata
        chart_data['meta']['name'] = request.name
        chart_data['meta']['birth_date'] = request.date
        chart_data['meta']['birth_time'] = request.time
        
        # 5. Create session
        session_id = str(uuid.uuid4())
        session_data = {
            'session_id': session_id,
            'user_name': request.name,
            'chart_data': chart_data,
            'conversation_history': [],
            'created_at': datetime.now().isoformat()
        }
        
        active_sessions[session_id] = session_data
        
        logger.info(f"Created session {session_id} for {request.name}")
        
        # 6. Return response with chart preview
        return SessionResponse(
            session_id=session_id,
            message=f"Chart ready for {request.name}",
            chart_preview={
                'ascendant': chart_data['ascendant']['sign'],
                'location': chart_data['meta']['location'],
                'planet_count': len(chart_data['planets'])
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time format: {str(e)}")
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Retrieve session data for validation/debugging.
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    return {
        'session_id': session_id,
        'user_name': session['user_name'],
        'created_at': session['created_at'],
        'chart_summary': {
            'ascendant': session['chart_data']['ascendant']['sign'],
            'planets': list(session['chart_data']['planets'].keys())
        }
    }


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time conversation with astrology assistant.
    """
    # 1. Validate session exists
    if session_id not in active_sessions:
        await websocket.close(code=1008, reason="Session not found")
        return
    
    # 2. Accept connection
    await websocket.accept()
    logger.info(f"WebSocket connected for session {session_id}")
    
    session_data = active_sessions[session_id]
    
    try:
        # 3. Send welcome message with chart summary
        await websocket.send_json({
            'type': 'welcome',
            'message': f"Welcome {session_data['user_name']}! Your chart is ready.",
            'chart_summary': {
                'ascendant': session_data['chart_data']['ascendant']['sign'],
                'planets': {
                    planet: data['sign'] 
                    for planet, data in session_data['chart_data']['planets'].items()
                }
            }
        })
        
        # 4. Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                user_message = data.get('content', '')
                
                # Store in conversation history
                session_data['conversation_history'].append({
                    'role': 'user',
                    'content': user_message,
                    'timestamp': datetime.now().isoformat()
                })
                
                # TODO: Integrate with your AI/LLM service here
                # For now, send a simple echo response
                response = await process_astrology_query(
                    user_message, 
                    session_data['chart_data']
                )
                
                # Store assistant response
                session_data['conversation_history'].append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Send response back
                await websocket.send_json({
                    'type': 'message',
                    'content': response
                })
            
            elif message_type == 'get_chart':
                # Send full chart data on request
                await websocket.send_json({
                    'type': 'chart_data',
                    'data': session_data['chart_data']
                })
            
            elif message_type == 'ping':
                await websocket.send_json({'type': 'pong'})
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        await websocket.close(code=1011, reason="Internal error")
    finally:
        # Optionally clean up session after disconnect
        # del active_sessions[session_id]
        pass


async def process_astrology_query(query: str, chart_data: dict) -> str:
    """
    Process user's astrology question using chart data.
    TODO: Integrate with your AI/LLM service (Claude API, etc.)
    """
    # Simple placeholder logic - replace with actual AI integration
    query_lower = query.lower()
    
    if 'ascendant' in query_lower or 'rising' in query_lower:
        asc = chart_data['ascendant']
        return f"Your ascendant (rising sign) is {asc['sign']} at {asc['formatted']}. This represents your outer personality and how others perceive you."
    
    elif 'sun' in query_lower:
        sun = chart_data['planets'].get('Sun', {})
        return f"Your Sun is in {sun['sign']} in the {sun['house']}th house. The Sun represents your core identity and life purpose."
    
    elif 'moon' in query_lower:
        moon = chart_data['planets'].get('Moon', {})
        return f"Your Moon is in {moon['sign']} in the {moon['house']}th house. The Moon governs your emotions and inner self."
    
    else:
        # Generic response with chart overview
        planets_list = ', '.join([f"{p} in {d['sign']}" for p, d in chart_data['planets'].items()])
        return f"I can help interpret your Vedic chart. You have: {planets_list}. What would you like to know more about?"


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Clean up a session (useful for testing/admin).
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del active_sessions[session_id]
    return {"message": "Session deleted successfully"}


# Health check endpoint
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions)
    }