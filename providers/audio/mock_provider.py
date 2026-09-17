import io
import math
import struct
from providers.audio.base import AudioProvider, AudioGenerationRequest, AudioGenerationResult

class MockAudioProvider(AudioProvider):
    """Generates synthetic WAV audio tone for rapid local testing without cloud dependencies."""

    def generate_speech(self, request: AudioGenerationRequest) -> AudioGenerationResult:
        sample_rate = 24000
        # Estimate duration roughly based on word count (avg 3 words per second, min 1.5s)
        word_count = max(1, len(request.text.split()))
        duration = max(1.5, word_count * 0.35)
        num_samples = int(sample_rate * duration)

        # Generate a pleasant multi-harmonic tone
        freq = 440.0 if "am_" in request.voice else 660.0
        audio_data = bytearray()
        for i in range(num_samples):
            t = float(i) / sample_rate
            # Add simple envelope fade in/out
            envelope = min(1.0, i / 1000.0) * min(1.0, (num_samples - i) / 1000.0)
            sample = 0.5 * math.sin(2.0 * math.pi * freq * t) + 0.25 * math.sin(2.0 * math.pi * (freq * 1.5) * t)
            val = int(sample * envelope * 32767.0)
            val = max(-32768, min(32767, val))
            audio_data.extend(struct.pack("<h", val))

        # Build standard RIFF WAV header
        header = bytearray()
        header.extend(b"RIFF")
        header.extend(struct.pack("<I", 36 + len(audio_data)))
        header.extend(b"WAVE")
        header.extend(b"fmt ")
        header.extend(struct.pack("<I", 16)) # Subchunk1Size
        header.extend(struct.pack("<H", 1))  # AudioFormat (PCM)
        header.extend(struct.pack("<H", 1))  # NumChannels (Mono)
        header.extend(struct.pack("<I", sample_rate))
        header.extend(struct.pack("<I", sample_rate * 2)) # ByteRate
        header.extend(struct.pack("<H", 2))  # BlockAlign
        header.extend(struct.pack("<H", 16)) # BitsPerSample
        header.extend(b"data")
        header.extend(struct.pack("<I", len(audio_data)))

        wav_bytes = bytes(header + audio_data)

        return AudioGenerationResult(
            audio_bytes=wav_bytes,
            sample_rate=sample_rate,
            duration_seconds=round(duration, 2),
            mime_type="audio/wav",
            parameters={"provider": "mock", "voice": request.voice, "words": word_count}
        )
