"""Modal GPU Image Provider driver."""

import io
import base64
import logging
from typing import Dict, Any, Optional
from core.config import settings
from providers.image.base import ImageProvider, ImageGenerationRequest, ImageGenerationResult
from providers.image.mock_provider import MockImageProvider

logger = logging.getLogger(__name__)

class ModalImageProvider(ImageProvider):
    """Invokes remote Modal GPU App for FLUX image generation & face conditioning."""

    def __init__(self, endpoint_url: Optional[str] = None):
        self.endpoint_url = endpoint_url or getattr(settings, "MODAL_IMAGE_ENDPOINT", None)
        self.fallback = MockImageProvider()

    def _composite_references(self, ref_list: list, target_w: int, target_h: int) -> Optional[bytes]:
        from PIL import Image
        if not ref_list:
            return None
        if len(ref_list) == 1:
            return ref_list[0]

        images = []
        for b in ref_list[:4]:
            try:
                images.append(Image.open(io.BytesIO(b)).convert("RGB"))
            except Exception:
                pass

        if not images:
            return None
        if len(images) == 1:
            return ref_list[0]

        canvas = Image.new("RGB", (target_w, target_h), (20, 20, 25))
        n = len(images)
        if n == 2:
            w_half = target_w // 2
            im1 = images[0].resize((w_half, target_h))
            im2 = images[1].resize((target_w - w_half, target_h))
            canvas.paste(im1, (0, 0))
            canvas.paste(im2, (w_half, 0))
        elif n == 3:
            w_half = target_w // 2
            h_half = target_h // 2
            im1 = images[0].resize((w_half, target_h))
            im2 = images[1].resize((target_w - w_half, h_half))
            im3 = images[2].resize((target_w - w_half, target_h - h_half))
            canvas.paste(im1, (0, 0))
            canvas.paste(im2, (w_half, 0))
            canvas.paste(im3, (w_half, h_half))
        else: # 4
            w_half = target_w // 2
            h_half = target_h // 2
            im1 = images[0].resize((w_half, h_half))
            im2 = images[1].resize((target_w - w_half, h_half))
            im3 = images[2].resize((w_half, target_h - h_half))
            im4 = images[3].resize((target_w - w_half, target_h - h_half))
            canvas.paste(im1, (0, 0))
            canvas.paste(im2, (w_half, 0))
            canvas.paste(im3, (0, h_half))
            canvas.paste(im4, (w_half, h_half))

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        return buf.getvalue()

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        # 1. Direct modal.Cls lookup on Modal Cloud
        try:
            import modal
            cls = modal.Cls.from_name("microdrama-studio-image", "FluxImageGenerator")
            instance = cls()

            target_w = request.width or 1344
            target_h = request.height or 768
            ref_bytes = self._composite_references(request.reference_images, target_w, target_h)

            raw_png_bytes = instance.generate_image.remote(
                prompt=request.prompt,
                image_bytes=ref_bytes,
                strength=0.75,
                num_inference_steps=request.num_inference_steps or 4,
                guidance_scale=3.5,
                width=target_w,
                height=target_h,
                seed=request.seed or 42
            )

            if isinstance(raw_png_bytes, bytes) and len(raw_png_bytes) > 0:
                return ImageGenerationResult(
                    image_bytes=raw_png_bytes,
                    mime_type="image/png",
                    seed=request.seed or 42,
                    parameters={"provider": "modal", "model": "FLUX on Modal L4 GPU", "reference_count": len(request.reference_images or [])}
                )
        except Exception as e:
            logger.info(f"Direct Modal lookup skipped ({e}); using local synthetic provider.")

        return self.fallback.generate(request)

    @property
    def capabilities(self) -> Dict[str, bool]:
        return {
            "text_to_image": True,
            "image_to_image": True,
            "multi_reference": True,
            "face_lock": True
        }
