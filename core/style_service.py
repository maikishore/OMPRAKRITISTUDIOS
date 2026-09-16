from typing import Optional
from sqlalchemy.orm import Session
from core.models import VisualStyle, Project
from core.enums import ProjectStatus
from schemas.style import VisualStyleSchema

class StyleService:
    @staticmethod
    def get_project_style(db: Session, project_id: str) -> Optional[VisualStyle]:
        return db.query(VisualStyle).filter(VisualStyle.project_id == project_id).first()

    @staticmethod
    def save_or_update_style(db: Session, project_id: str, data: VisualStyleSchema, approve: bool = False) -> VisualStyle:
        style = StyleService.get_project_style(db, project_id)
        if not style:
            style = VisualStyle(project_id=project_id)
            db.add(style)

        style.cinematic_realism = data.cinematic_realism
        style.camera_language = data.camera_language
        style.lens_preferences = data.lens_preferences
        style.lighting_language = data.lighting_language
        style.color_progression = data.color_progression
        style.contrast = data.contrast
        style.depth_of_field = data.depth_of_field
        style.film_grain = data.film_grain
        style.production_design = data.production_design
        style.visual_motifs = data.visual_motifs
        style.is_approved = approve

        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            if approve:
                project.status = ProjectStatus.STYLE_READY.value

        db.commit()
        db.refresh(style)
        return style
