import os
from typing import Dict, Any, Optional

from providers.video.base import VideoProvider, VideoGenerationRequest, VideoGenerationResult
from providers.video.mock_video_provider import MockVideoProvider

class ModalVideoProvider(VideoProvider):
    """Client for Modal Serverless LTX-Video / Wan GPU Worker."""

    def __init__(
        self,
        app_name: str = "microdrama-studio-video",
        class_name: str = "LTXVideoGenerator"
    ):
        self.app_name = app_name
        self.class_name = class_name
        self._fallback = MockVideoProvider()

    def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        try:
            import modal

            print(f"📡 Connecting to Modal Video Worker `{self.app_name}.{self.class_name}`...")
            generator_cls = modal.Cls.from_name(self.app_name, self.class_name)
            generator_instance = generator_cls()

            video_bytes = generator_instance.generate_video.remote(
                prompt=request.prompt,
                image_bytes=request.start_frame_bytes,
                negative_prompt=request.negative_prompt,
                num_frames=request.num_frames,
                fps=request.fps,
                num_inference_steps=request.num_inference_steps,
                guidance_scale=request.guidance_scale,
                width=request.width,
                height=request.height,
                seed=request.seed or 42
            )

            fps = request.fps or 24
            num_frames = request.num_frames or 97
            duration = round(num_frames / fps, 2)

            return VideoGenerationResult(
                video_bytes=video_bytes,
                mime_type="video/mp4",
                duration=duration,
                seed=request.seed or 42,
                parameters={"provider": "modal", "app": self.app_name, "class": self.class_name}
            )

        except Exception as e:
            print(f"⚠️ Modal video worker call failed ({e}). Falling back to local simulation...")
            res = self._fallback.generate(request)
            res.parameters["fallback_reason"] = str(e)
            return res

    @property
    def capabilities(self) -> Dict[str, bool]:
        return {
            "text_to_video": True,
            "image_to_video": True,
            "frame_interpolation": False
        }
