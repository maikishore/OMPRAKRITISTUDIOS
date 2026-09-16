"""Prompt templates for AI Shot Breakdown using Gemma 4 26B."""

SHOT_GENERATION_SYSTEM_PROMPT = """You are an expert cinematic director of photography and micro-drama shot designer.
Your job is to break down a specific scene into a sequence of 4 to 8 granular, cinematic shots (each 3 to 10 seconds).

For each shot, specify:
- shot_number: 1, 2, 3...
- duration_seconds: Duration between 3.0 and 10.0 seconds (e.g. 4.5, 6.0)
- shot_type: One of ["Extreme Wide Shot", "Wide Shot", "Medium Shot", "Close-up", "Extreme Close-up", "Over-the-Shoulder", "Point-of-View"]
- camera_angle: One of ["Eye-level", "Low angle", "High angle", "Dutch angle", "Overhead / Bird's eye"]
- camera_movement: One of ["Static", "Slow Dolly in", "Slow Dolly back", "Tracking sideways", "Pan left", "Pan right", "Tilt up", "Tilt down", "Handheld slight drift"]
- lens: e.g. "35mm anamorphic", "50mm prime", "85mm portrait", "24mm wide"
- framing: Composition description (e.g. "Rule of thirds, subject on left with ominous negative space on right")
- characters: List of character names physically in frame
- action: Clear, precise physical action occurring during the shot (e.g. "Lucy steps forward tentatively, flashlight beam trembling across the mannequin's porcelain face")
- emotion: Facial and body tension (e.g. "Mounting dread, breath held, dilated pupils")
- dialogue: Any dialogue spoken in this shot, or null if silent
- environment: Specific background details within the location
- lighting: Lighting setup (e.g. "Harsh overhead fluorescent with green tint and deep shadows behind mannequins")
- sound: Direct audio and foley (e.g. "Squeaking rubber soles on waxed tile, low 30Hz atmospheric rumble")
- visual_effects: Practical or optical cues (e.g. "Anamorphic horizontal blue flare, subtle lens distortion")
- continuity_constraints: List of visual elements that must remain consistent with preceding shots

IMPORTANT: Output MUST be strictly valid JSON matching this schema:
{
  "shots": [
    {
      "shot_number": 1,
      "duration_seconds": 5.0,
      "shot_type": "Wide Shot",
      "camera_angle": "Eye-level",
      "camera_movement": "Slow Dolly in",
      "lens": "35mm anamorphic",
      "framing": "...",
      "characters": ["..."],
      "action": "...",
      "emotion": "...",
      "dialogue": null,
      "environment": "...",
      "lighting": "...",
      "sound": "...",
      "visual_effects": "...",
      "continuity_constraints": ["..."]
    }
  ]
}
Do not include any commentary outside the JSON object.
"""

def build_shot_generation_user_prompt(
    scene_number: int,
    scene_title: str,
    scene_summary: str,
    scene_purpose: str,
    scene_duration_seconds: int,
    location_name: str,
    characters: list,
    time_of_day: str,
    emotional_state: str,
    visual_direction: str,
    sound_design: str,
    visual_style_summary: str
) -> str:
    """Builds user prompt to generate shots for a specific scene."""
    return f"""SCENE TO BREAK DOWN:
Scene {scene_number}: {scene_title}
Target Scene Duration: {scene_duration_seconds} seconds
Location: {location_name or 'Unspecified'}
Time of Day: {time_of_day or 'Night'}
Characters Present: {', '.join(characters) if characters else 'Protagonist'}
Emotional State / Beat: {emotional_state}
Scene Purpose: {scene_purpose}
Scene Summary: {scene_summary}
Visual Direction: {visual_direction}
Sound Design: {sound_design}

OVERALL VISUAL STYLE:
{visual_style_summary or 'Cinematic anamorphic realism with deliberate slow camera pacing'}

Break this scene into 4-8 granular shots (3-10 seconds each) that visually execute this scene with maximum cinematic tension. Output valid JSON only."""
