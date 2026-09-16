import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from core.models import Project
from schemas.location import LocationCreate
from ai.llm_client import LLMClient
from prompts.locations.location_prompt import (
    get_location_generation_system_prompt,
    get_location_generation_user_prompt
)

logger = logging.getLogger("microdrama.location_engine")

class LocationEngine:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def generate_locations_from_story(self, project: Project) -> List[LocationCreate]:
        """Extracts and structures 3-5 core environments using Cloudflare Gemma 4."""
        synopsis = project.story.synopsis if project.story else (project.logline or project.title)
        system_prompt = get_location_generation_system_prompt()
        user_prompt = get_location_generation_user_prompt(
            title=project.title,
            genre=project.genre,
            synopsis=synopsis
        )

        if self.llm.is_configured():
            try:
                raw_json = self.llm.generate_structured_json(system_prompt, user_prompt)
                loc_list = raw_json.get("locations", [])
                results = []
                for loc in loc_list:
                    results.append(LocationCreate(
                        project_id=project.id,
                        name=loc.get("name", "Unknown Environment"),
                        description=loc.get("description"),
                        architecture=loc.get("architecture"),
                        materials=loc.get("materials"),
                        lighting=loc.get("lighting"),
                        time_of_day=loc.get("time_of_day", "Night / After Hours"),
                        visual_identity=loc.get("visual_identity"),
                        continuity_constraints=loc.get("continuity_constraints", [])
                    ))
                if results:
                    return results
            except Exception as e:
                logger.error(f"Location LLM generation failed: {e}. Using deterministic seed fallback.")

        return self._get_fallback_locations(project.id)

    def _get_fallback_locations(self, project_id: str) -> List[LocationCreate]:
        """Benchmark locations for After Closing seed."""
        return [
            LocationCreate(
                project_id=project_id,
                name="Central Mall Atrium",
                description="Massive multi-tier central atrium where the lockdown begins and final morning discovery occurs.",
                architecture="1990s brutalist commercial atrium with glass pyramid skylights and suspended escalators",
                materials="Polished white marble floor, brushed steel handrails, exposed concrete geometric pillars",
                lighting="Overcast moonlight filtering through skylights mixed with flickering yellow emergency exit signs",
                time_of_day="Midnight / After Closing",
                visual_identity="Vast empty cavern with echoing acoustics and long geometrical shadow lines",
                continuity_constraints=[
                    "Dry decorative fountain in the center filled with dead leaves and coins",
                    "Massive steel shutter gates locked across the main glass revolving doors"
                ]
            ),
            LocationCreate(
                project_id=project_id,
                name="Fashion Store & Fitting Corridor",
                description="Upscale clothing boutique where the second trial takes place amongst dozens of motionless mannequins.",
                architecture="Modern luxury retail layout with mirror-paneled pillars and narrow fitting room corridor",
                materials="Dark walnut parquet flooring, floor-to-ceiling glass display cases, velvet curtains",
                lighting="Cold cyan fluorescent tracks overhead, half extinguished into heavy shadows",
                time_of_day="Night",
                visual_identity="Endless reflective glass mirrors creating disorienting infinite reflections of mannequins",
                continuity_constraints=[
                    "Fitting room #3 door is permanently ajar revealing a headless pedestal",
                    "Full-length gilded mirror with spiderweb crack at lower corner"
                ]
            ),
            LocationCreate(
                project_id=project_id,
                name="Children's Toy Store",
                description="Surreal specialty toy boutique where Lucy encounters Emma and the wind-up puzzle.",
                architecture="Archway entrance framed with faded rainbow tiles and carousel centerpiece",
                materials="Checkered linoleum floor, pastel painted wooden shelves, plastic toy cases",
                lighting="Static amber carousel spotlight cutting through dense atmospheric dust",
                time_of_day="Night",
                visual_identity="Creepy contrast between cheerful childhood artifacts and pitch-black corners",
                continuity_constraints=[
                    "Central mechanical carousel horse is frozen mid-motion",
                    "Overhead chime melody looping faintly on distorted speaker"
                ]
            ),
            LocationCreate(
                project_id=project_id,
                name="Security & CCTV Control Hub",
                description="Cramped subterranean monitoring room where David searches for override codes.",
                architecture="Sub-level utility bunker with rack-mounted servers and CRT video monitor wall",
                materials="Industrial diamond-plate steel flooring, metal mesh walls, exposed conduits",
                lighting="Glowing green cathode ray screens casting eerie glow over metal consoles",
                time_of_day="Night",
                visual_identity="Claustrophobic tech nerve-center with static fuzz on all 16 security monitors",
                continuity_constraints=[
                    "Monitor #7 consistently shows the atrium from an unmapped high camera angle",
                    "Master breaker panel locked with a heavy padlock"
                ]
            ),
            LocationCreate(
                project_id=project_id,
                name="Final Display Window (Street Front)",
                description="The exterior street-facing window display where transformed players stand at dawn.",
                architecture="Sleek street-level facade with thick plate glass facing empty morning street",
                materials="High-gloss black lacquer pedestal staging, pristine plate glass, studio spotlights",
                lighting="Crisp, stark morning sunlight blending with warm halogen display spotlights",
                time_of_day="Dawn / Morning",
                visual_identity="Chilling museum-like stillness viewed from outside the glass looking in",
                continuity_constraints=[
                    "Gold lettering on glass: 'AUTUMN COLLECTION — NEW ARRIVALS'",
                    "Pedestals 1, 2, and 3 occupied by perfectly styled human mannequins"
                ]
            )
        ]
