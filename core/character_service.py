from typing import List, Optional
from sqlalchemy.orm import Session
from core.models import Character, Project
from core.enums import ProjectStatus
from schemas.character import CharacterCreate, CharacterUpdate

class CharacterService:
    @staticmethod
    def create_character(db: Session, data: CharacterCreate) -> Character:
        character = Character(
            project_id=data.project_id,
            name=data.name,
            role=data.role,
            gender=data.gender,
            age=data.age,
            appearance=data.appearance,
            hair=data.hair,
            face=data.face,
            body=data.body,
            skin=data.skin,
            clothing=data.clothing,
            accessories=data.accessories,
            personality=data.personality,
            behavior=data.behavior,
            voice_description=data.voice_description,
            character_arc=data.character_arc,
            continuity_constraints=data.continuity_constraints,
            master_reference_asset_id=data.master_reference_asset_id,
            identity_prompt=data.identity_prompt,
            negative_constraints=data.negative_constraints,
            is_approved=False
        )
        db.add(character)
        db.commit()
        db.refresh(character)
        return character

    @staticmethod
    def get_character(db: Session, character_id: str) -> Optional[Character]:
        return db.query(Character).filter(Character.id == character_id).first()

    @staticmethod
    def list_project_characters(db: Session, project_id: str) -> List[Character]:
        return db.query(Character).filter(Character.project_id == project_id).all()

    @staticmethod
    def list_characters_by_project(db: Session, project_id: str) -> List[Character]:
        """Alias for list_project_characters."""
        return db.query(Character).filter(Character.project_id == project_id).all()

    @staticmethod
    def update_character(db: Session, character_id: str, data: CharacterUpdate) -> Optional[Character]:
        character = CharacterService.get_character(db, character_id)
        if not character:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(character, key, value)

        db.commit()
        db.refresh(character)
        return character

    @staticmethod
    def delete_character(db: Session, character_id: str) -> bool:
        character = CharacterService.get_character(db, character_id)
        if not character:
            return False
        db.delete(character)
        db.commit()
        return True

    @staticmethod
    def approve_all_characters(db: Session, project_id: str) -> bool:
        characters = CharacterService.list_project_characters(db, project_id)
        if not characters:
            return False
        for c in characters:
            c.is_approved = True
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.CHARACTERS_READY.value
        db.commit()
        return True
