from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import GenerationJob
from .enums import JobStatus
from schemas.job import JobCreate

def utc_now():
    return datetime.now(timezone.utc)

class JobService:
    @staticmethod
    def create_job(db: Session, data: JobCreate) -> GenerationJob:
        job = GenerationJob(
            project_id=data.project_id,
            type=data.type.value if hasattr(data.type, "value") else data.type,
            provider=data.provider,
            payload=data.payload,
            status=JobStatus.QUEUED.value,
            progress=0.0
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[GenerationJob]:
        return db.query(GenerationJob).filter(GenerationJob.id == job_id).first()

    @staticmethod
    def list_project_jobs(db: Session, project_id: str) -> List[GenerationJob]:
        return db.query(GenerationJob).filter(GenerationJob.project_id == project_id).order_by(GenerationJob.created_at.desc()).all()

    @staticmethod
    def update_job_status(
        db: Session,
        job_id: str,
        status: JobStatus,
        progress: Optional[float] = None,
        result_asset_ids: Optional[List[str]] = None,
        error: Optional[str] = None
    ) -> Optional[GenerationJob]:
        job = JobService.get_job(db, job_id)
        if not job:
            return None

        job.status = status.value if hasattr(status, "value") else status
        if progress is not None:
            job.progress = progress
        if result_asset_ids is not None:
            job.result_asset_ids = result_asset_ids
        if error is not None:
            job.error = error

        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = utc_now()
        elif status in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED):
            job.completed_at = utc_now()

        db.commit()
        db.refresh(job)
        return job
