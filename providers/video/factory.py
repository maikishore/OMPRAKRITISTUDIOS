import os
from providers.video.base import VideoProvider
from providers.video.mock_video_provider import MockVideoProvider
from providers.video.modal_video_provider import ModalVideoProvider

class VideoProviderFactory:
    """Factory to create VideoProvider instances based on environment or parameters."""

    @staticmethod
    def get_provider(provider_type: str = "auto") -> VideoProvider:
        prov = provider_type.lower()
        if prov == "auto":
            prov = os.getenv("VIDEO_PROVIDER", "modal").lower()

        if prov == "modal":
            return ModalVideoProvider()
        elif prov == "mock":
            return MockVideoProvider()
        else:
            return MockVideoProvider()
