import logging
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from uuid import UUID
from app.schemas.game_schemas import GameSession, ConversationEntry
from app.services.deepgram_service import deepgram_service 
# We only need the main function now, the regex helpers are gone
from app.services.llm_service import get_astro_response

logger = logging.getLogger(__name__)

class GameSessionManager:
    """
    Manages the entire lifecycle of a single game session over a WebSocket.
    Now optimized for RAG + Structured Astro Output.
    """

    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.session: GameSession | None = None
        self.transcriber = None
        self.is_active = True

    def _clean_text_for_tts(self, text: str) -> str:
        """Removes markdown or stray characters for smoother speech."""
        cleaned_text = text.replace("*", "").replace("#", "").replace("`", "")
        return cleaned_text
    
    async def _load_session_data(self) -> bool:
        # Note: In the new flow, session is injected via game.py -> manager.session = ...
        # But if we need to reload from DB later, logic goes here.
        if self.session:
            return True
        return False

    async def _send_json(self, data: dict):
        if self.is_active:
            try:
                await self.websocket.send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"[{self.session_id}] Error sending JSON: {e}")

    async def _stream_ai_audio(self, text: str):
        """Stream complete AI audio to frontend."""
        if not self.is_active:
            return
        
        cleaned_text = self._clean_text_for_tts(text)
        
        # Signal audio is starting
        await self._send_json({"status": "ai_speaking"})
        
        try:
            # Stream audio chunks from TTS
            async for audio_chunk in deepgram_service.text_to_speech_stream(cleaned_text, "male"):
                if self.is_active:
                    await self.websocket.send_bytes(audio_chunk)
            
            # Signal audio is done
            await self._send_json({"status": "ai_finished_speaking"})
            
        except Exception as e:
            logger.error(f"[{self.session_id}] Audio streaming error: {e}")
            await self._send_json({"status": "error", "message": "Audio failed"})

    async def _start_stt(self):
        """Start Deepgram real-time transcription."""
        logger.info(f"[{self.session_id}] Starting STT...")
        self.transcriber = deepgram_service.get_live_transcriber()
        self.transcriber.start()

    async def _handle_user_speech(self, audio_chunk: bytes):
        """Send audio data to the transcriber."""
        if self.transcriber and self.transcriber._is_active:
            try:
                await asyncio.to_thread(self.transcriber.send, audio_chunk)
            except Exception as e:
                logger.error(f"[{self.session_id}] STT Send Error: {e}")

    async def _stop_stt_and_process_transcript(self):
        """Stop STT and process the final transcript."""
        if not self.transcriber:
            return

        logger.info(f"[{self.session_id}] Stopping STT...")
        try:
            transcript = await asyncio.to_thread(self.transcriber.stop)
            self.transcriber = None

            if transcript and isinstance(transcript, str) and transcript.strip():
                await self._process_user_transcript(transcript)
            else:
                await self._send_json({"status": "ai_finished_speaking"}) # Reset state
        except Exception as e:
            logger.error(f"[{self.session_id}] STT Stop Error: {e}")
            self.transcriber = None

    async def _process_user_transcript(self, text: str):
        """
        The Core Logic:
        1. Receive User Text
        2. Ask LLM (RAG + Math)
        3. Handle Structured Response (Speech + UI Commands)
        """
        if not self.session:
            logger.error("No session found during processing")
            return
            
        logger.info(f"[{self.session_id}] User said: '{text}'")
        await self._send_json({"status": "user_response_text", "text": text})
        
        # Add user message to history
        self.session.conversation_history.append(ConversationEntry(role="user", message=text))
        await self._send_json({"status": "ai_thinking"})

        try:
            # --- 1. CALL THE NEW LLM SERVICE ---
            # This now returns a DICT, not a string
            response_data = await asyncio.to_thread(get_astro_response, self.session)
            
            # Handle case where LLM might fail and return a fallback string or dict
            if isinstance(response_data, str):
                # Fallback if something went wrong and it returned raw string
                speech_text = response_data
                ui_data = {}
            else:
                speech_text = response_data.get("speech", "I am meditating on your chart.")
                ui_data = response_data.get("ui", {})

            logger.info(f"[{self.session_id}] AI Speech: '{speech_text[:50]}...'")
            
            # --- 2. HANDLE UI COMMANDS (The "Cool Stuff") ---
            # We send a consolidated update event
            if ui_data:
                await self._send_json({
                    "status": "astro_ui_update",
                    "highlights": {
                        "houses": ui_data.get("highlight_houses", []),
                        "planets": ui_data.get("highlight_planets", [])
                    },
                    "time_travel": ui_data.get("transit_date"), # YYYY-MM-DD
                    "remedy": ui_data.get("suggested_remedy")
                })
                logger.info(f"[{self.session_id}] UI Update Sent: {ui_data}")

            # --- 3. STREAM AUDIO ---
            self.session.conversation_history.append(ConversationEntry(role="ai", message=speech_text))
            
            # Send text for chat bubble
            await self._send_json({"status": "ai_response_text", "text": speech_text})
            
            # Stream audio
            await self._stream_ai_audio(speech_text)

        except Exception as e:
            logger.error(f"[{self.session_id}] AI processing error: {e}", exc_info=True)
            await self._send_json({"status": "error", "message": "The stars are cloudy today."})

    async def _handle_end_game(self):
        logger.info(f"[{self.session_id}] User ended the game.")
        await self._send_json({"status": "game_ended"})
        self.is_active = False

    async def run(self):
        """Main entry point for the game session."""
        if not self.session:
            logger.error("Session object not injected into Manager")
            await self.websocket.close(code=1008)
            return
        
        logger.info(f"[{self.session_id}] Game session started")
        
        # 1. Send Chart Data immediately (for rendering Skyfield)
        if self.session.chart_data:
            await self._send_json({"status": "chart_data", "chart": self.session.chart_data})
        
        # 2. Initial Greeting
        # We can pull from history or generate a personalized welcome
        if self.session.conversation_history:
            greeting = self.session.conversation_history[-1].message
        else:
            # Extract Name, Ascendant, and Moon Sign
            name = self.session.chart_data.get('meta', {}).get('name', 'Seeker')
            asc_sign = self.session.chart_data.get('ascendant', {}).get('sign', 'Unknown')
            moon_sign = self.session.chart_data.get('planets', {}).get('moon', {}).get('sign', 'Unknown')
            
            # Construct a personalized Vedic greeting
            greeting = (
                f"Namaste {name}. "
                f"You are a {asc_sign} Ascendant with Moon in {moon_sign}. "
                f"The cosmos is ready to reveal your path. What do you seek?"
            )
            
            logger.info(f"[{self.session_id}] Generated greeting: {greeting}")
            self.session.conversation_history.append(ConversationEntry(role="ai", message=greeting))
        
        await self._send_json({"status": "ai_response_text", "text": greeting})
        await self._stream_ai_audio(greeting)

        # 3. Main Loop
        while self.is_active:
            try:
                data = await self.websocket.receive()
                
                if "text" in data:
                    msg = json.loads(data["text"])
                    action = msg.get("action")
                    
                    if action == "start_speaking":
                        await self._start_stt()
                    elif action == "stop_speaking":
                        await self._stop_stt_and_process_transcript()
                    elif action == "end_game":
                        await self._handle_end_game()
                
                elif "bytes" in data:
                    await self._handle_user_speech(data["bytes"])
                        
            except WebSocketDisconnect:
                logger.info(f"[{self.session_id}] WebSocket disconnected")
                self.is_active = False
            except Exception as e:
                logger.error(f"[{self.session_id}] Loop Error: {e}")
                self.is_active = False
        
        # Cleanup
        if self.transcriber:
            try:
                self.transcriber.stop()
            except:
                pass