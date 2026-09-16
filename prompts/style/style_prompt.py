def get_style_generation_system_prompt() -> str:
    return (
        "You are an elite director of photography (DP) and visual director for a cinematic micro-drama. "
        "Define the comprehensive visual grammar, lens packages, lighting language, color grading progression, "
        "and camera movement philosophy tailored specifically to the project's story and genre.\n\n"
        "Respond strictly with a single JSON object."
    )

def get_style_generation_user_prompt(title: str, genre: str, synopsis: str, tone: str) -> str:
    return (
        f"Project: {title} ({genre})\n"
        f"Tone: {tone}\n"
        f"Synopsis: {synopsis}\n\n"
        "Return a JSON object with this exact schema:\n"
        "{\n"
        '  "cinematic_realism": "e.g. Gritty 35mm photochemical grain, naturalistic skin textures, high optical fidelity",\n'
        '  "camera_language": "e.g. Deliberate mechanical dolly movements, slow creeping push-ins, claustrophobic framing",\n'
        '  "lens_preferences": "e.g. Anamorphic primes (35mm wide establishing, 50mm medium, 85mm intimate portraiture)",\n'
        '  "lighting_language": "e.g. Volumetric haze, hard shadows, high contrast with deep inky blacks and specular highlights",\n'
        '  "color_progression": "e.g. Begins in warm commercial mall tones, shifts into sickly cyan/green fluorescent in Act II, ends in stark cold morning daylight in Act III",\n'
        '  "contrast": "High contrast with crushed deep blacks",\n'
        '  "depth_of_field": "Shallow depth of field with creamy oval anamorphic bokeh",\n'
        '  "film_grain": "Subtle organic 35mm Kodak 5219 grain structure",\n'
        '  "production_design": "Grounded practical textures: reflective chrome, weathered tile, glossy mannequin polymers",\n'
        '  "visual_motifs": [\n'
        '    "Window reflections showing rigid static poses",\n'
        '    "Overhead symmetrical wide shots emphasizing entrapment",\n'
        '    "Flickering lights timed to narrative heartbeats"\n'
        '  ]\n'
        "}"
    )
