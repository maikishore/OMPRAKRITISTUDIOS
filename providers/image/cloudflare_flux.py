"""Cloudflare Workers AI FLUX.1 [schnell] Image Provider."""

import io
import base64
import httpx
import logging
from typing import Dict, Any, Optional
from core.config import settings
from providers.image.base import ImageProvider, ImageGenerationRequest, ImageGenerationResult

logger = logging.getLogger(__name__)

class CloudflareFluxProvider(ImageProvider):
    """Generates images using Cloudflare Workers AI @cf/black-forest-labs/flux-1-schnell."""

    def __init__(self, account_id: Optional[str] = None, auth_token: Optional[str] = None):
        self.account_id = account_id or settings.CLOUDFLARE_ACCOUNT_ID
        self.auth_token = auth_token or settings.CLOUDFLARE_AUTH_TOKEN
        self.model = "@cf/black-forest-labs/flux-1-schnell"

    def is_configured(self) -> bool:
        return bool(self.account_id and self.auth_token)

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if not self.is_configured():
            raise ValueError("Cloudflare credentials not configured. Please set them in Settings or .env.")

        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": request.prompt,
            "num_steps": min(8, max(4, request.num_inference_steps)),
            "width": min(1024, request.width),
            "height": min(1024, request.height)
        }

        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            # Cloudflare returns raw image bytes or base64 JSON
            content_type = response.headers.get("content-type", "")
            if "image/" in content_type:
                image_bytes = response.content
            else:
                data = response.json()
                if not data.get("success"):
                    errors = data.get("errors", [])
                    raise RuntimeError(f"Cloudflare FLUX error: {errors}")
                result = data.get("result", {})
                b64_img = result.get("image", "")
                image_bytes = base64.b64decode(b64_img)

            return ImageGenerationResult(
                image_bytes=image_bytes,
                mime_type="image/png",
                seed=request.seed,
                parameters={"provider": "cloudflare", "model": self.model}
            )

    @property
    def capabilities(self) -> Dict[str, bool]:
        return {
            "text_to_image": True,
            "image_to_image": False,
            "multi_reference": False,
            "face_lock": False
        }
