"""Location & Environment Staging Suite Service.

Compiles multi-perspective establishing shots, reverse angles, emergency blackout states,
and CCTV surveillance cutaways for zero spatial drift in downstream video generation.
"""

from typing import Dict, Any, List
from core.models import Location

class LocationSheetService:
    """Manages cinematic presets and prompt compilation for multi-angle environment staging."""

    PRESETS: Dict[str, Dict[str, Any]] = {
        "MASTER_WIDE": {
            "name": "🏛️ Master Wide Establishing View",
            "description": "Grand panoramic eye-level establishing still defining architectural materials, scale, and baseline spatial geography.",
            "aspect_ratio": "16:9",
            "width": 1024,
            "height": 576,
            "template": "Grand wide-angle architectural establishing photograph of {name}. Architecture: {architecture}. Materials and textures: {materials}. Lighting: {lighting}. Perfectly composed cinematic wide shot, pristine spatial geometry, 8k resolution, raw photo."
        },
        "REVERSE_180": {
            "name": "🔄 Reverse Angle (180° Lookback View)",
            "description": "Opposite angle looking back across the environment, locking background geometry for reverse-shot dialogue and exit tracking.",
            "aspect_ratio": "16:9",
            "width": 1024,
            "height": 576,
            "template": "Reverse 180-degree wide angle photograph of {name}, looking back across the entire space toward the entrance and corridors. Architecture: {architecture}, {materials}. Lighting: {lighting}. Cinematic depth, deep focus, 8k resolution, raw photo."
        },
        "EMERGENCY_BLACKOUT": {
            "name": "🚨 Emergency Power Failure & Red Strobes",
            "description": "Pitch-black blackout state with harsh red emergency strobe beacons, long cast shadows, and eerie exit signs for horror/thriller climax.",
            "aspect_ratio": "16:9",
            "width": 1024,
            "height": 576,
            "template": "Cinematic horror still of {name} during a complete electrical power outage. Pitch-black darkness with isolated pulsing red emergency strobe lights, eerie glowing green exit signs, deep impenetrable shadows across {materials}, heavy atmospheric dread, raw film still."
        },
        "LOW_ANGLE_TRACKING": {
            "name": "📐 Low-Angle Floor Staging Still",
            "description": "Dramatic ground-level perspective looking up at towering structures, ideal for suspenseful character movement and chase tracking.",
            "aspect_ratio": "9:16",
            "width": 768,
            "height": 1344,
            "template": "Dramatic low-angle floor-level photograph inside {name}, looking up at towering vertical architecture: {architecture}, {materials}. Dramatic hard edge lighting: {lighting}, reflections on polished floors, cinematic vertical perspective, 8k resolution."
        },
        "CCTV_SURVEILLANCE": {
            "name": "📹 High-Angle CCTV Security Camera",
            "description": "Overhead wide fisheye perspective with surveillance timestamps, high-contrast security monitor aesthetics for cutaways.",
            "aspect_ratio": "16:9",
            "width": 1024,
            "height": 576,
            "template": "Security camera CCTV surveillance monitor still of {name}. High-angle ceiling perspective looking down across the entire layout, slight fisheye lens distortion, security timestamp overlay, high contrast industrial lighting, grainy authentic surveillance aesthetic."
        },
        "ATMOSPHERIC_HAZE": {
            "name": "🌫️ Volumetric Midnight Haze & Moonlight",
            "description": "Quiet, eerie after-hours atmosphere with volumetric light shafts through glass skylights and floating dust motes.",
            "aspect_ratio": "16:9",
            "width": 1024,
            "height": 576,
            "template": "Cinematic midnight photograph of {name} after hours. Desolate empty space, volumetric moonlight shafts piercing through glass skylights, soft haze and floating dust motes, cool blue and amber ambient lighting across {materials}, 8k resolution."
        }
    }

    @classmethod
    def compile_prompt(cls, location: Location, preset_key: str, default_aspect_ratio: str = "16:9") -> Dict[str, Any]:
        """Compiles a ready-to-render environment prompt and dimension specs."""
        preset = cls.PRESETS.get(preset_key, cls.PRESETS["MASTER_WIDE"])
        arch = getattr(location, "architecture", None) or "Modern commercial architecture"
        mat = getattr(location, "materials", None) or "glass, polished stone, and structural steel"
        light = getattr(location, "lighting", None) or "dramatic commercial ambient lighting"

        prompt = preset["template"].format(
            name=location.name,
            architecture=arch,
            materials=mat,
            lighting=light
        )

        width = preset["width"]
        height = preset["height"]

        # Adjust dimensions if project prefers 9:16 or 16:9
        if preset["aspect_ratio"] == "16:9" and default_aspect_ratio == "9:16" and preset_key == "MASTER_WIDE":
            # Keep wide aspect for panoramic environment unless specified
            pass

        return {
            "preset_key": preset_key,
            "preset_name": preset["name"],
            "prompt": prompt,
            "width": width,
            "height": height,
            "aspect_ratio": preset["aspect_ratio"]
        }

    @classmethod
    def list_presets(cls) -> List[Dict[str, Any]]:
        """Returns all available environment staging presets."""
        res = []
        for k, v in cls.PRESETS.items():
            res.append({
                "key": k,
                "name": v["name"],
                "description": v["description"],
                "aspect_ratio": v["aspect_ratio"]
            })
        return res
