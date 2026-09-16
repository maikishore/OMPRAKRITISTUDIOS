from typing import List, Optional
from sqlalchemy.orm import Session
from .models import Asset
from schemas.asset import AssetCreate

class AssetService:
    @staticmethod
    def create_asset(db: Session, data: AssetCreate) -> Asset:
        asset = Asset(
            project_id=data.project_id,
            type=data.type.value if hasattr(data.type, "value") else data.type,
            file_path=data.file_path,
            mime_type=data.mime_type,
            provider=data.provider,
            model=data.model,
            prompt=data.prompt,
            seed=data.seed,
            parameters=data.parameters,
            width=data.width,
            height=data.height,
            fps=data.fps,
            duration=data.duration,
            parent_asset_id=data.parent_asset_id
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    @staticmethod
    def get_asset(db: Session, asset_id: str) -> Optional[Asset]:
        return db.query(Asset).filter(Asset.id == asset_id).first()

    @staticmethod
    def list_project_assets(db: Session, project_id: str, asset_type: Optional[str] = None) -> List[Asset]:
        q = db.query(Asset).filter(Asset.project_id == project_id)
        if asset_type:
            q = q.filter(Asset.type == asset_type)
        return q.order_by(Asset.created_at.desc()).all()

    @staticmethod
    def approve_asset(db: Session, asset_id: str, approved: bool = True, rejection_reason: Optional[str] = None) -> Optional[Asset]:
        asset = AssetService.get_asset(db, asset_id)
        if not asset:
            return None
        asset.is_approved = approved
        asset.rejection_reason = rejection_reason if not approved else None
        db.commit()
        db.refresh(asset)
        return asset
