import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from core.models import Story, Project
from core.enums import ProjectStatus
from schemas.story import StorySchema
from .llm_client import LLMClient
from prompts.story.story_prompt import get_story_generation_system_prompt, get_story_generation_user_prompt

logger = logging.getLogger("microdrama.story_engine")

class StoryEngine:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def generate_story(self, title: str, genre: str, idea: str, target_duration_seconds: int = 600) -> StorySchema:
        """Generates a validated StorySchema using Cloudflare Gemma 4 26B (or seed fallback if offline)."""
        system_prompt = get_story_generation_system_prompt()
        user_prompt = get_story_generation_user_prompt(title, genre, idea, target_duration_seconds)

        if self.llm.is_configured():
            try:
                raw_json = self.llm.generate_structured_json(system_prompt, user_prompt)
                return StorySchema.model_validate(raw_json)
            except Exception as e:
                logger.error(f"LLM story generation failed: {e}. Falling back to deterministic structured template.")

        # High quality fallback template (especially tailored if seed project is After Closing)
        return self._get_fallback_story(title, genre, idea)

    def save_story(self, db: Session, project_id: str, story_data: StorySchema, approve: bool = False) -> Story:
        """Persists or updates the structured story in the database and updates project status."""
        story = db.query(Story).filter(Story.project_id == project_id).first()
        if not story:
            story = Story(project_id=project_id)
            db.add(story)

        story.premise = story_data.premise
        story.theme = story_data.theme
        story.tone = story_data.tone
        story.synopsis = story_data.synopsis
        story.ending = story_data.ending
        story.story_rules = story_data.story_rules
        story.acts = story_data.acts
        story.clues = story_data.clues
        story.continuity_rules = story_data.continuity_rules
        story.is_approved = approve

        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            if approve:
                project.status = ProjectStatus.STORY_APPROVED.value
            elif project.status == ProjectStatus.IDEA.value:
                project.status = ProjectStatus.STORY_DRAFT.value

        db.commit()
        db.refresh(story)
        return story

    def _get_fallback_story(self, title: str, genre: str, idea: str) -> StorySchema:
        """Deterministic seed story structure for offline development and instant testing."""
        return StorySchema(
            premise=f"In '{title}', characters are trapped in a surreal, escalating environment under strict, unforgiving rules.",
            theme="The illusion of control and inevitable transformation",
            tone=f"Atmospheric, high-tension {genre.lower()} with cold cinematic realism",
            synopsis=(
                f"Lucy and David find themselves locked inside a deserted shopping mall after hours alongside a mysterious child. "
                f"A series of broadcast games force them to navigate increasingly surreal store floors. While they complete every trial, "
                f"the true ritual of the mall steadily hardens their limbs into glossy plastic mannequins."
            ),
            ending=(
                "Lucy places the final puzzle piece and the exit doors click open. But as morning light floods the atrium, "
                "she cannot move. Looking into the store window, she sees her own mannequin reflection alongside David and Emma. "
                "The cheerful mall speaker announces: 'Next player.'"
            ),
            story_rules=[
                "Rule 1: The broadcast games cannot be abandoned once initiated.",
                "Rule 2: Each cleared game permanently extinguishes one sector of the mall lights.",
                "Rule 3: Completing a game is not an escape—it is the transformation catalyst."
            ],
            acts=[
                {
                    "act": 1,
                    "title": "Act I: The Lockdown",
                    "description": "The mall gates drop at closing time. Lucy meets David and a wandering child. The first challenge begins.",
                    "key_revelation": "The security exits are bricked behind display walls."
                },
                {
                    "act": 2,
                    "title": "Act II: The Escalating Trials",
                    "description": "They navigate the fashion floor and children's section, solving timed puzzles while mannequins shift positions.",
                    "key_revelation": "Lucy's fingertips have turned rigid and synthetic."
                },
                {
                    "act": 3,
                    "title": "Act III: The False Dawn",
                    "description": "The final game is completed. The morning doors unlock, but total paralysis sets in. They take their place in the window display.",
                    "key_revelation": "There was never a winning condition—only conversion."
                }
            ],
            clues=[
                "Distant mechanical clicking echoing behind store walls",
                "Mannequins wearing clothes identical to past missing shoppers",
                "Store PA system repeating cheerful promotional slogans between games"
            ],
            continuity_rules=[
                "Lucy wears an oversized olive green canvas jacket and silver pendant",
                "David carries a heavy black tactical flashlight with scuffed lens",
                "Lighting shifts chronologically from warm incandescent commercial glow to cold blue fluorescent stillness"
            ]
        )
