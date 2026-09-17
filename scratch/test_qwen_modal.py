import modal

print("Testing live QwenAudioWorker on Modal Cloud...")
cls = modal.Cls.from_name("microdrama-studio-audio", "QwenAudioWorker")
instance = cls()

wav_bytes = instance.generate_speech.remote(
    text="Did you hear that? I'm telling you, someone else is in this building with us!",
    voice="Vivian",
    instruct="Speak in a terrified, breathless whisper, shaking with fear and dread",
    speed=1.0
)

print(f"✅ Success! Received {len(wav_bytes)} bytes of real speech audio from Modal Qwen3-TTS!")
with open("scratch/test_qwen_output.wav", "wb") as f:
    f.write(wav_bytes)
print("Saved sample to scratch/test_qwen_output.wav")
