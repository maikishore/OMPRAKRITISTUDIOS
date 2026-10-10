import pytest
from providers.video.base import VideoGenerationRequest
from providers.video.mock_video_provider import MockVideoProvider
from providers.video.factory import VideoProviderFactory
from core.modal_service import ModalService

def test_mock_video_provider_generation():
    provider = MockVideoProvider()
    req = VideoGenerationRequest(
        prompt="A cyberpunk character walking in rain, cinematic lighting",
        width=512,
        height=512,
        fps=24,
        num_frames=24,
        seed=42
    )
    res = provider.generate(req)
    assert res.video_bytes is not None
    assert len(res.video_bytes) > 0
    assert res.mime_type == "video/mp4"
    assert res.duration > 0

def test_video_provider_factory():
    provider = VideoProviderFactory.get_provider("mock")
    assert isinstance(provider, MockVideoProvider)
    assert provider.capabilities["image_to_video"] is True

def test_modal_service_inactivity_window():
    models = ModalService.AVAILABLE_MODELS
    video_model = next((m for m in models if m["id"] == "video"), None)
    assert video_model is not None
    assert video_model["app_name"] == "microdrama-studio-video"
