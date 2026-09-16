from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from core.models import Shot, Scene, Project, PromptVersion
from core.enums import ShotStatus, ProjectStatus
from schemas.shot import ShotCreate

class ShotService:
    """Service layer for Shot management and prompt versioning."""

    @staticmethod
    def create_shot(db: Session, shot_in: ShotCreate) -> Shot:
        """Create a new shot for a scene."""
        shot = Shot(
            scene_id=shot_in.scene_id,
            shot_number=shot_in.shot_number,
            duration_seconds=shot_in.duration_seconds,
            shot_type=shot_in.shot_type,
            camera_angle=shot_in.camera_angle,
            camera_movement=shot_in.camera_movement,
            lens=shot_in.lens,
            framing=shot_in.framing,
            characters=shot_in.characters,
            location_id=shot_in.location_id,
            action=shot_in.action,
            emotion=shot_in.emotion,
            dialogue=shot_in.dialogue,
            environment=shot_in.environment,
            lighting=shot_in.lighting,
            sound=shot_in.sound,
            visual_effects=shot_in.visual_effects,
            image_prompt=shot_in.image_prompt,
            video_prompt=shot_in.video_prompt,
            reference_asset_ids=shot_in.reference_asset_ids,
            previous_shot_id=shot_in.previous_shot_id,
            continuity_constraints=shot_in.continuity_constraints,
            status=ShotStatus.DRAFT.value
        )
        db.add(shot)
        db.commit()
        db.refresh(shot)

        # Record initial prompt versions if prompts exist
        if shot.image_prompt:
            ShotService.record_prompt_version(db, target_type="shot_image", target_id=shot.id, prompt=shot.image_prompt)
        if shot.video_prompt:
            ShotService.record_prompt_version(db, target_type="shot_video", target_id=shot.id, prompt=shot.video_prompt)

        return shot

    @staticmethod
    def get_shot(db: Session, shot_id: str) -> Optional[Shot]:
        """Get a shot by ID."""
        return db.query(Shot).filter(Shot.id == shot_id).first()

    @staticmethod
    def list_shots_by_scene(db: Session, scene_id: str) -> List[Shot]:
        """List all shots in a scene ordered by shot_number."""
        return db.query(Shot).filter(Shot.scene_id == scene_id).order_by(Shot.shot_number.asc()).all()

    @staticmethod
    def list_shots_by_project(db: Session, project_id: str) -> List[Shot]:
        """List all shots across all scenes for a project."""
        return (
            db.query(Shot)
            .join(Scene, Shot.scene_id == Scene.id)
            .filter(Scene.project_id == project_id)
            .order_by(Scene.scene_number.asc(), Shot.shot_number.asc())
            .all()
        )

    @staticmethod
    def record_prompt_version(
        db: Session,
        target_type: str,
        target_id: str,
        prompt: str,
        negative_prompt: Optional[str] = None,
        model: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> PromptVersion:
        """Records a new immutable prompt version in the prompt_versions table."""
        latest = (
            db.query(PromptVersion)
            .filter(PromptVersion.target_type == target_type, PromptVersion.target_id == target_id)
            .order_by(PromptVersion.version.desc())
            .first()
        )
        next_version = (latest.version + 1) if latest else 1

        pv = PromptVersion(
            target_type=target_type,
            target_id=target_id,
            version=next_version,
            prompt=prompt,
            negative_prompt=negative_prompt,
            model=model or "FLUX / LTX",
            parameters=parameters or {}
        )
        db.add(pv)
        db.commit()
        db.refresh(pv)
        return pv

    @staticmethod
    def list_prompt_versions(db: Session, target_type: str, target_id: str) -> List[PromptVersion]:
        """Retrieve full prompt history for a shot or reference."""
        return (
            db.query(PromptVersion)
            .filter(PromptVersion.target_type == target_type, PromptVersion.target_id == target_id)
            .order_by(PromptVersion.version.desc())
            .all()
        )

    @staticmethod
    def update_shot(db: Session, shot_id: str, updates: Dict[str, Any]) -> Optional[Shot]:
        """Update shot fields and track prompt revisions."""
        shot = ShotService.get_shot(db, shot_id)
        if not shot:
            return None

        # Track prompt changes if image_prompt or video_prompt are updated
        if "image_prompt" in updates and updates["image_prompt"] != shot.image_prompt:
            if updates["image_prompt"]:
                ShotService.record_prompt_version(
                    db, target_type="shot_image", target_id=shot.id, prompt=updates["image_prompt"]
                )

        if "video_prompt" in updates and updates["video_prompt"] != shot.video_prompt:
            if updates["video_prompt"]:
                ShotService.record_prompt_version(
                    db, target_type="shot_video", target_id=shot.id, prompt=updates["video_prompt"]
                )

        for key, value in updates.items():
            if hasattr(shot, key):
                setattr(shot, key, value)

        db.commit()
        db.refresh(shot)
        return shot

    @staticmethod
    def delete_shot(db: Session, shot_id: str) -> bool:
        """Delete a shot and renumber remaining shots in the scene."""
        shot = ShotService.get_shot(db, shot_id)
        if not shot:
            return False
        scene_id = shot.scene_id
        db.delete(shot)
        db.commit()

        # Renumber remaining shots
        remaining = ShotService.list_shots_by_scene(db, scene_id)
        for idx, sh in enumerate(remaining, start=1):
            sh.shot_number = idx
        db.commit()
        return True

    @staticmethod
    def batch_create_shots_for_scene(db: Session, scene_id: str, shot_list: List[Dict[str, Any]]) -> List[Shot]:
        """Batch replace or insert shots for a scene."""
        # Remove existing shots for this scene
        db.query(Shot).filter(Shot.scene_id == scene_id).delete()
        db.commit()

        created = []
        for s_data in shot_list:
            shot = Shot(
                scene_id=scene_id,
                shot_number=s_data.get("shot_number", len(created) + 1),
                duration_seconds=float(s_data.get("duration_seconds", 5.0)),
                shot_type=s_data.get("shot_type", "Medium Shot"),
                camera_angle=s_data.get("camera_angle", "Eye-level"),
                camera_movement=s_data.get("camera_movement", "Slow Dolly"),
                lens=s_data.get("lens", "50mm"),
                framing=s_data.get("framing"),
                characters=s_data.get("characters", []),
                location_id=s_data.get("location_id"),
                action=s_data.get("action"),
                emotion=s_data.get("emotion"),
                dialogue=s_data.get("dialogue"),
                environment=s_data.get("environment"),
                lighting=s_data.get("lighting"),
                sound=s_data.get("sound"),
                visual_effects=s_data.get("visual_effects"),
                image_prompt=s_data.get("image_prompt"),
                video_prompt=s_data.get("video_prompt"),
                reference_asset_ids=s_data.get("reference_asset_ids", []),
                continuity_constraints=s_data.get("continuity_constraints", []),
                status=ShotStatus.DRAFT.value
            )
            db.add(shot)
            created.append(shot)
        db.commit()

        for shot in created:
            db.refresh(shot)
            if shot.image_prompt:
                ShotService.record_prompt_version(db, "shot_image", shot.id, shot.image_prompt)
            if shot.video_prompt:
                ShotService.record_prompt_version(db, "shot_video", shot.id, shot.video_prompt)

        return created

    @staticmethod
    def approve_all_shots_for_project(db: Session, project_id: str) -> bool:
        """Approve all shots and transition project status to SHOTS_READY."""
        shots = ShotService.list_shots_by_project(db, project_id)
        if not shots:
            return False
        for sh in shots:
            sh.status = ShotStatus.APPROVED.value
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.SHOTS_READY.value
        db.commit()
        return True
