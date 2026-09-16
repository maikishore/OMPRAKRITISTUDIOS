def get_story_generation_system_prompt() -> str:
    return (
        "You are an elite cinematic screenwriter and micro-drama story architect. "
        "Your mission is to craft a tightly paced, compelling ~10-minute AI micro-drama script structure "
        "based on the user's idea, genre, and target runtime.\n\n"
        "Guidelines:\n"
        "1. Focus on visual storytelling, high emotional stakes, and tight narrative economy.\n"
        "2. Break down the story into a clean 3-Act structure (Act I: Setup & Catalyst, Act II: Confrontation & Rising Escalation, Act III: Climax & Resolution/Twist).\n"
        "3. Provide explicit world/story rules, narrative clues, and visual continuity rules (e.g. key wardrobe, props, or physical markers).\n"
        "4. Respond with a strictly structured JSON object matching the exact format below."
    )

def get_story_generation_user_prompt(title: str, genre: str, idea: str, target_duration_seconds: int = 600) -> str:
    mins = target_duration_seconds // 60
    return (
        f"Project Title: {title}\n"
        f"Genre: {genre}\n"
        f"Target Runtime: ~{mins} minutes ({target_duration_seconds} seconds)\n"
        f"Core Idea / Logline: {idea}\n\n"
        "Return a JSON object with this exact schema:\n"
        "{\n"
        '  "premise": "Core premise of the micro-drama (1-2 sentences)",\n'
        '  "theme": "Central dramatic theme",\n'
        '  "tone": "Emotional and visual tone (e.g., Cold claustrophobic horror, surreal neon dread)",\n'
        '  "synopsis": "Full narrative synopsis detailing beginning, escalation, and climax",\n'
        '  "ending": "The climatic ending or psychological twist",\n'
        '  "story_rules": [\n'
        '    "Rule 1: e.g. The games cannot be abandoned once started",\n'
        '    "Rule 2: e.g. Each cleared stage permanently shuts down one section of the mall lights"\n'
        '  ],\n'
        '  "acts": [\n'
        '    {"act": 1, "title": "Setup & The Lockdown", "description": "...", "key_revelation": "..."},\n'
        '    {"act": 2, "title": "The Trials & Transformation", "description": "...", "key_revelation": "..."},\n'
        '    {"act": 3, "title": "The False Victory & Mannequin Climax", "description": "...", "key_revelation": "..."}\n'
        '  ],\n'
        '  "clues": [\n'
        '    "Clue 1: Distant mechanical buzzing from mannequin joints",\n'
        '    "Clue 2: The store announcement repeating countdowns in a cheerful tone"\n'
        '  ],\n'
        '  "continuity_rules": [\n'
        '    "Lucy always wears the silver pendant and oversized green parka",\n'
        '    "David holds the flickering halogen flashlight with cracked glass"\n'
        '  ]\n'
        "}"
    )
