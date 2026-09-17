"""Prompt templates for AI Scene Generation & Breakdown using Gemma 4 26B."""

SCENE_GENERATION_SYSTEM_PROMPT = """You are an expert cinematic micro-drama screenwriter and script supervisor.
Your job is to break down a structured 3-Act story, character roster, location bible, and visual style into a sequential list of 8 to 12 dramatic scenes.

The total duration of all scenes must closely match the target runtime in seconds (default ~600 seconds / 10 minutes).
Each scene must have:
- scene_number: 1, 2, 3...
- title: Short dramatic title
- summary: 2-3 sentences describing the core dramatic action and progression
- purpose: The narrative function (e.g. Inciting incident, escalating dread, clue revelation, midpoint reversal, climax)
- duration_seconds: Estimated running duration in seconds (typically 30-90s per scene)
- location_name: The name of the matching location from the location bible
- time_of_day: e.g. "Night - After Closing", "Midnight", "Dawn"
- characters: List of character names present in this scene
- emotional_state: Emotional tension level and protagonist psychology
- story_beat: 3-Act beat (e.g., Act 1 - Setup, Act 2 - First Game, Act 3 - Climax)
- dialogue: 2 to 4 lines of core dramatic spoken dialogue exchanges between characters in this scene
- sound_design: Ambient audio, mechanical cues, eerie soundscapes, musical mood
- visual_direction: Key camera angles, lighting mood, color shift, or blocking guidance
- continuity_notes: Any key props, costumes, physical injuries, or clues to maintain

IMPORTANT: Output MUST be strictly valid JSON matching this schema:
{
  "scenes": [
    {
      "scene_number": 1,
      "title": "...",
      "summary": "...",
      "purpose": "...",
      "duration_seconds": 55,
      "location_name": "...",
      "time_of_day": "...",
      "characters": ["Lucy", "David"],
      "emotional_state": "...",
      "story_beat": "...",
      "dialogue": "Lucy: 'Can you believe they rented the entire mall for this?'\\nDavid: 'Something feels off. The security guards just vanished.'",
      "sound_design": "...",
      "visual_direction": "...",
      "continuity_notes": "..."
    }
  ]
}
Do not include any commentary or preamble outside the JSON object.
"""

def build_scene_generation_user_prompt(
    title: str,
    genre: str,
    target_duration_seconds: int,
    story_context: dict,
    character_names: list,
    location_names: list,
    visual_style_summary: str
) -> str:
    """Builds user prompt to generate scenes from story and bible."""
    acts_summary = ""
    for act in story_context.get("acts", []):
        acts_summary += f"\n--- Act {act.get('act_number')}: {act.get('title')} ({act.get('duration_target_seconds', 0)}s) ---\n"
        acts_summary += f"Summary: {act.get('summary', '')}\n"
        acts_summary += f"Key Events: {', '.join(act.get('key_events', []))}\n"

    rules = story_context.get("story_rules", [])
    rules_text = "\n".join([f"- {r}" for r in rules])

    return f"""Project: {title}
Genre: {genre}
Target Total Runtime: {target_duration_seconds} seconds (~{target_duration_seconds // 60} minutes)

STORY 3-ACT STRUCTURE:
{acts_summary}

STORY RULES & CONTINUITY:
{rules_text}

CHARACTER ROSTER:
{', '.join(character_names) if character_names else 'Lucy, David, Emma'}

LOCATION BIBLE:
{', '.join(location_names) if location_names else 'Central Mall Atrium, Fashion Store, Toy Store, Security CCTV Station, Window Display'}

VISUAL STYLE:
{visual_style_summary or 'Cinematic anamorphic, realistic dark horror lighting progression'}

Break this story down into 8-12 granular, sequential scenes totaling ~{target_duration_seconds}s.
Ensure each scene includes vivid dialogue exchanges for the characters present. Output valid JSON only."""

