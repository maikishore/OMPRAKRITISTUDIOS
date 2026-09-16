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
    def list_assets_by_project(db: Session, project_id: str, asset_type: Optional[str] = None) -> List[Asset]:
        """Alias for list_project_assets."""
        return AssetService.list_project_assets(db, project_id, asset_type)

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

    @staticmethod
    def save_image_asset(
        db: Session,
        project_id: str,
        asset_type: str,
        image_bytes: bytes,
        prompt: str,
        seed: Optional[int] = None,
        width: int = 768,
        height: int = 1344,
        parent_asset_id: Optional[str] = None,
        provider: str = "modal",
        model: str = "FLUX.1 [dev]",
        parameters: Optional[dict] = None
    ) -> Asset:
        """Saves generated image bytes to disk and registers Asset in database."""
        import uuid
        from storage.paths import StoragePaths
        from storage.object_store import LocalObjectStore

        asset_id = str(uuid.uuid4())
        filename = f"{asset_type.lower()}_{asset_id[:8]}_{int(seed or 42)}.png"

        if "character" in asset_type.lower():
            dest_dir = StoragePaths.get_project_dir(project_id) / "characters"
        elif "location" in asset_type.lower():
            dest_dir = StoragePaths.get_project_dir(project_id) / "locations"
        elif "keyframe" in asset_type.lower() or "shot" in asset_type.lower():
            dest_dir = StoragePaths.get_keyframes_dir(project_id)
        else:
            dest_dir = StoragePaths.get_project_dir(project_id) / "misc"

        dest_path = dest_dir / filename
        LocalObjectStore.save_file(image_bytes, dest_path)

        asset = Asset(
            id=asset_id,
            project_id=project_id,
            type=asset_type,
            file_path=str(dest_path),
            mime_type="image/png",
            provider=provider,
            model=model,
            prompt=prompt,
            seed=seed or 42,
            width=width,
            height=height,
            parent_asset_id=parent_asset_id,
            parameters=parameters or {},
            is_approved=False
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    @staticmethod
    def set_character_master_reference(db: Session, character_id: str, asset_id: str) -> bool:
        """Sets an asset as the master approved visual identity reference for a character."""
        from core.models import Character
        char = db.query(Character).filter(Character.id == character_id).first()
        asset = AssetService.get_asset(db, asset_id)
        if not char or not asset:
            return False
        char.master_reference_asset_id = asset_id
        char.is_approved = True
        asset.is_approved = True
        db.commit()
        return True

    @staticmethod
    def set_location_master_reference(db: Session, location_id: str, asset_id: str) -> bool:
        """Sets an asset as the master approved visual identity reference for a location."""
        from core.models import Location
        loc = db.query(Location).filter(Location.id == location_id).first()
        asset = AssetService.get_asset(db, asset_id)
        if not loc or not asset:
            return False
        loc.master_reference_asset_id = asset_id
        loc.is_approved = True
        asset.is_approved = True
        db.commit()
        return True

    @staticmethod
    def link_shot_keyframe(db: Session, shot_id: str, asset_id: str) -> bool:
        """Links an approved generated keyframe to a Shot."""
        from core.models import Shot
        from core.enums import ShotStatus
        shot = db.query(Shot).filter(Shot.id == shot_id).first()
        asset = AssetService.get_asset(db, asset_id)
        if not shot or not asset:
            return False
        current_refs = list(shot.reference_asset_ids or [])
        if asset_id not in current_refs:
            current_refs.append(asset_id)
            shot.reference_asset_ids = current_refs
        shot.status = ShotStatus.KEYFRAME_READY.value
        asset.is_approved = True
        db.commit()
        return True

    @staticmethod
    def delete_asset(db: Session, asset_id: str) -> bool:
        """Deletes an asset from DB, disk, and unlinks it from characters, locations, or shots."""
        from pathlib import Path
        from core.models import Character, Location, Shot
        from core.enums import ShotStatus

        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return False

        # 1. Unlink from characters
        chars = db.query(Character).filter(Character.master_reference_asset_id == asset_id).all()
        for c in chars:
            c.master_reference_asset_id = None
            c.is_approved = False

        # 2. Unlink from locations
        locs = db.query(Location).filter(Location.master_reference_asset_id == asset_id).all()
        for l in locs:
            l.master_reference_asset_id = None
            l.is_approved = False

        # 3. Unlink from shots
        shots = db.query(Shot).all()
        for sh in shots:
            if sh.reference_asset_ids and asset_id in sh.reference_asset_ids:
                updated_refs = [r for r in sh.reference_asset_ids if r != asset_id]
                sh.reference_asset_ids = updated_refs
                if not updated_refs and sh.status == ShotStatus.KEYFRAME_READY.value:
                    sh.status = ShotStatus.DRAFT.value

        # 4. Remove physical file from disk if present
        if asset.file_path:
            try:
                p = Path(asset.file_path)
                if p.exists():
                    p.unlink()
            except Exception:
                pass

        # 5. Remove DB row
        db.delete(asset)
        db.commit()
        return True
