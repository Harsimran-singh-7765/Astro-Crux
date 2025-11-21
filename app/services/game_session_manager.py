import logging
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from uuid import UUID
from app.schemas.game_schemas import GameSession, ConversationEntry
from app.services.deepgram_service import deepgram_service 
from app.services.llm_service import get_astro_response, extract_focus_signal, clean_response_text

logger = logging.getLogger(__name__)

class GameSessionManager:
    """
    Manages the entire lifecycle of a single game session over a WebSocket.
    """

    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.session: GameSession | None = None
        self.transcriber = None
        self.is_active = True

    def _clean_text_for_tts(self, text: str) -> str:
        """Removes characters that should not be spoken by TTS."""
        logger.info(f"[{self.session_id}] Cleaning text for TTS...")
        cleaned_text = text.replace("*", "").replace("#", "")
        logger.info(f"[{self.session_id}] Cleaned text: '{cleaned_text[:60]}...'")
        return cleaned_text
    
    async def _load_session_data(self, retries=3, delay=0.5) -> bool:
        logger.info(f"[{self.session_id}] Loading session data...")
        if self.session:
            logger.info(f"[{self.session_id}] Session already loaded")
            return True
        logger.error(f"[{self.session_id}] Session not provided.")
        return False

    async def _send_json(self, data: dict):
        if self.is_active:
            logger.debug(f"[{self.session_id}] Sending JSON to client: {json.dumps(data)}")
            await self.websocket.send_text(json.dumps(data))

    async def _generate_audio_for_message(self, text: str) -> bytes:
        """
        Generates complete audio for a single message.
        Returns audio as bytes.
        """
        logger.info(f"[{self.session_id}] Generating audio for: '{text[:50]}...'")
        audio_chunks = []
        
        try:
            async for chunk in deepgram_service.text_to_speech_stream(text, "male"):
                audio_chunks.append(chunk)
            
            # Combine all chunks into single audio blob
            full_audio = b''.join(audio_chunks)
            logger.info(f"[{self.session_id}] Generated {len(full_audio)} bytes of audio")
            return full_audio
            
        except Exception as e:
            logger.error(f"[{self.session_id}] Audio generation error: {e}")
            return b''

    async def _stream_ai_audio(self, text: str):
        """Stream complete AI audio to frontend."""
        logger.info(f"[{self.session_id}] Streaming audio for: '{text[:60]}...'")
        
        if not self.is_active:
            return
        
        cleaned_text = self._clean_text_for_tts(text)
        
        # Signal audio is starting
        await self._send_json({"status": "ai_speaking"})
        
        try:
            # Stream audio chunks from TTS
            async for audio_chunk in deepgram_service.text_to_speech_stream(cleaned_text, "male"):
                if self.is_active:
                    logger.debug(f"[{self.session_id}] Sending audio chunk: {len(audio_chunk)} bytes")
                    await self.websocket.send_bytes(audio_chunk)
            
            # Signal audio is done
            await self._send_json({"status": "ai_finished_speaking"})
            logger.info(f"[{self.session_id}] ✅ Audio streaming complete")
            
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
        if not self.transcriber:
            logger.warning(f"[{self.session_id}] Transcriber not initialized, ignoring audio chunk")
            return
            
        if not self.transcriber._is_active:
            logger.debug(f"[{self.session_id}] Transcriber inactive, ignoring audio chunk")
            return
            
        try:
            logger.debug(f"[{self.session_id}] Sending audio chunk to STT: {len(audio_chunk)} bytes")
            await asyncio.to_thread(self.transcriber.send, audio_chunk)
        except Exception as e:
            logger.error(f"[{self.session_id}] Error sending audio to STT: {e}", exc_info=True)

    async def _stop_stt_and_process_transcript(self):
        """Stop STT and process the final transcript."""
        if not self.transcriber:
            logger.warning(f"[{self.session_id}] Transcriber not initialized")
            return

        logger.info(f"[{self.session_id}] Stopping STT...")
        
        try:
            # Stop the transcriber in a thread (it's synchronous)
            transcript = await asyncio.to_thread(self.transcriber.stop)
            self.transcriber = None

            logger.info(f"[{self.session_id}] Raw transcript from Deepgram: '{transcript}'")

            if transcript and isinstance(transcript, str) and transcript.strip():
                logger.info(f"[{self.session_id}] Valid transcript received, processing...")
                await self._process_user_transcript(transcript)
            else:
                logger.warning(f"[{self.session_id}] Empty or invalid transcript received.")
                await self._send_json({"status": "ai_finished_speaking"})
        except Exception as e:
            logger.error(f"[{self.session_id}] Error stopping STT: {e}", exc_info=True)
            self.transcriber = None
            await self._send_json({"status": "error", "message": "STT failed"})

    async def _process_user_transcript(self, text: str):
        if not self.session:
            logger.error(f"[{self.session_id}] Error: _process_user_transcript called with no session.")
            return
            
        logger.info(f"[{self.session_id}] User said: '{text}'")
        
        await self._send_json({"status": "user_response_text", "text": text})

        self.session.conversation_history.append(ConversationEntry(role="user", message=text))
        await self._send_json({"status": "ai_thinking"})

        try:
            response = await asyncio.to_thread(
                get_astro_response, self.session
            )
            logger.info(f"[{self.session_id}] AI response received from LLM: '{response}'")
            
            self.session.conversation_history.append(ConversationEntry(role="ai", message=response))
            
            # Extract focus signal BEFORE cleaning
            focus_signal = extract_focus_signal(response)
            if focus_signal:
                logger.info(f"[{self.session_id}] ✨ Focus signal detected: {focus_signal}")
                await self._send_json({"status": "ai_focus", "focus": focus_signal})
            
            # Clean response for TTS (removes focus tags)
            clean_response = clean_response_text(response)
            
            # Send clean response (without focus tags) to UI for display
            await self._send_json({"status": "ai_response_text", "text": clean_response})
            
            # Stream clean audio (without focus tag artifacts)
            await self._stream_ai_audio(clean_response)

        except Exception as e:
            logger.error(f"[{self.session_id}] AI response error: {e}", exc_info=True)
            await self._send_json({"status": "error", "message": "AI processing failed"})

    async def _handle_end_game(self):
        if not self.session:
             logger.error(f"[{self.session_id}] Error: _handle_end_game called with no session.")
             return
        logger.info(f"[{self.session_id}] User ended the game.")
        await self._send_json({"status": "game_ended"})
        self.is_active = False

    async def run(self):
        """Main entry point for the game session."""
        if not self.session:
            await self.websocket.close(code=1008, reason="Invalid session")
            self.is_active = False
            return
        
        logger.info(f"[{self.session_id}] Game session started")
        
        # Send chart data to frontend
        if self.session.chart_data:
            logger.info(f"[{self.session_id}] Sending chart data to frontend")
            await self._send_json({"status": "chart_data", "chart": self.session.chart_data})
        
        # Get initial greeting from session or generate one
        if self.session.conversation_history:
            initial_message = self.session.conversation_history[0].message
        else:
            name = self.session.chart_data.get('meta', {}).get('name', 'Seeker')
            asc = self.session.chart_data.get('ascendant', {}).get('sign', 'Unknown')
            initial_message = f"Namaste {name}. You are a {asc} ascendant. Ask anything."
            self.session.conversation_history.append(ConversationEntry(role="ai", message=initial_message))
        
        # Send initial greeting
        await self._send_json({"status": "ai_response_text", "text": initial_message})
        await self._stream_ai_audio(initial_message)

        while self.is_active:
            try:
                data = await self.websocket.receive()
                logger.debug(f"[{self.session_id}] Received data: {list(data.keys())}")
                
                # Handle text messages (JSON)
                if "text" in data:
                    text_data = data.get("text")
                    if text_data:
                        logger.debug(f"[{self.session_id}] Received JSON: {text_data}")
                        msg = json.loads(text_data)
                        action = msg.get("action")
                        
                        if action == "start_speaking":
                            logger.info(f"[{self.session_id}] ▶️ START SPEAKING - Initializing STT")
                            await self._start_stt()
                            
                        elif action == "stop_speaking":
                            logger.info(f"[{self.session_id}] ⏹️ STOP SPEAKING - Processing transcript")
                            await self._stop_stt_and_process_transcript()
                            
                        elif action == "end_game":
                            logger.info(f"[{self.session_id}] 🏁 END GAME")
                            await self._handle_end_game()
                
                # Handle binary messages (audio)
                elif "bytes" in data:
                    audio_data = data.get("bytes")
                    if audio_data:
                        logger.debug(f"[{self.session_id}] 🎤 Received audio chunk: {len(audio_data)} bytes")
                        await self._handle_user_speech(audio_data)
                        
            except WebSocketDisconnect:
                logger.info(f"[{self.session_id}] ❌ WebSocket disconnected")
                self.is_active = False
            except json.JSONDecodeError as e:
                logger.error(f"[{self.session_id}] JSON decode error: {e}")
            except Exception as e:
                logger.error(f"[{self.session_id}] ❌ Unhandled error in main loop: {e}", exc_info=True)
                self.is_active = False
        
        if self.transcriber:
            try:
                if hasattr(self.transcriber, '_is_active') and self.transcriber._is_active:
                    self.transcriber.stop()
            except Exception as e:
                logger.error(f"[{self.session_id}] Error during cleanup: {e}")
            finally:
                self.transcriber = None
        logger.info(f"[{self.session_id}] Game session ended.")
