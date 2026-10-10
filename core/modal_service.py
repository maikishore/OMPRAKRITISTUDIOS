import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class ModalService:
    """Service to monitor, deploy, test, and stop Modal serverless GPU apps."""

    MODAL_CLI = sys.executable.replace("python", "modal") if "venv" in sys.executable else "modal"

    AVAILABLE_MODELS = [
        {
            "id": "image",
            "name": "FLUX Image Generator (L4 GPU)",
            "app_name": "microdrama-studio-image",
            "class_name": "FluxImageGenerator",
            "worker_file": "modal/image_worker.py",
            "description": "FLUX.1 [dev] / FLUX.2 Klein 4B with IP-Adapter face-locking and sequential CPU offload.",
            "gpu": "NVIDIA L4 (24GB VRAM)",
            "phase": "Phase 4 (Active)"
        },
        {
            "id": "video",
            "name": "LTX Video Generator (L4/A10G GPU)",
            "app_name": "microdrama-studio-video",
            "class_name": "LTXVideoGenerator",
            "worker_file": "modal/video_worker.py",
            "description": "LTX-Video 0.9.5 high-motion camera & character video generator.",
            "gpu": "NVIDIA L4 / A10G",
            "phase": "Phase 5"
        },
        {
            "id": "audio",
            "name": "Qwen3-TTS 1.7B Emotional Audio Engine",
            "app_name": "microdrama-studio-audio",
            "class_name": "QwenAudioWorker",
            "worker_file": "modal/audio_worker.py",
            "description": "Qwen3-TTS-12Hz-1.7B CustomVoice & VoiceDesign with natural language instruct emotion steering.",
            "gpu": "NVIDIA L4 (24GB VRAM)",
            "phase": "Voice / Dialogue"
        }
    ]

    @classmethod
    def get_modal_cli_path(cls) -> str:
        # Check if ./venv/bin/modal exists
        venv_modal = Path(sys.executable).parent / "modal"
        if venv_modal.exists():
            return str(venv_modal)
        return "modal"

    @classmethod
    def get_current_profile(cls) -> Optional[str]:
        """Returns the currently active Modal profile/workspace name."""
        cli = cls.get_modal_cli_path()
        try:
            res = subprocess.run([cli, "profile", "current"], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return None

    @classmethod
    def list_deployed_apps(cls) -> List[Dict[str, Any]]:
        """Returns a list of all deployed/running Modal apps."""
        cli = cls.get_modal_cli_path()
        try:
            res = subprocess.run([cli, "app", "list", "--json"], capture_output=True, text=True, timeout=15)
            if res.returncode == 0 and res.stdout.strip():
                return json.loads(res.stdout)
        except Exception as e:
            print(f"Error listing modal apps: {e}")
        return []

    @classmethod
    def is_app_deployed(cls, app_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Checks if a specific app is currently in deployed state."""
        apps = cls.list_deployed_apps()
        for a in apps:
            if a.get("description") == app_name and a.get("state") == "deployed":
                return True, a
        return False, None

    @classmethod
    def deploy_worker(
        cls,
        worker_file: str,
        root_dir: Optional[Path] = None,
        inactivity_timeout_minutes: int = 15
    ) -> Tuple[bool, str]:
        """Deploys a Modal worker script with configured inactivity auto-shutdown timer."""
        cli = cls.get_modal_cli_path()
        cwd = str(root_dir) if root_dir else None
        
        # Verify file exists
        p = Path(worker_file)
        if cwd:
            full_p = Path(cwd) / worker_file
        else:
            full_p = p
            
        if not full_p.exists():
            return False, f"Worker file not found: {full_p}"

        # Convert minutes to seconds for scaledown_window
        scaledown_seconds = max(60, inactivity_timeout_minutes * 60)
        env = os.environ.copy() if "os" in globals() else {}
        import os
        env = os.environ.copy()
        env["MODAL_SCALEDOWN_WINDOW"] = str(scaledown_seconds)

        try:
            res = subprocess.run(
                [cli, "deploy", worker_file],
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=180
            )
            output = res.stdout + "\n" + res.stderr
            if res.returncode == 0:
                return True, output.strip()
            return False, output.strip()
        except Exception as e:
            return False, f"Deployment failed with error: {str(e)}"

    @classmethod
    def stop_app(cls, app_identifier: str) -> Tuple[bool, str]:
        """Stops an active Modal app and terminates all running GPU containers."""
        cli = cls.get_modal_cli_path()
        try:
            res = subprocess.run(
                [cli, "app", "stop", "-y", app_identifier],
                capture_output=True,
                text=True,
                timeout=30
            )
            output = res.stdout + "\n" + res.stderr
            if res.returncode == 0:
                return True, f"Successfully stopped app '{app_identifier}'."
            return False, output.strip()
        except Exception as e:
            return False, f"Stop failed with error: {str(e)}"

    @classmethod
    def test_connection(cls, app_name: str, class_name: str) -> Tuple[bool, str]:
        """Performs a lookup test against a deployed Modal app/class."""
        try:
            import modal
            remote_cls = modal.Cls.from_name(app_name, class_name)
            if remote_cls:
                return True, f"✅ Connection verified: Successfully located `{app_name}.{class_name}` on Modal."
            return False, f"❌ Failed to resolve `{app_name}.{class_name}` on Modal."
        except Exception as e:
            return False, f"❌ Connection test failed: {str(e)}"
