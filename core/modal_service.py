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
            "name": "Lightricks LTX-2.5 Multimodal Engine (Video + Synchronized Audio)",
            "app_name": "microdrama-studio-video",
            "class_name": "LTXVideoGenerator",
            "worker_file": "modal/video_worker.py",
            "description": "Lightricks LTX-2.5 joint video & synchronized sound generation from text & image prompts (A100 or L4 GPU).",
            "gpu": "NVIDIA A100 / L4",
            "phase": "Phase 5 (Active)"
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
    def get_credentials(cls) -> Dict[str, str]:
        """Returns the currently configured Modal token ID, secret, and HF token."""
        from core.config import settings
        token_id = os.getenv("MODAL_TOKEN_ID", "") or getattr(settings, "MODAL_TOKEN_ID", "")
        token_secret = os.getenv("MODAL_TOKEN_SECRET", "") or getattr(settings, "MODAL_TOKEN_SECRET", "")
        hf_token = os.getenv("HF_TOKEN", "") or getattr(settings, "HF_TOKEN", "")
        return {
            "token_id": token_id,
            "token_secret": token_secret,
            "hf_token": hf_token,
            "environment": os.getenv("MODAL_ENVIRONMENT", "main")
        }

    @classmethod
    def save_credentials(
        cls,
        token_id: str,
        token_secret: str,
        environment: str = "main",
        hf_token: str = ""
    ) -> Tuple[bool, str]:
        """Saves Modal credentials to os.environ, updates .env file, and syncs modal CLI profile."""
        token_id = token_id.strip()
        token_secret = token_secret.strip()
        hf_token = hf_token.strip()
        if not token_id or not token_secret:
            return False, "Token ID and Token Secret cannot be empty."

        # 1. Update os.environ
        os.environ["MODAL_TOKEN_ID"] = token_id
        os.environ["MODAL_TOKEN_SECRET"] = token_secret
        os.environ["MODAL_ENVIRONMENT"] = environment
        if hf_token:
            os.environ["HF_TOKEN"] = hf_token

        # 2. Update settings in-memory
        from core.config import settings
        settings.MODAL_TOKEN_ID = token_id
        settings.MODAL_TOKEN_SECRET = token_secret
        settings.MODAL_ENVIRONMENT = environment
        if hf_token:
            settings.HF_TOKEN = hf_token

        # 3. Update local .env file if it exists
        try:
            env_file = settings.BASE_DIR / ".env"
            lines = []
            if env_file.exists():
                with open(env_file, "r") as f:
                    lines = f.readlines()

            id_set = False
            sec_set = False
            env_set = False
            hf_set = False
            new_lines = []
            for line in lines:
                if line.startswith("MODAL_TOKEN_ID="):
                    new_lines.append(f"MODAL_TOKEN_ID={token_id}\n")
                    id_set = True
                elif line.startswith("MODAL_TOKEN_SECRET="):
                    new_lines.append(f"MODAL_TOKEN_SECRET={token_secret}\n")
                    sec_set = True
                elif line.startswith("MODAL_ENVIRONMENT="):
                    new_lines.append(f"MODAL_ENVIRONMENT={environment}\n")
                    env_set = True
                elif line.startswith("HF_TOKEN="):
                    if hf_token:
                        new_lines.append(f"HF_TOKEN={hf_token}\n")
                        hf_set = True
                else:
                    new_lines.append(line)

            if not id_set:
                new_lines.append(f"MODAL_TOKEN_ID={token_id}\n")
            if not sec_set:
                new_lines.append(f"MODAL_TOKEN_SECRET={token_secret}\n")
            if not env_set:
                new_lines.append(f"MODAL_ENVIRONMENT={environment}\n")
            if hf_token and not hf_set:
                new_lines.append(f"HF_TOKEN={hf_token}\n")

            with open(env_file, "w") as f:
                f.writelines(new_lines)
        except Exception as e:
            print(f"Warning: Could not write credentials to .env: {e}")

        # 4. Sync with Modal CLI profile if available
        cli = cls.get_modal_cli_path()
        try:
            res = subprocess.run(
                [cli, "token", "set", "--token-id", token_id, "--token-secret", token_secret, "--no-verify"],
                capture_output=True,
                text=True,
                timeout=15
            )
            if res.returncode == 0:
                return True, "✅ Modal credentials saved and linked to Modal workspace!"
        except Exception as e_cli:
            print(f"CLI token set note: {e_cli}")

        return True, "✅ Modal credentials updated and saved successfully!"

    @classmethod
    def verify_credentials(cls) -> Tuple[bool, str]:
        """Tests if Modal is authenticated and accessible with the current credentials."""
        cli = cls.get_modal_cli_path()
        try:
            res = subprocess.run([cli, "app", "list", "--json"], capture_output=True, text=True, timeout=12)
            if res.returncode == 0:
                profile = cls.get_current_profile() or "active"
                return True, f"🟢 Successfully connected to Modal workspace (Profile: `{profile}`)!"
            else:
                err = res.stderr.strip() or res.stdout.strip()
                return False, f"❌ Modal authentication check failed: {err}"
        except Exception as e:
            return False, f"❌ Verification error: {str(e)}"


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
        inactivity_timeout_minutes: int = 15,
        target_gpu: str = "A100"
    ) -> Tuple[bool, str]:
        """Deploys a Modal worker script with configured inactivity auto-shutdown timer and target GPU."""
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
        env = os.environ.copy()
        env["MODAL_SCALEDOWN_WINDOW"] = str(scaledown_seconds)
        env["MODAL_VIDEO_GPU"] = target_gpu

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
