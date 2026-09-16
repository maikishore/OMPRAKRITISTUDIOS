from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class VideoGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    start_frame_bytes: Optional[bytes] = None
    end_frame_bytes: Optional[bytes] = None
    width: int = 768
    height: int = 512
    fps: int = 24
    num_frames: int = 97  # ~4 seconds at 24fps
    num_inference_steps: int = 50
    guidance_scale: float = 4.5
    seed: Optional[int] = None
    parameters: Dict[str, Any] = {}

class VideoGenerationResult(BaseModel):
    video_bytes: bytes
    mime_type: str = "video/mp4"
    duration: float
    seed: Optional[int] = None
    parameters: Dict[str, Any] = {}

class VideoProvider(ABC):
    """Abstract interface for all Video generation backends (LTX, Wan, Modal, etc.)"""

    @abstractmethod
    def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        pass

    @property
    @abstractmethod
    def capabilities(self) -> Dict[str, bool]:
        """e.g. {'text_to_video': True, 'image_to_video': True, 'frame_interpolation': True}"""
        pass
