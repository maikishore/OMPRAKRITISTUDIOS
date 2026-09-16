"""Factory for instantiating Image Generation Providers."""

from typing import Optional
from providers.image.base import ImageProvider
from providers.image.modal_provider import ModalImageProvider
from providers.image.cloudflare_flux import CloudflareFluxProvider
from providers.image.mock_provider import MockImageProvider

def get_image_provider(provider_name: Optional[str] = "modal") -> ImageProvider:
    """Returns the requested ImageProvider instance."""
    name = (provider_name or "modal").lower()

    if name in ("modal", "flux_modal", "flux_dev"):
        return ModalImageProvider()
    elif name in ("cloudflare", "flux_schnell", "cf"):
        return CloudflareFluxProvider()
    elif name in ("mock", "offline", "test"):
        return MockImageProvider()
    else:
        # Default to Modal GPU provider
        return ModalImageProvider()
