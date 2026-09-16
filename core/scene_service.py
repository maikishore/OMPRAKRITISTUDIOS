from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from core.models import Scene, Project, Location
from core.enums import ProjectStatus
from schemas.scene import SceneCreate

class SceneService:
    """Service layer for Scene management and runtime calculations."""

    @staticmethod
    def create_scene(db: Session, scene_in: SceneCreate) -> Scene:
        """Create a new scene."""
        scene = Scene(
            project_id=scene_in.project_id,
            scene_number=scene_in.scene_number,
            title=scene_in.title,
            summary=scene_in.summary,
            purpose=scene_in.purpose,
            duration_seconds=scene_in.duration_seconds,
            location_id=scene_in.location_id,
            time_of_day=scene_in.time_of_day,
            emotional_state=scene_in.emotional_state,
            story_beat=scene_in.story_beat,
            dialogue=scene_in.dialogue,
            sound_design=scene_in.sound_design,
            visual_direction=scene_in.visual_direction,
            continuity_notes=scene_in.continuity_notes,
            characters=scene_in.characters,
            is_approved=False
        )
        db.add(scene)
        db.commit()
        db.refresh(scene)
        return scene

    @staticmethod
    def get_scene(db: Session, scene_id: str) -> Optional[Scene]:
        """Get a scene by its ID."""
        return db.query(Scene).filter(Scene.id == scene_id).first()

    @staticmethod
    def list_scenes_by_project(db: Session, project_id: str) -> List[Scene]:
        """List all scenes for a project ordered by scene_number."""
        return db.query(Scene).filter(Scene.project_id == project_id).order_by(Scene.scene_number.asc()).all()

    @staticmethod
    def update_scene(db: Session, scene_id: str, updates: Dict[str, Any]) -> Optional[Scene]:
        """Update scene fields."""
        scene = SceneService.get_scene(db, scene_id)
        if not scene:
            return None
        for key, value in updates.items():
            if hasattr(scene, key):
                setattr(scene, key, value)
        db.commit()
        db.refresh(scene)
        return scene

    @staticmethod
    def delete_scene(db: Session, scene_id: str) -> bool:
        """Delete a scene and re-index remaining scenes."""
        scene = SceneService.get_scene(db, scene_id)
        if not scene:
            return False
        project_id = scene.project_id
        db.delete(scene)
        db.commit()

        # Re-number remaining scenes
        remaining = SceneService.list_scenes_by_project(db, project_id)
        for idx, sc in enumerate(remaining, start=1):
            sc.scene_number = idx
        db.commit()
        return True

    @staticmethod
    def delete_all_scenes_for_project(db: Session, project_id: str) -> int:
        """Delete all scenes for a project."""
        deleted = db.query(Scene).filter(Scene.project_id == project_id).delete()
        db.commit()
        return deleted

    @staticmethod
    def batch_create_scenes(db: Session, project_id: str, scene_list: List[Dict[str, Any]]) -> List[Scene]:
        """Batch replace or insert scenes for a project."""
        SceneService.delete_all_scenes_for_project(db, project_id)
        created = []
        for s_data in scene_list:
            sc = Scene(
                project_id=project_id,
                scene_number=s_data.get("scene_number", len(created) + 1),
                title=s_data.get("title", f"Scene {len(created) + 1}"),
                summary=s_data.get("summary", ""),
                purpose=s_data.get("purpose", ""),
                duration_seconds=s_data.get("duration_seconds", 45),
                location_id=s_data.get("location_id"),
                time_of_day=s_data.get("time_of_day"),
                emotional_state=s_data.get("emotional_state"),
                story_beat=s_data.get("story_beat"),
                dialogue=s_data.get("dialogue"),
                sound_design=s_data.get("sound_design"),
                visual_direction=s_data.get("visual_direction"),
                continuity_notes=s_data.get("continuity_notes"),
                characters=s_data.get("characters", []),
                is_approved=False
            )
            db.add(sc)
            created.append(sc)
        db.commit()
        for sc in created:
            db.refresh(sc)
        return created

    @staticmethod
    def calculate_total_runtime(db: Session, project_id: str) -> Dict[str, Any]:
        """Calculate total running duration and comparison against project target."""
        scenes = SceneService.list_scenes_by_project(db, project_id)
        total_seconds = sum(s.duration_seconds for s in scenes)
        project = db.query(Project).filter(Project.id == project_id).first()
        target_seconds = project.target_duration_seconds if project else 600
        delta = total_seconds - target_seconds
        
        return {
            "total_seconds": total_seconds,
            "target_seconds": target_seconds,
            "delta_seconds": delta,
            "scene_count": len(scenes),
            "is_on_budget": abs(delta) <= 60, # within 1 minute tolerance
            "percent_of_target": round((total_seconds / target_seconds * 100) if target_seconds > 0 else 100, 1)
        }

    @staticmethod
    def approve_all_scenes(db: Session, project_id: str) -> bool:
        """Approve all scenes and transition project status to SCENES_READY."""
        scenes = SceneService.list_scenes_by_project(db, project_id)
        if not scenes:
            return False
        for s in scenes:
            s.is_approved = True
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.SCENES_READY.value
        db.commit()
        return True
