def get_character_generation_system_prompt() -> str:
    return (
        "You are an elite casting director, cinematic character designer, and wardrobe supervisor for a micro-drama. "
        "Given the approved story synopsis, world rules, and theme, extract all essential characters (2-4 characters) "
        "and define their precise visual appearance, anatomy, wardrobe, personality, continuity constraints, and AI image prompts.\n\n"
        "Guidelines:\n"
        "1. Every character must have distinct, unambiguous physical features (hair, facial traits, skin tone, clothing, accessories).\n"
        "2. Include an 'identity_prompt' optimized for photorealistic image generation.\n"
        "3. Include 'continuity_constraints' (e.g., persistent scars, jewelry, specific jackets) that must never disappear across scenes.\n"
        "4. Respond strictly with a JSON list of character objects."
    )

def get_character_generation_user_prompt(title: str, genre: str, synopsis: str, story_rules: list) -> str:
    rules_formatted = "\n".join(f"- {r}" for r in story_rules)
    return (
        f"Project: {title} ({genre})\n"
        f"Synopsis: {synopsis}\n"
        f"Story Rules:\n{rules_formatted}\n\n"
        "Return a JSON object with this exact schema:\n"
        "{\n"
        '  "characters": [\n'
        '    {\n'
        '      "name": "Character Name",\n'
        '      "role": "Protagonist / Antagonist / Supporting",\n'
        '      "gender": "Female / Male / Non-binary",\n'
        '      "age": "e.g. 24",\n'
        '      "appearance": "Overall visual summary",\n'
        '      "hair": "e.g. Shoulder-length dark wavy hair with messy bangs",\n'
        '      "face": "e.g. Sharp jawline, dark hazel eyes, light freckles",\n'
        '      "body": "e.g. Slim, athletic build, 5ft 6in",\n'
        '      "skin": "e.g. Fair complexion with cool undertone",\n'
        '      "clothing": "e.g. Oversized olive green canvas parka over black hoodie and worn denim jeans",\n'
        '      "accessories": "e.g. Delicate silver pendant necklace, wrist smartwatch",\n'
        '      "personality": "Determined, analytical under pressure, protective",\n'
        '      "behavior": "Checks pulse when nervous, scans exits repeatedly",\n'
        '      "voice_description": "Controlled, low-pitched with slight vocal fry",\n'
        '      "character_arc": "From desperate escape-seeker to realizing the horrifying truth of the games",\n'
        '      "continuity_constraints": [\n'
        '        "Always wears the silver pendant",\n'
        '        "Green parka has brass zipper on left collar"\n'
        '      ],\n'
        '      "identity_prompt": "Cinematic portrait of a 24-year-old woman, sharp jawline, dark hazel eyes, shoulder-length dark wavy hair with bangs, wearing an olive green canvas parka and silver pendant, photorealistic, 35mm film photography, 8k textures",\n'
        '      "negative_constraints": "blurry, generic face, altered clothing color, missing pendant"\n'
        '    }\n'
        '  ]\n'
        "}"
    )
