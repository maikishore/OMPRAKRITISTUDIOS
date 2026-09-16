def get_location_generation_system_prompt() -> str:
    return (
        "You are an elite cinematic production designer and location scout for a micro-drama. "
        "Given the approved story synopsis and rules, extract the 3-5 core physical environments/locations "
        "needed to stage the entire 10-minute micro-drama with distinct architectural, material, and lighting continuity.\n\n"
        "Guidelines:\n"
        "1. Focus on atmosphere, spatial texture, lighting mood, and physical constraints.\n"
        "2. Define visual identity and architectural materials.\n"
        "3. Respond strictly with a JSON list of location objects."
    )

def get_location_generation_user_prompt(title: str, genre: str, synopsis: str) -> str:
    return (
        f"Project: {title} ({genre})\n"
        f"Synopsis: {synopsis}\n\n"
        "Return a JSON object with this exact schema:\n"
        "{\n"
        '  "locations": [\n'
        '    {\n'
        '      "name": "Location Name (e.g. Central Mall Atrium)",\n'
        '      "description": "Spatial overview and narrative function",\n'
        '      "architecture": "e.g. Multi-level 90s brutalist commercial atrium with glass skylights",\n'
        '      "materials": "e.g. Polished white marble floors, brushed steel railings, towering concrete pillars",\n'
        '      "lighting": "e.g. Overcast moonlight through frosted glass skylights combined with flickering emergency sodium lights",\n'
        '      "time_of_day": "Night / After Hours",\n'
        '      "visual_identity": "Eerie desolation, long shadows stretching across reflective marble",\n'
        '      "continuity_constraints": [\n'
        '        "Fountain in center is dry and filled with abandoned coins",\n'
        '        "Escalator is locked and frozen at step 14"\n'
        '      ]\n'
        '    }\n'
        '  ]\n'
        "}"
    )
