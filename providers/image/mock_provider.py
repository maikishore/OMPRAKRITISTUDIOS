"""Local Mock Image Provider for testing, rapid development, and offline execution."""

import io
import time
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from providers.image.base import ImageProvider, ImageGenerationRequest, ImageGenerationResult

class MockImageProvider(ImageProvider):
    """Generates synthetic high-contrast visual stills with metadata overlays."""

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        width = request.width or 768
        height = request.height or 1344

        # Generate a stylized gradient canvas
        img = Image.new("RGB", (width, height), color=(18, 20, 28))
        draw = ImageDraw.Draw(img)

        # Draw aesthetic cinematic border
        draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(220, 60, 60), width=3)
        draw.rectangle([(26, 26), (width - 26, height - 26)], outline=(60, 80, 120), width=1)

        # Draw decorative rule lines
        draw.line([(40, 100), (width - 40, 100)], fill=(120, 140, 180), width=2)
        draw.line([(40, height - 120), (width - 40, height - 120)], fill=(120, 140, 180), width=2)

        # Render Header text
        header = "🎬 MICRODRAMA STUDIO"
        sub = "FLUX.1 [DEV] / MODAL GPU EMULATION"
        draw.text((45, 50), header, fill=(255, 255, 255))
        draw.text((45, 75), sub, fill=(180, 200, 220))

        # Wrap Prompt text across lines
        prompt_lines = []
        words = request.prompt.split()
        cur_line = []
        for word in words:
            cur_line.append(word)
            if len(" ".join(cur_line)) > 36:
                prompt_lines.append(" ".join(cur_line))
                cur_line = []
        if cur_line:
            prompt_lines.append(" ".join(cur_line))

        y_offset = 140
        draw.text((45, y_offset), "PROMPT SPECIFICATION:", fill=(255, 215, 0))
        y_offset += 30

        for line in prompt_lines[:12]:
            draw.text((45, y_offset), line, fill=(230, 230, 230))
            y_offset += 24

        # Render reference thumbnails if provided
        if request.reference_images:
            x_thumb = width - 160
            y_thumb = 140
            for r_idx, r_bytes in enumerate(request.reference_images[:3]):
                try:
                    r_img = Image.open(io.BytesIO(r_bytes)).convert("RGB").resize((120, 120))
                    img.paste(r_img, (x_thumb, y_thumb))
                    draw.rectangle([(x_thumb, y_thumb), (x_thumb + 120, y_thumb + 120)], outline=(100, 220, 120), width=2)
                    draw.text((x_thumb + 5, y_thumb + 125), f"REF #{r_idx+1}", fill=(100, 220, 120))
                    y_thumb += 150
                except Exception:
                    pass

        # Footer parameters
        footer_y = height - 100
        ref_count = len(request.reference_images)
        ref_badge = f"IP-Adapter Face Lock: {ref_count} Ref Active" if ref_count > 0 else "Base Diffusion"
        draw.text((45, footer_y), f"Resolution: {width}x{height} | Seed: {request.seed or 42}", fill=(180, 180, 180))
        draw.text((45, footer_y + 25), f"Model: FLUX.1 / Modal GPU | {ref_badge}", fill=(100, 220, 120))

        # Output PNG bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", quality=95)
        image_bytes = buffer.getvalue()

        return ImageGenerationResult(
            image_bytes=image_bytes,
            mime_type="image/png",
            seed=request.seed or 42,
            parameters={
                "provider": "mock",
                "width": width,
                "height": height,
                "reference_count": ref_count
            }
        )

    @property
    def capabilities(self) -> Dict[str, bool]:
        return {
            "text_to_image": True,
            "image_to_image": True,
            "multi_reference": True,
            "face_lock": True
        }
