"""Character Sheet & Expression Matrix Service.

Generates consistent multi-angle turnarounds, expression grids, and action poses
tailored for zero face drift in downstream Image-to-Video models.
"""

from typing import Dict, Any, List
from core.models import Character

class CharacterSheetService:
    """Templates and compilers for Character Turnaround Sheets and Expression Matrices."""

    PRESETS: Dict[str, Dict[str, Any]] = {
        "MASTER_PORTRAIT": {
            "name": "👤 Master Frontal Portrait (Identity Anchor)",
            "description": "Clean, neutral eye-level cinematic portrait defining facial biometric baseline.",
            "aspect_ratio": "9:16",
            "width": 768,
            "height": 1344,
            "template": "Cinematic eye-level 35mm film portrait of {name}, {traits}, wearing {costume}. Neutral direct expression, soft chiaroscuro lighting, subtle skin texture, shallow depth of field, 8k resolution, raw photo."
        },
        "TURNAROUND_3ANGLE": {
            "name": "📐 3-Angle Model Sheet (Front, 3/4, Profile)",
            "description": "Composite turnaround showing the character in 3 distinct camera angles in one frame for 360° video awareness.",
            "aspect_ratio": "16:9",
            "width": 1024,
            "height": 576,
            "template": "Character turn-around model sheet of {name}, {traits}, wearing {costume}. Three distinct views side-by-side in one frame: front view, three-quarter view, and 90 degree side profile view. Uniform soft cinematic studio lighting, clean background, 8k resolution, photorealistic character reference."
        },
        "EXPRESSION_TERROR": {
            "name": "😱 Fear & Terror (Horror/Drama Climax)",
            "description": "Extreme panic, wide eyes, shallow rapid breathing, sweat glistening.",
            "aspect_ratio": "9:16",
            "width": 768,
            "height": 1344,
            "template": "Cinematic close-up portrait of {name}, {traits}, wearing {costume}, expression of intense horror and terror, wide dilated pupils, hyper-realistic panic, cold sweat, dramatic rim lighting, shadowy background, raw film still."
        },
        "EXPRESSION_SHOCK": {
            "name": "⚡ Sudden Shock & Disbelief",
            "description": "Mouth slightly agape, freezing in realization, tense jaw.",
            "aspect_ratio": "9:16",
            "width": 768,
            "height": 1344,
            "template": "Cinematic medium portrait of {name}, {traits}, wearing {costume}, expression of utter shock and sudden disbelief, jaw clenched, eyes fixed off-camera, dramatic harsh overhead lighting, cinematic depth of field."
        },
        "EXPRESSION_ANGER": {
            "name": "😡 Confrontational Anger & Tension",
            "description": "Furrowed brow, sharp aggressive eye contact, heavy emotional tension.",
            "aspect_ratio": "9:16",
            "width": 768,
            "height": 1344,
            "template": "Intense cinematic close-up of {name}, {traits}, wearing {costume}, angry confrontational expression, furrowed brow, fierce gaze, hard side lighting, deep shadows, 35mm film aesthetic."
        },
        "EXPRESSION_SUSPICION": {
            "name": "🤫 Suspicion & Stealth Whispering",
            "description": "Glancing sideways, tense posture, vigilant and alert.",
            "aspect_ratio": "9:16",
            "width": 768,
            "height": 1344,
            "template": "Cinematic 3/4 angle portrait of {name}, {traits}, wearing {costume}, suspicious and guarded expression, glancing over shoulder, dim moody atmospheric lighting, cinematic horror color grading."
        },
        "FULL_BODY_STANCE": {
            "name": "🚶 Full Body Wardrobe & Proportions",
            "description": "Head-to-toe full body reference locking signature clothing, shoes, and height proportions.",
            "aspect_ratio": "9:16",
            "width": 768,
            "height": 1344,
            "template": "Full-body cinematic fashion photography of {name}, {traits}, wearing {costume}, full head to shoes visible, natural standing stance, atmospheric environment lighting, 8k resolution, ultra-detailed textures."
        },
        "ACTION_RUNNING": {
            "name": "🏃 Dynamic Action / Escape Pose",
            "description": "In-motion dynamic movement, sprinting or lunging.",
            "aspect_ratio": "9:16",
            "width": 768,
            "height": 1344,
            "template": "Action still of {name}, {traits}, wearing {costume}, captured mid-sprint while escaping down a dim corridor, dynamic motion blur on edges, urgent body language, cinematic lens flare, high tension."
        }
    }

    @classmethod
    def compile_prompt(cls, character: Character, preset_key: str) -> Dict[str, Any]:
        """Compiles a ready-to-render prompt and dimension specs for a character preset."""
        preset = cls.PRESETS.get(preset_key, cls.PRESETS["MASTER_PORTRAIT"])
        traits = getattr(character, "physical_traits", None) or character.appearance or "cinematic character"
        costume = getattr(character, "signature_costume", None) or character.clothing or "signature wardrobe"
        
        prompt = preset["template"].format(
            name=character.name,
            traits=traits,
            costume=costume
        )
        return {
            "preset_key": preset_key,
            "preset_name": preset["name"],
            "prompt": prompt,
            "width": preset["width"],
            "height": preset["height"],
            "aspect_ratio": preset["aspect_ratio"]
        }

    @classmethod
    def list_presets(cls) -> List[Dict[str, Any]]:
        """Returns all available character sheet presets."""
        res = []
        for k, v in cls.PRESETS.items():
            res.append({
                "key": k,
                "name": v["name"],
                "description": v["description"],
                "aspect_ratio": v["aspect_ratio"]
            })
        return res
