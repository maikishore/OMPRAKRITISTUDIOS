from pathlib import Path
from core.config import settings

class StoragePaths:
    @staticmethod
    def get_project_dir(project_id: str) -> Path:
        p = settings.STORAGE_ROOT / "projects" / project_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def get_character_dir(project_id: str, character_id: str) -> Path:
        p = StoragePaths.get_project_dir(project_id) / "characters" / character_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def get_location_dir(project_id: str, location_id: str) -> Path:
        p = StoragePaths.get_project_dir(project_id) / "locations" / location_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def get_keyframes_dir(project_id: str) -> Path:
        p = StoragePaths.get_project_dir(project_id) / "keyframes"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def get_videos_dir(project_id: str) -> Path:
        p = StoragePaths.get_project_dir(project_id) / "videos"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def get_final_dir(project_id: str) -> Path:
        p = StoragePaths.get_project_dir(project_id) / "final"
        p.mkdir(parents=True, exist_ok=True)
        return p
