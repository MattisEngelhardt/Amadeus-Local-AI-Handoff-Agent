from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


class AudioTranscriber:
    def __init__(
        self,
        model: str | None = None,
        whisper_mode: str = "local",
        whisper_local_model: str = "large-v3",
        language: str = "de",
        **_legacy_kwargs: object,
    ) -> None:
        self.model = model or "faster-whisper"
        self.whisper_mode = whisper_mode
        self.whisper_local_model = whisper_local_model or "large-v3"
        self.language = language
        self._local_model = None

        if self.whisper_mode != "local":
            logger.warning(
                "Amadeus only supports local transcription in the core path. Using local mode."
            )
            self.whisper_mode = "local"

    def _transcribe_local(self, file_path: str) -> str | None:
        try:
            if not self._local_model:
                logger.info(
                    "Loading local faster-whisper model '%s'. First run may download model files.",
                    self.whisper_local_model,
                )
                from faster_whisper import WhisperModel

                self._local_model = WhisperModel(
                    self.whisper_local_model,
                    device="cpu",
                    compute_type="int8",
                )

            import numpy as np
            import scipy.io.wavfile as wav

            samplerate, data = wav.read(file_path)
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)

            if data.dtype == np.int16:
                data = data.astype(np.float32) / 32768.0
            elif data.dtype == np.int32:
                data = data.astype(np.float32) / 2147483648.0
            elif data.dtype == np.uint8:
                data = (data.astype(np.float32) - 128.0) / 128.0
            else:
                data = data.astype(np.float32)

            if samplerate != 16000:
                logger.warning("Audio samplerate is %sHz; 16000Hz is preferred.", samplerate)

            segments, _info = self._local_model.transcribe(
                data,
                beam_size=5,
                language=self.language,
            )
            return " ".join(segment.text for segment in segments).strip()
        except Exception as exc:
            logger.error("Local faster-whisper transcription failed: %s", exc)
            return None

    def transcribe(self, file_path: str) -> str | None:
        if not os.path.exists(file_path):
            logger.error("Audio file not found: %s", file_path)
            return None
        return self._transcribe_local(file_path)
