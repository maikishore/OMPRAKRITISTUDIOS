import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from core.models import Project
from schemas.character import CharacterCreate
from ai.llm_client import LLMClient
from prompts.characters.character_prompt import (
    get_character_generation_system_prompt,
    get_character_generation_user_prompt
)

logger = logging.getLogger("microdrama.character_engine")

class CharacterEngine:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def generate_characters_from_story(self, project: Project) -> List[CharacterCreate]:
        """Uses Cloudflare Gemma 4 (or deterministic fallback) to generate characters from approved story."""
        synopsis = project.story.synopsis if project.story else (project.logline or project.title)
        story_rules = project.story.story_rules if project.story else []

        system_prompt = get_character_generation_system_prompt()
        user_prompt = get_character_generation_user_prompt(
            title=project.title,
            genre=project.genre,
            synopsis=synopsis,
            story_rules=story_rules
        )

        if self.llm.is_configured():
            try:
                raw_json = self.llm.generate_structured_json(system_prompt, user_prompt)
                char_list = raw_json.get("characters", [])
                results = []
                for c in char_list:
                    results.append(CharacterCreate(
                        project_id=project.id,
                        name=c.get("name", "Unknown"),
                        role=c.get("role", "Supporting"),
                        gender=c.get("gender"),
                        age=str(c.get("age", "")),
                        appearance=c.get("appearance"),
                        hair=c.get("hair"),
                        face=c.get("face"),
                        body=c.get("body"),
                        skin=c.get("skin"),
                        clothing=c.get("clothing"),
                        accessories=c.get("accessories"),
                        personality=c.get("personality"),
                        behavior=c.get("behavior"),
                        voice_description=c.get("voice_description"),
                        character_arc=c.get("character_arc"),
                        continuity_constraints=c.get("continuity_constraints", []),
                        identity_prompt=c.get("identity_prompt"),
                        negative_constraints=c.get("negative_constraints")
                    ))
                if results:
                    return results
            except Exception as e:
                logger.error(f"Character LLM generation failed: {e}. Using deterministic seed fallback.")

        return self._get_fallback_characters(project.id, project.title)

    def _get_fallback_characters(self, project_id: str, title: str) -> List[CharacterCreate]:
        """High quality benchmark characters (Lucy, David, Emma) for seed testing."""
        return [
            CharacterCreate(
                project_id=project_id,
                name="Lucy Vance",
                role="Protagonist",
                gender="Female",
                age="24",
                appearance="Sharp, observant young woman with determined expression and subtle signs of exhaustion.",
                hair="Shoulder-length dark brown wavy hair with textured bangs",
                face="Strong jawline, dark hazel eyes, light natural freckles across nose bridge",
                body="Slim, athletic build, 5ft 6in",
                skin="Fair complexion with cool undertone",
                clothing="Oversized olive green canvas parka with brass collar zipper, black crewneck hoodie, dark indigo worn jeans",
                accessories="Delicate silver geometric pendant necklace on thin chain",
                personality="Analytical, quick-thinking, protective of others, initially composed",
                behavior="Subconsciously touches her necklace when analyzing puzzle rules; checks door latches twice",
                voice_description="Controlled and low, becoming breathy and hushed under extreme stress",
                character_arc="Transitions from confident game-solver to horrified realization of her own physical petrification",
                continuity_constraints=[
                    "Always wears the silver geometric pendant necklace",
                    "Olive green parka brass zipper is positioned on left collar"
                ],
                identity_prompt="Cinematic medium portrait of Lucy Vance, 24 years old, sharp jawline, dark hazel eyes, shoulder-length dark brown wavy hair with bangs, wearing an oversized olive green canvas parka over black hoodie and silver geometric pendant necklace, 35mm film still, photorealistic, cinematic lighting",
                negative_constraints="blurry, distorted facial features, missing pendant, changed clothing color"
            ),
            CharacterCreate(
                project_id=project_id,
                name="David Cruz",
                role="Co-Protagonist",
                gender="Male",
                age="27",
                appearance="Tall, cautious mall security contractor caught inside after hours.",
                hair="Short faded black hair, clean-cut with slight temple grey",
                face="Angular features, tired brown eyes, light stubble along jaw",
                body="Broad-shouldered, 6ft 0in, rugged frame",
                skin="Warm olive tan skin tone",
                clothing="Charcoal grey utility bomber jacket over faded navy thermal shirt, dark cargo pants, combat boots",
                accessories="Heavy black tactical halogen flashlight with scuffed lens attached to belt clip",
                personality="Pragmatic, defensive, skeptical of the mall games",
                behavior="Constantly illuminates corners and checks his watch countdown",
                voice_description="Gruff, steady baritone with cautious cadence",
                character_arc="Attempts to break physical barriers before succumbing to the rigid mannequin transformation",
                continuity_constraints=[
                    "Carries heavy black tactical flashlight with scuffed lens",
                    "Charcoal grey utility jacket has small tear on right shoulder"
                ],
                identity_prompt="Cinematic medium portrait of David Cruz, 27 years old, short black hair, light stubble, rugged angular face, tired brown eyes, wearing charcoal grey utility bomber jacket and carrying a heavy black tactical flashlight, 35mm film still, photorealistic, dramatic side lighting",
                negative_constraints="smooth baby face, bright clothes, missing tactical flashlight"
            ),
            CharacterCreate(
                project_id=project_id,
                name="Emma (The Child)",
                role="Mysterious Catalyst",
                gender="Female",
                age="8",
                appearance="Pale, eerily quiet child wandering the deserted mall corridors without fear.",
                hair="Long straight blonde hair with porcelain sheen",
                face="Unblinking pale blue eyes, completely neutral expression",
                body="Small, frail posture, unnervingly still when standing",
                skin="Porcelain pale, smooth synthetic-like sheen",
                clothing="Vintage yellow pleated wool coat over white collared dress, black mary-jane shoes with white socks",
                accessories="Small red velvet music box winding key held in right hand",
                personality="Enigmatic, speaks in matter-of-fact game rules, emotionless",
                behavior="Stands perfectly motionless for minutes at a time without blinking",
                voice_description="Clear, melodic, child-like cadence with zero emotional inflection",
                character_arc="Revealed to be the earliest converted mannequin guiding the next players into the ritual",
                continuity_constraints=[
                    "Yellow pleated coat with four large black buttons",
                    "Red velvet winding key always in right hand"
                ],
                identity_prompt="Cinematic medium portrait of an 8-year-old girl named Emma, long straight blonde hair, eerie unblinking pale blue eyes, porcelain skin, wearing a vintage yellow pleated coat over white dress, holding a small red winding key, 35mm film look, haunting cinematic lighting",
                negative_constraints="smiling, emotional expression, modern casual clothing"
            )
        ]
