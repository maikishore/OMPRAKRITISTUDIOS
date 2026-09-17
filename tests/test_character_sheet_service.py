import pytest
from core.models import Character
from core.character_sheet_service import CharacterSheetService

def test_character_sheet_service_list_presets():
    presets = CharacterSheetService.list_presets()
    assert len(presets) >= 5
    keys = [p["key"] for p in presets]
    assert "MASTER_PORTRAIT" in keys
    assert "TURNAROUND_3ANGLE" in keys
    assert "EXPRESSION_TERROR" in keys
    assert "FULL_BODY_STANCE" in keys

def test_character_sheet_service_compile_prompt():
    char = Character(
        id="char-test-1",
        project_id="proj-1",
        name="Lucy Vance",
        role="Protagonist",
        appearance="28-year-old retail supervisor with messy dark ponytail",
        clothing="dark green security vest over black hoodie",
        identity_prompt="Portrait of Lucy Vance"
    )

    # Test master portrait
    res_master = CharacterSheetService.compile_prompt(char, "MASTER_PORTRAIT")
    assert "Lucy Vance" in res_master["prompt"]
    assert res_master["width"] == 768
    assert res_master["height"] == 1344

    # Test 3-angle turnaround
    res_turn = CharacterSheetService.compile_prompt(char, "TURNAROUND_3ANGLE")
    assert "Lucy Vance" in res_turn["prompt"]
    assert "three-quarter view" in res_turn["prompt"]
    assert res_turn["width"] == 1024
    assert res_turn["height"] == 576
    assert res_turn["aspect_ratio"] == "16:9"

    # Test terror expression
    res_terror = CharacterSheetService.compile_prompt(char, "EXPRESSION_TERROR")
    assert "terror" in res_terror["prompt"].lower()
