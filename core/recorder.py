import logging
import os
import queue
import threading
import time

import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class AudioRecorder:
    def __init__(self, samplerate=16000, channels=1):
        """
        Initialize the Audio Recorder.
        :param samplerate: Sampling rate in Hz (16000 is default for Whisper)
        :param channels: Number of channels (1 = mono, 2 = stereo)
        """
        self.samplerate = samplerate
        self.channels = channels
        self.recording = False
        self.audio_queue = queue.Queue()
        self.thread = None
        self.filename = None
        self.start_time = None
        self.elapsed_time = 0.0

    def _callback(self, indata, frames, time_info, status):
        """This is called for each audio block by sounddevice."""
        if status:
            logger.warning(f"Sounddevice warning: {status}")
        self.audio_queue.put(indata.copy())

    def start_recording(self, filename="temp_recording.wav"):
        """Starts recording audio in a background thread."""
        if self.recording:
            logger.warning("Recording is already in progress.")
            return False

        self.filename = filename
        # Ensure output directory exists for the temp recording
        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        self.recording = True
        self.audio_queue = queue.Queue()
        self.start_time = time.time()
        self.elapsed_time = 0.0

        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started recording, saving to {filename}")
        return True

    def _record_loop(self):
        """Internal recording loop running in background thread."""
        try:
            with sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                callback=self._callback,
                dtype='int16' # Use 16-bit PCM for clean WAV output
            ):
                while self.recording:
                    self.elapsed_time = time.time() - self.start_time
                    sd.sleep(100)
        except Exception as e:
            logger.error(f"Error in recording stream: {e}")
            self.recording = False

    def get_duration(self):
        """Returns the current recording duration in seconds."""
        if self.recording and self.start_time:
            return time.time() - self.start_time
        return self.elapsed_time

    def stop_recording(self):
        """Stops the recording thread and writes the wave file."""
        if not self.recording:
            logger.warning("No recording to stop.")
            return None

        self.recording = False
        if self.thread:
            self.thread.join()

        logger.info("Recording stopped. Processing audio data...")

        # Collect all audio chunks from queue
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())

        if not audio_data:
            logger.error("No audio data was captured.")
            return None

        # Concatenate all blocks
        audio_np = np.concatenate(audio_data, axis=0)

        # Write WAV file
        try:
            wav.write(self.filename, self.samplerate, audio_np)
            logger.info(f"Audio saved successfully to {self.filename}")
            return self.filename
        except Exception as e:
            logger.error(f"Failed to write audio file: {e}")
            return None

# Quick local test runner
if __name__ == "__main__":
    recorder = AudioRecorder()
    print("Press enter to start recording...")
    input()
    recorder.start_recording("test_run.wav")
    print("Recording... Press enter to stop.")
    while recorder.recording:
        try:
            time.sleep(0.5)
            print(f"Duration: {recorder.get_duration():.1f}s", end="\r")
        except KeyboardInterrupt:
            break
    input()
    file_path = recorder.stop_recording()
    print(f"\nRecording stopped. Saved to {file_path}")
