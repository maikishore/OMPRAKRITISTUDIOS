import io
import os
import tempfile
import numpy as np
from PIL import Image, ImageDraw
import imageio
from typing import Dict, Any

from providers.video.base import VideoProvider, VideoGenerationRequest, VideoGenerationResult

class MockVideoProvider(VideoProvider):
    """Local simulation provider for Video Generation (generates dynamic MP4 animation)."""

    def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        width = (request.width // 32) * 32
        height = (request.height // 32) * 32
        fps = request.fps or 24
        total_frames = min(request.num_frames or 48, 48)  # Quick preview

        base_img = None
        if request.start_frame_bytes:
            try:
                base_img = Image.open(io.BytesIO(request.start_frame_bytes)).convert("RGB").resize((width, height))
            except Exception:
                pass

        frames = []
        for i in range(total_frames):
            if base_img:
                # Ken Burns effect (Smooth zoom & pan)
                scale = 1.0 + 0.08 * (i / total_frames)
                w_s, h_s = int(width * scale), int(height * scale)
                resized = base_img.resize((w_s, h_s), Image.Resampling.BILINEAR)
                x_off = (w_s - width) // 2
                y_off = (h_s - height) // 2
                frame = resized.crop((x_off, y_off, x_off + width, y_off + height))
            else:
                frame = Image.new("RGB", (width, height), color=(15 + (i * 2) % 30, 20 + i % 25, 35 + (i * 3) % 40))

            draw = ImageDraw.Draw(frame)
            draw.rectangle([(8, 8), (width - 8, height - 8)], outline=(255, 140, 0), width=3)
            draw.text((20, 20), "LOCAL PREVIEW VIDEO (MOCK / DEV MODE)", fill=(255, 255, 255))
            draw.text((20, 50), f"Frame {i+1}/{total_frames} @ {fps}fps | Seed: {request.seed or 42}", fill=(220, 220, 220))
            draw.text((20, 80), f"Prompt: {request.prompt[:80]}", fill=(180, 180, 180))
            frames.append(np.array(frame))

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name

        imageio.mimsave(tmp_path, frames, fps=fps, format="mp4")
        with open(tmp_path, "rb") as f:
            video_bytes = f.read()
        os.remove(tmp_path)

        duration = round(total_frames / fps, 2)
        return VideoGenerationResult(
            video_bytes=video_bytes,
            mime_type="video/mp4",
            duration=duration,
            seed=request.seed or 42,
            parameters={"provider": "mock", "frames": total_frames, "fps": fps}
        )

    @property
    def capabilities(self) -> Dict[str, bool]:
        return {
            "text_to_video": True,
            "image_to_video": True,
            "frame_interpolation": False
        }
