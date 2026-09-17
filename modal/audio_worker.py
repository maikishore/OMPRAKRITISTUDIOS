"""Modal Serverless Worker for Qwen3-TTS 1.7B Voice Synthesis & Dialogue Generation.

Supports:
- Qwen3-TTS-12Hz-1.7B-CustomVoice with natural language `instruct` emotion control
- 10-minute warm keep-alive on NVIDIA L4 GPU

Deploy with: `modal deploy modal/audio_worker.py`
"""

import io
from typing import Optional

try:
    import modal
    app = modal.App("microdrama-studio-audio")

    audio_volume = modal.Volume.from_name("microdrama-audio-cache", create_if_missing=True)

    image_env = (
        modal.Image.debian_slim(python_version="3.11")
        .apt_install("git", "ffmpeg", "libsndfile1")
        .pip_install(
            "qwen-tts>=0.1.1",
            "torch>=2.4.0",
            "torchaudio>=2.4.0",
            "transformers>=4.48.0",
            "accelerate>=0.34.0",
            "soundfile>=0.13.1",
            "huggingface_hub>=0.25.0",
            "scipy>=1.15.0",
            "numpy>=1.26.0"
        )
        .env({
            "HF_HOME": "/cache/huggingface"
        })
    )

    @app.cls(
        image=image_env,
        gpu="L4",
        volumes={"/cache": audio_volume},
        timeout=300,
        scaledown_window=600  # 10 minutes warm keep-alive
    )
    class QwenAudioWorker:
        """Serverless Qwen3-TTS 1.7B Worker for emotional character dialogue."""

        @modal.enter()
        def load_qwen_tts(self):
            import torch
            from qwen_tts import Qwen3TTSModel

            print("🔊 Initializing Qwen3-TTS 1.7B Pipeline on Modal GPU...")
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
            model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
            print(f"Loading {model_id} onto {self.device}...")
            
            self.model = Qwen3TTSModel.from_pretrained(
                model_id,
                device_map=self.device,
                dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32
            )
            print("✅ Qwen3-TTS 1.7B CustomVoice loaded successfully!")

        @modal.method()
        def generate_speech(
            self,
            text: str,
            voice: str = "vivian",
            instruct: Optional[str] = None,
            speed: float = 1.0
        ) -> bytes:
            """Synthesizes text into high-fidelity 24kHz WAV audio bytes with emotion instruct."""
            import soundfile as sf
            import numpy as np

            # Normalize speaker name to lowercase Qwen supported speakers
            v_clean = voice.replace("qwen_", "").lower()
            if v_clean in ["sarah", "lucy"]:
                v_clean = "vivian"
            elif v_clean in ["adam", "david"]:
                v_clean = "eric"
            elif v_clean in ["michael", "marcus", "uncle martin"]:
                v_clean = "uncle_martin"
            elif v_clean not in ["vivian", "eric", "uncle_martin", "serena", "ryan", "elena", "dylan"]:
                v_clean = "vivian"

            print(f"🎙️ Qwen3-TTS Generating speech for speaker '{v_clean}' | Instruct: '{instruct}' | Text: {text[:60]}...")

            # Execute Qwen3-TTS inference
            wavs, sr = self.model.generate_custom_voice(
                text=text.strip(),
                language="English",
                speaker=v_clean,
                instruct=instruct or "Speak with dramatic presence and authentic emotional tension"
            )

            # Extract numpy audio data from returned wavs (list or array)
            if isinstance(wavs, list) and len(wavs) > 0:
                audio_np = wavs[0]
            else:
                audio_np = wavs

            if hasattr(audio_np, "cpu"):
                audio_np = audio_np.cpu().numpy()
            elif not isinstance(audio_np, np.ndarray):
                audio_np = np.array(audio_np)

            if audio_np.ndim > 1:
                audio_np = audio_np.squeeze()

            buffer = io.BytesIO()
            sample_rate = sr if sr else 24000
            sf.write(buffer, audio_np, sample_rate, format="WAV")
            out_bytes = buffer.getvalue()
            print(f"✅ Qwen3-TTS speech synthesized successfully! Output size: {len(out_bytes)} bytes, Sample Rate: {sample_rate}Hz")
            return out_bytes

except ImportError:
    pass
