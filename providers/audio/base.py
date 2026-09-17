from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class AudioGenerationRequest:
    text: str
    voice: str = "af_sarah"
    speed: float = 1.0
    reference_audio: Optional[bytes] = None
    parameters: Optional[Dict[str, Any]] = None

@dataclass
class AudioGenerationResult:
    audio_bytes: bytes
    sample_rate: int = 24000
    duration_seconds: float = 3.0
    mime_type: str = "audio/wav"
    parameters: Optional[Dict[str, Any]] = None

class AudioProvider(ABC):
    @abstractmethod
    def generate_speech(self, request: AudioGenerationRequest) -> AudioGenerationResult:
        """Generates speech audio bytes from dialogue text and voice profile."""
        pass
