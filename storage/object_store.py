import shutil
from pathlib import Path
from typing import Optional, Union

class LocalObjectStore:
    """Local filesystem-backed object store. Can be swapped for S3/R2 in production."""

    @staticmethod
    def save_file(source_data: Union[bytes, Path], destination_path: Path) -> Path:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(source_data, bytes):
            with open(destination_path, "wb") as f:
                f.write(source_data)
        elif isinstance(source_data, Path):
            shutil.copy2(source_data, destination_path)
        return destination_path

    @staticmethod
    def read_file(file_path: Path) -> Optional[bytes]:
        if not file_path.exists():
            return None
        with open(file_path, "rb") as f:
            return f.read()

    @staticmethod
    def exists(file_path: Path) -> bool:
        return file_path.exists()
