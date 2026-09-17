"""Factory to instantiate configured Audio/TTS providers."""

from providers.audio.base import AudioProvider
from providers.audio.modal_provider import ModalAudioProvider
from providers.audio.mock_provider import MockAudioProvider

def get_audio_provider(provider_name: str = "modal") -> AudioProvider:
    """Returns an AudioProvider instance based on configuration."""
    name = (provider_name or "").lower().strip()
    if name == "modal":
        return ModalAudioProvider()
    elif name == "mock":
        return MockAudioProvider()
    return ModalAudioProvider()
