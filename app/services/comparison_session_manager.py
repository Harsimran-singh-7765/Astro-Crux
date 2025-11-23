"""
Comparison Session Manager
Manages WebSocket connections for Kundli Comparerer feature.
"""

import logging
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.services.vedic_calculator import calculate_vedic_chart
from app.services.deepgram_service import deepgram_service
from app.services.kundli_comparerer import get_kundli_comparison

logger = logging.getLogger(__name__)

class ComparisonSessionManager:
    """
    Manages a Kundli Comparison session over WebSocket.
    Calculates both charts and generates compatibility analysis.
    """

    def __init__(self, websocket: WebSocket, session_id: str):
        self.websocket = websocket
        self.session_id = session_id
        self.is_active = True

    def _clean_text_for_tts(self, text: str) -> str:
        """Remove markdown/special characters for TTS."""
        cleaned = text.replace("*", "").replace("#", "").replace("`", "").replace("**", "")
        return cleaned

    async def _send_json(self, data: dict):
        if self.is_active:
            try:
                await self.websocket.send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"[{self.session_id}] Error sending JSON: {e}")

    async def _stream_ai_audio(self, text: str):
        """Stream AI voice output to frontend."""
        if not self.is_active:
            return
        
        cleaned_text = self._clean_text_for_tts(text)
        
        await self._send_json({"status": "ai_speaking"})
        
        try:
            async for audio_chunk in deepgram_service.text_to_speech_stream(cleaned_text, "male"):
                if self.is_active:
                    await self.websocket.send_bytes(audio_chunk)
            
            await self._send_json({"status": "ai_finished_speaking"})
            
        except Exception as e:
            logger.error(f"[{self.session_id}] Audio streaming error: {e}")
            await self._send_json({"status": "error", "message": "Audio failed"})

    async def run(self):
        """
        Main entry point for comparison session.
        The comparison endpoint pre-calculates both charts before WebSocket connection.
        """
        logger.info(f"[{self.session_id}] Comparison session started")
        
        if not hasattr(self, 'comparison_data'):
            logger.error(f"[{self.session_id}] No comparison data provided")
            await self._send_json({"status": "error", "message": "No data"})
            self.is_active = False
            return
        
        try:
            msg = self.comparison_data
            
            # Extract chart and name data
            chart1 = msg.get("person1", {}).get("chart", {})
            chart2 = msg.get("person2", {}).get("chart", {})
            name1 = msg.get("person1", {}).get("name", "Person 1")
            name2 = msg.get("person2", {}).get("name", "Person 2")
            
            # Send analyzing status
            await self._send_json({"status": "analyzing"})
            logger.info(f"[{self.session_id}] Generating comparison for {name1} and {name2}")
            
            # Generate comparison analysis
            try:
                comparison_data = await asyncio.to_thread(
                    get_kundli_comparison,
                    chart1, chart2, name1, name2
                )
            except Exception as e:
                logger.error(f"[{self.session_id}] Comparison generation error: {e}")
                await self._send_json({
                    "status": "error",
                    "message": f"Comparison failed: {str(e)}"
                })
                self.is_active = False
                return

            # Build comprehensive response text
            response_text = f"""
Namaste. I have analyzed the cosmic connection between {name1} and {name2}.

{comparison_data.get('summary', '')}

Emotional Harmony: {comparison_data.get('emotional_analysis', '')}

Intellectual Connection: {comparison_data.get('intellectual_analysis', '')}

Financial Prosperity: {comparison_data.get('financial_analysis', '')}

Physical Attraction: {comparison_data.get('physical_analysis', '')}

Your Strengths Together: {comparison_data.get('strengths', '')}

Challenges to Navigate: {comparison_data.get('challenges', '')}

Divine Remedies: {comparison_data.get('recommendations', '')}
"""

            # Send comparison data with scores
            await self._send_json({
                "status": "comparison_result",
                "analysis": comparison_data,
                "scores": comparison_data.get("scores", {}),
                "ui_control": comparison_data.get("ui", {})
            })
            
            logger.info(f"[{self.session_id}] Comparison complete")
            await self._send_json({"status": "comparison_finished"})
            
            self.is_active = False

        except WebSocketDisconnect:
            logger.info(f"[{self.session_id}] WebSocket disconnected")
            self.is_active = False
        except Exception as e:
            logger.error(f"[{self.session_id}] Session Error: {e}", exc_info=True)
            await self._send_json({"status": "error", "message": str(e)})
            self.is_active = False
