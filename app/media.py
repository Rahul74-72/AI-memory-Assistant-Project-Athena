"""Decode uploads as data, strip image metadata, and transcribe locally."""
import io
import os
import threading
import warnings
from functools import lru_cache

from PIL import Image, ImageOps, UnidentifiedImageError
from app.settings import MAX_UPLOAD, WHISPER_MODEL

Image.MAX_IMAGE_PIXELS = 16_000_000
_speech_gate = threading.BoundedSemaphore(1)


def clean_image(data):
    if not data or len(data) > MAX_UPLOAD:
        raise ValueError("Upload a nonempty image smaller than 8 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as picture:
                if picture.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Only JPEG, PNG and WebP images are supported.")
                picture.load()
                picture = ImageOps.exif_transpose(picture).convert("RGB")
                picture.thumbnail((1600, 1600))
                output = io.BytesIO()
                picture.save(output, "JPEG", quality=85)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("Invalid or oversized image.") from exc


@lru_cache(maxsize=1)
def speech_model():
    from faster_whisper import WhisperModel
    return WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8", cpu_threads=4,
                        local_files_only=os.environ.get("ATHENA_MODEL_DOWNLOADS", "0") != "1")


def transcribe(data):
    if not data or len(data) > MAX_UPLOAD:
        raise ValueError("Audio must be nonempty and smaller than 8 MB.")
    if not _speech_gate.acquire(blocking=False):
        raise ValueError("Speech recognition is busy. Try again shortly.")
    try:
        import av
        import numpy as np
        # Decode with a strict duration bound before handing audio to Whisper.
        samples = []
        total = 0
        with av.open(io.BytesIO(data)) as container:
            if not container.streams.audio:
                raise ValueError("The file contains no audio.")
            resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
            for frame in container.decode(audio=0):
                for converted in resampler.resample(frame):
                    total += converted.samples
                    if total > 16000 * 90:
                        raise ValueError("Audio is limited to 90 seconds.")
                    samples.append(converted.to_ndarray().flatten())
        if not samples:
            raise ValueError("No speech audio found.")
        audio = np.concatenate(samples).astype(np.float32) / 32768
        segments, info = speech_model().transcribe(audio, beam_size=1, vad_filter=True)
        return {"text": " ".join(s.text.strip() for s in segments).strip(), "language": info.language}
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError("Local transcription failed. Check the audio and Whisper installation.") from exc
    finally:
        _speech_gate.release()
