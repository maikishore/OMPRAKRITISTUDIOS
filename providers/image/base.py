from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class ImageGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 1024
    height: int = 768
    num_inference_steps: int = 4
    guidance_scale: float = 3.5
    seed: Optional[int] = None
    reference_images: List[bytes] = []
    strength: float = 0.75
    parameters: Dict[str, Any] = {}

class ImageGenerationResult(BaseModel):
    image_bytes: bytes
    mime_type: str = "image/png"
    seed: Optional[int] = None
    parameters: Dict[str, Any] = {}

class ImageProvider(ABC):
    """Abstract interface for all Image generation backends (FLUX, Qwen, Modal, etc.)"""

    @abstractmethod
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        pass

    @property
    @abstractmethod
    def capabilities(self) -> Dict[str, bool]:
        """e.g. {'text_to_image': True, 'image_to_image': True, 'multi_reference': False}"""
        pass
