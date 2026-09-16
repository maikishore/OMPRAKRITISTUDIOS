import logging
from typing import Optional
from sqlalchemy.orm import Session
from core.models import Project
from schemas.style import VisualStyleSchema
from ai.llm_client import LLMClient
from prompts.style.style_prompt import (
    get_style_generation_system_prompt,
    get_style_generation_user_prompt
)

logger = logging.getLogger("microdrama.style_engine")

class StyleEngine:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def generate_style_from_story(self, project: Project) -> VisualStyleSchema:
        """Generates project visual style rules using Cloudflare Gemma 4."""
        synopsis = project.story.synopsis if project.story else (project.logline or project.title)
        tone = project.story.tone if project.story else "Cinematic drama"

        system_prompt = get_style_generation_system_prompt()
        user_prompt = get_style_generation_user_prompt(
            title=project.title,
            genre=project.genre,
            synopsis=synopsis,
            tone=tone
        )

        if self.llm.is_configured():
            try:
                raw_json = self.llm.generate_structured_json(system_prompt, user_prompt)
                return VisualStyleSchema.model_validate(raw_json)
            except Exception as e:
                logger.error(f"Style LLM generation failed: {e}. Using deterministic seed fallback.")

        return self._get_fallback_style(project.genre)

    def _get_fallback_style(self, genre: str) -> VisualStyleSchema:
        return VisualStyleSchema(
            cinematic_realism="High-fidelity 35mm optical look with naturalistic skin tones, organic fine grain, and accurate optical depth",
            camera_language="Intentional, deliberate dolly and slow tracking shots; creeping push-ins during puzzle moments; symmetrical static framing for architectural dread",
            lens_preferences="Anamorphic Master Primes: 35mm for cavernous wide shots, 50mm for standard interaction, 85mm for intimate character tension",
            lighting_language="Moody chiaroscuro lighting with volumetric haze; sharp directional rim lighting separating characters from deep black backgrounds",
            color_progression="Act I: Warm commercial mall incandescence. Act II: Cold desaturated cyan and green fluorescent tension. Act III: Bleached morning sunlight with pristine clinical warmth",
            contrast="High contrast ratio (8:1) with deep inky blacks and controlled highlight roll-off",
            depth_of_field="Shallow depth of field (T2.0) with subtle oval anamorphic bokeh and edge falloff",
            film_grain="Fine organic 35mm film grain (Kodak Vision3 500T 5219 texture)",
            production_design="Hyper-tactile surfaces: reflective marble, glossy plastic polymer limbs, velvet curtains, scratched metal conduits",
            visual_motifs=[
                "Mirrors and glass reflections that don't match character posture",
                "Wide overhead symmetrical shots highlighting entrapment in the geometric architecture",
                "Gradual lighting shifts from warm yellow to sterile surgical white/cyan"
            ]
        )
