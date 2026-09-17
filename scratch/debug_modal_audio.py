import modal

app = modal.App.lookup("microdrama-studio-audio")
cls = modal.Cls.from_name("microdrama-studio-audio", "QwenAudioWorker")
worker = cls()

print("Calling QwenAudioWorker.generate_speech.remote...")
try:
    res = worker.generate_speech.remote(
        text="Did you hear that? I'm telling you, someone else is in this building with us!",
        voice="Vivian",
        instruct="Speak in a terrified whisper",
        speed=1.0
    )
    print(f"Returned bytes: {len(res)}")
except Exception as e:
    print(f"Exception during remote call: {e}")
