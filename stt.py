import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
import config

_model = None


def _get_model():
    global _model
    if _model is None:
        print("Loading STT model...", flush=True)
        _model = WhisperModel(
            config.STT_MODEL,
            device=config.STT_DEVICE,
            compute_type=config.STT_COMPUTE_TYPE,
        )
    return _model


def warm_up():
    """Load the STT model ahead of time so the first transcription is fast."""
    _get_model()


def _transcribe_array(audio) -> str:
    model = _get_model()
    segments, _ = model.transcribe(audio, language="en")
    return " ".join(seg.text.strip() for seg in segments).strip()


def record_and_transcribe() -> str:
    """Blocking push-to-talk used by the terminal app (main.py)."""
    frames = []

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    input("Press ENTER to start recording...")
    print("Recording... press ENTER to stop.", flush=True)

    with sd.InputStream(
        samplerate=config.AUDIO_SAMPLE_RATE,
        channels=config.AUDIO_CHANNELS,
        dtype=config.AUDIO_DTYPE,
        callback=callback,
    ):
        input()

    print("Transcribing...", flush=True)

    if not frames:
        return ""

    audio = np.concatenate(frames, axis=0).flatten()
    return _transcribe_array(audio)


class Recorder:
    """Start/stop microphone recording, driven by the web frontend."""

    def __init__(self):
        self._frames = []
        self._stream = None

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def start(self):
        self._frames = []

        def callback(indata, frame_count, time_info, status):
            self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=config.AUDIO_SAMPLE_RATE,
            channels=config.AUDIO_CHANNELS,
            dtype=config.AUDIO_DTYPE,
            callback=callback,
        )
        self._stream.start()

    def stop(self) -> str:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            return ""

        audio = np.concatenate(self._frames, axis=0).flatten()
        return _transcribe_array(audio)
