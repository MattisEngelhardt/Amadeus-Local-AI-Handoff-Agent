import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class AudioTranscriber:
    def __init__(self, api_key=None, model="whisper-1", whisper_mode="api", whisper_local_model="base"):
        """
        Initialize the Audio Transcriber.
        :param api_key: Optional OpenAI API key.
        :param model: Whisper API model identifier.
        :param whisper_mode: "api" or "local".
        :param whisper_local_model: Size of local model ("tiny", "base", etc.).
        """
        load_dotenv()
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.whisper_mode = whisper_mode
        self.whisper_local_model = whisper_local_model or "base"
        self._local_model = None
        self.client = None

        if self.whisper_mode == "api":
            if not self.api_key:
                logger.warning("OpenAI API key not found. Transcribing will fail in API mode unless key is provided.")
            else:
                self.client = OpenAI(api_key=self.api_key)

    def _transcribe_local(self, file_path):
        """Transcribes audio locally using faster-whisper without API calls."""
        try:
            if not self._local_model:
                logger.info(f"Loading local Whisper model '{self.whisper_local_model}' (first run may download files)...")
                from faster_whisper import WhisperModel
                # Runs on CPU with int8 quantization for portability and speed
                self._local_model = WhisperModel(self.whisper_local_model, device="cpu", compute_type="int8")

            logger.info(f"Transcribing audio file locally: {file_path}")
            
            import scipy.io.wavfile as wav
            import numpy as np

            samplerate, data = wav.read(file_path)

            # Ensure mono 1D float32 normalized data
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
                logger.warning(f"Audio samplerate is {samplerate}Hz but Whisper expects 16000Hz.")

            segments, info = self._local_model.transcribe(data, beam_size=5)
            transcript_text = " ".join([segment.text for segment in segments]).strip()
            logger.info("Local transcription completed successfully.")
            return transcript_text

        except Exception as e:
            logger.error(f"Error during local Whisper transcription: {e}")
            if self.api_key:
                logger.warning("Local transcription failed. Falling back to OpenAI API...")
                self.whisper_mode = "api"
                return self.transcribe(file_path)
            return None

    def transcribe(self, file_path):
        """
        Transcribes the given audio file using OpenAI's Whisper (API or local).
        :param file_path: Path to the audio file.
        :return: Transcribed text string, or None if transcription failed.
        """
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found: {file_path}")
            return None

        if self.whisper_mode == "local":
            return self._transcribe_local(file_path)

        # Re-initialize client if api_key was provided later or loaded
        if not self.client:
            self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                logger.error("Cannot transcribe: OpenAI API key is missing. Please set OPENAI_API_KEY.")
                return None
            self.client = OpenAI(api_key=self.api_key)

        logger.info(f"Sending {file_path} to OpenAI Whisper API...")
        try:
            with open(file_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file
                )
            
            transcript_text = response.text.strip()
            logger.info("Transcription completed successfully.")
            return transcript_text

        except Exception as e:
            logger.error(f"Error during OpenAI Whisper API call: {e}")
            return None
