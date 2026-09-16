from typing import List, Optional
from sqlalchemy.orm import Session
from core.models import Location, Project
from core.enums import ProjectStatus
from schemas.location import LocationCreate, LocationUpdate

class LocationService:
    @staticmethod
    def create_location(db: Session, data: LocationCreate) -> Location:
        location = Location(
            project_id=data.project_id,
            name=data.name,
            description=data.description,
            architecture=data.architecture,
            materials=data.materials,
            lighting=data.lighting,
            time_of_day=data.time_of_day,
            visual_identity=data.visual_identity,
            continuity_constraints=data.continuity_constraints,
            master_reference_asset_id=data.master_reference_asset_id,
            is_approved=False
        )
        db.add(location)
        db.commit()
        db.refresh(location)
        return location

    @staticmethod
    def get_location(db: Session, location_id: str) -> Optional[Location]:
        return db.query(Location).filter(Location.id == location_id).first()

    @staticmethod
    def list_project_locations(db: Session, project_id: str) -> List[Location]:
        return db.query(Location).filter(Location.project_id == project_id).all()

    @staticmethod
    def list_locations_by_project(db: Session, project_id: str) -> List[Location]:
        """Alias for list_project_locations."""
        return db.query(Location).filter(Location.project_id == project_id).all()

    @staticmethod
    def update_location(db: Session, location_id: str, data: LocationUpdate) -> Optional[Location]:
        location = LocationService.get_location(db, location_id)
        if not location:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(location, key, value)

        db.commit()
        db.refresh(location)
        return location

    @staticmethod
    def delete_location(db: Session, location_id: str) -> bool:
        location = LocationService.get_location(db, location_id)
        if not location:
            return False
        db.delete(location)
        db.commit()
        return True

    @staticmethod
    def approve_all_locations(db: Session, project_id: str) -> bool:
        locations = LocationService.list_project_locations(db, project_id)
        if not locations:
            return False
        for loc in locations:
            loc.is_approved = True

        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.LOCATIONS_READY.value
        db.commit()
        return True
