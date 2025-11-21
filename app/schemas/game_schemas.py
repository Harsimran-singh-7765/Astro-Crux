from pydantic import BaseModel
from typing import List, Optional, Literal
from uuid import UUID

class BirthDetails(BaseModel):
    name: str
    date: str  # "YYYY-MM-DD"
    time: str  # "HH:MM"
    location: str # "Mumbai", "Delhi"

class ConversationEntry(BaseModel):
    role: Literal["user", "ai"]
    message: str

class GameSession(BaseModel):
    session_id: str
    user_id: str
    # Instead of a scenario ID, we store the calculated chart
    chart_data: dict 
    conversation_history: List[ConversationEntry] = []