import pytest
from core.modal_service import ModalService

def test_modal_service_profile():
    profile = ModalService.get_current_profile()
    # If modal is authenticated, profile will be a non-empty string
    assert profile is None or isinstance(profile, str)

def test_modal_service_available_models():
    models = ModalService.AVAILABLE_MODELS
    assert len(models) >= 1
    assert models[0]["app_name"] == "microdrama-studio-image"
    assert models[0]["class_name"] == "FluxImageGenerator"

def test_modal_service_list_apps():
    apps = ModalService.list_deployed_apps()
    assert isinstance(apps, list)
