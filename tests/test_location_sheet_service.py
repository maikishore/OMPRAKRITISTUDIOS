import pytest
from core.models import Location
from core.location_sheet_service import LocationSheetService

def test_location_sheet_service_list_presets():
    presets = LocationSheetService.list_presets()
    assert len(presets) >= 5
    keys = [p["key"] for p in presets]
    assert "MASTER_WIDE" in keys
    assert "REVERSE_180" in keys
    assert "EMERGENCY_BLACKOUT" in keys
    assert "CCTV_SURVEILLANCE" in keys

def test_location_sheet_service_compile_prompt():
    loc = Location(
        id="loc-test-1",
        project_id="proj-1",
        name="Central Mall Atrium",
        description="A hollow 4-story commercial shopping atrium",
        architecture="Brutalist steel framework with towering glass skylights",
        materials="polished terrazzo flooring, chrome railings, reflective glass",
        lighting="commercial fluorescent lights, strobing emergency beacons"
    )

    # Test master wide
    res_wide = LocationSheetService.compile_prompt(loc, "MASTER_WIDE")
    assert "Central Mall Atrium" in res_wide["prompt"]
    assert "Brutalist steel" in res_wide["prompt"]
    assert res_wide["width"] == 1024
    assert res_wide["height"] == 576

    # Test emergency blackout
    res_blackout = LocationSheetService.compile_prompt(loc, "EMERGENCY_BLACKOUT")
    assert "outage" in res_blackout["prompt"].lower() or "blackout" in res_blackout["prompt"].lower()
    assert res_blackout["aspect_ratio"] == "16:9"

    # Test CCTV surveillance
    res_cctv = LocationSheetService.compile_prompt(loc, "CCTV_SURVEILLANCE")
    assert "cctv" in res_cctv["prompt"].lower() or "surveillance" in res_cctv["prompt"].lower()
