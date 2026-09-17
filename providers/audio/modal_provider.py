"""Modal TTS Audio Provider Driver."""

import logging
from typing import Optional
from providers.audio.base import AudioProvider, AudioGenerationRequest, AudioGenerationResult
from providers.audio.mock_provider import MockAudioProvider

logger = logging.getLogger(__name__)

class ModalAudioProvider(AudioProvider):
    """Invokes remote Modal serverless KokoroAudioWorker on Modal Cloud."""

    def __init__(self):
        self.fallback = MockAudioProvider()

    def generate_speech(self, request: AudioGenerationRequest) -> AudioGenerationResult:
        try:
            import modal
            cls = modal.Cls.from_name("microdrama-studio-audio", "KokoroAudioWorker")
            instance = cls()

            raw_wav_bytes = instance.generate_speech.remote(
                text=request.text,
                voice=request.voice or "af_sarah",
                speed=request.speed or 1.0
            )

            if isinstance(raw_wav_bytes, bytes) and len(raw_wav_bytes) > 44:
                # Calculate duration from WAV byte length (24000 Hz, 16-bit mono = 48000 bytes/sec)
                data_len = len(raw_wav_bytes) - 44
                duration = round(data_len / 48000.0, 2)
                return AudioGenerationResult(
                    audio_bytes=raw_wav_bytes,
                    sample_rate=24000,
                    duration_seconds=max(0.5, duration),
                    mime_type="audio/wav",
                    parameters={"provider": "modal", "model": "Kokoro-82M on Modal", "voice": request.voice}
                )
        except Exception as e:
            logger.info(f"Modal Audio lookup skipped ({e}); using local mock audio provider.")

        return self.fallback.generate_speech(request)
