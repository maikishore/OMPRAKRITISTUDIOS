"""Modal Serverless GPU Worker for FLUX Image Generation and Face Conditioning.

Based on proven high-performance FLUX setup in OHM (flux_klein_modal.py).
Deploy with: `modal deploy modal/image_worker.py`
"""

import os
import io
from typing import Optional

try:
    import modal
    app = modal.App("microdrama-studio-image")

    # Persistent Volume for caching model weights permanently across containers
    model_volume = modal.Volume.from_name("microdrama-model-cache", create_if_missing=True)

    # Define container image with diffusers & torch & fast transfer
    image_env = (
        modal.Image.debian_slim(python_version="3.11")
        .apt_install("git")
        .pip_install(
            "git+https://github.com/huggingface/diffusers.git",
            "transformers>=4.48.0",
            "accelerate>=0.33.0",
            "sentencepiece",
            "protobuf",
            "numpy",
            "torch",
            "pillow",
            "torchvision",
            "hf_transfer"
        )
        .env({
            "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            "HF_HOME": "/cache/huggingface"
        })
    )

    # Optional HF secrets (injected automatically if HF_TOKEN is in environment)
    secrets = []
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        secrets.append(modal.Secret.from_dict({"HF_TOKEN": hf_token}))

    # Inactivity shutdown window (in seconds)
    # Automatically terminates GPU instance if no requests arrive within this window.
    INACTIVITY_TIMEOUT_SECONDS = int(os.getenv("MODAL_SCALEDOWN_WINDOW", "900"))  # Default: 15 minutes (900s)

    @app.cls(
        image=image_env,
        gpu="L4",
        volumes={"/cache": model_volume},
        secrets=secrets,
        timeout=600,
        scaledown_window=INACTIVITY_TIMEOUT_SECONDS  # Keep warm for 15 minutes (900s) by default
    )
    class FluxImageGenerator:
        """Modal GPU Class running FLUX pipeline on L4 GPU with persistent caching & 10min warm window."""

        @modal.enter()
        def load_model(self):
            import torch

            print("🔥 Loading FLUX pipeline on L4 GPU...")
            
            # Try Flux2KleinPipeline first (4B parameters, optimal for 24GB L4)
            try:
                from diffusers import Flux2KleinPipeline
                print("Loading black-forest-labs/FLUX.2-klein-4B pipeline...")
                self.pipe = Flux2KleinPipeline.from_pretrained(
                    "black-forest-labs/FLUX.2-klein-4B",
                    torch_dtype=torch.bfloat16
                )
                self.pipe.enable_model_cpu_offload()
                print("✅ FLUX.2 Klein 4B loaded successfully!")
                return
            except Exception as e:
                print(f"Note: Klein 4B load attempted ({e}), loading FLUX.1 with sequential CPU offload...")

            # Fallback to FLUX.1 with sequential offload
            try:
                from diffusers import FluxPipeline
                self.pipe = FluxPipeline.from_pretrained(
                    "black-forest-labs/FLUX.1-schnell",
                    torch_dtype=torch.bfloat16
                )
                self.pipe.enable_sequential_cpu_offload()
                if hasattr(self.pipe, "vae"):
                    self.pipe.vae.enable_slicing()
                    self.pipe.vae.enable_tiling()
                print("✅ FLUX.1 Schnell loaded with sequential CPU offload & VAE slicing!")
            except Exception as e2:
                print(f"⚠️ Model load fallback: {e2}")
                self.pipe = None

        @modal.method()
        def generate_image(
            self,
            prompt: str,
            image_bytes: Optional[bytes] = None,
            strength: float = 0.75,
            num_inference_steps: int = 4,
            guidance_scale: float = 3.5,
            width: int = 768,
            height: int = 1344,
            seed: int = 42
        ) -> bytes:
            """Executes Text-to-Image or Image-to-Image inference on Modal GPU."""
            import torch
            from PIL import Image

            generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu").manual_seed(seed)

            if self.pipe:
                if image_bytes:
                    print(f"Running Image-to-Image / Face conditioning with prompt: {prompt[:80]}...")
                    init_image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((width, height))
                    try:
                        from diffusers import FluxImg2ImgPipeline
                        img2img = FluxImg2ImgPipeline.from_pipe(self.pipe)
                        result = img2img(
                            prompt=prompt,
                            image=init_image,
                            strength=strength,
                            num_inference_steps=num_inference_steps,
                            guidance_scale=guidance_scale,
                            generator=generator
                        ).images[0]
                    except Exception as e_img2img:
                        print(f"Img2Img fallback to standard pipe ({e_img2img})...")
                        result = self.pipe(
                            prompt=prompt,
                            width=width,
                            height=height,
                            num_inference_steps=num_inference_steps,
                            guidance_scale=guidance_scale,
                            generator=generator
                        ).images[0]
                else:
                    print(f"Running Text-to-Image generation with prompt: {prompt[:80]}...")
                    result = self.pipe(
                        prompt=prompt,
                        width=width,
                        height=height,
                        num_inference_steps=num_inference_steps,
                        guidance_scale=guidance_scale,
                        generator=generator
                    ).images[0]
            else:
                from PIL import ImageDraw
                result = Image.new("RGB", (width, height), color=(25, 25, 35))
                draw = ImageDraw.Draw(result)
                draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(200, 50, 50), width=4)
                draw.text((40, 60), "FLUX MODAL GPU (L4)", fill=(255, 255, 255))
                draw.text((40, 100), prompt[:150], fill=(200, 200, 200))

            buffer = io.BytesIO()
            result.save(buffer, format="PNG")
            return buffer.getvalue()

except ImportError:
    pass
