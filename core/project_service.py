from typing import List, Optional
from sqlalchemy.orm import Session
from .models import Project
from .enums import ProjectStatus
from schemas.project import ProjectCreate, ProjectUpdate

class ProjectService:
    @staticmethod
    def create_project(db: Session, data: ProjectCreate) -> Project:
        project = Project(
            title=data.title,
            logline=data.logline,
            genre=data.genre,
            target_duration_seconds=data.target_duration_seconds,
            language=data.language,
            aspect_ratio=data.aspect_ratio,
            image_model=data.image_model,
            video_model=data.video_model,
            default_video_duration=data.default_video_duration,
            default_resolution=data.default_resolution,
            default_fps=data.default_fps,
            status=ProjectStatus.IDEA.value
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project(db: Session, project_id: str) -> Optional[Project]:
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def list_projects(db: Session) -> List[Project]:
        return db.query(Project).order_by(Project.created_at.desc()).all()

    @staticmethod
    def update_project(db: Session, project_id: str, data: ProjectUpdate) -> Optional[Project]:
        project = ProjectService.get_project(db, project_id)
        if not project:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key == "status" and value is not None:
                setattr(project, key, value.value if hasattr(value, "value") else value)
            elif value is not None:
                setattr(project, key, value)

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: str) -> bool:
        project = ProjectService.get_project(db, project_id)
        if not project:
            return False
        db.delete(project)
        db.commit()
        return True
