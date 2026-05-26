from __future__ import annotations

import logging
import os
import sys
import threading
import time
from typing import Any

import yaml
from amadeus.core.analyzer import TranscriptAnalyzer
from amadeus.core.ollama_client import OllamaClient
from amadeus.core.recorder import AudioRecorder
from amadeus.core.transcriber import AudioTranscriber
from amadeus.core.validator import RequirementsValidator
from amadeus.core.workflow import prepare_handoff_workspace
from amadeus.ui.notification import notify_user
from amadeus.ui.overlay import OverlayWindow
from amadeus.ui.tray import SystemTrayApp
from dotenv import load_dotenv
from pynput import keyboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("amadeus.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


class AmadeusApp:
    def __init__(self) -> None:
        load_dotenv()
        self.config = self._load_config()

        self.output_dir = self._absolute_path(self.config.get("output_dir", "./output"))

        audio_config = self.config.get("audio", {})
        self.samplerate = int(audio_config.get("samplerate", 16000))
        self.channels = int(audio_config.get("channels", 1))
        self.temp_filename = str(audio_config.get("temp_filename", "temp_recording.wav"))
        self.temp_filepath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), self.temp_filename)
        )

        model_config = self.config.get("models", {})
        self.ollama_base_url = str(model_config.get("ollama_base_url", "http://localhost:11434"))
        self.llm_model = str(model_config.get("ollama_model", "amadeus"))
        self.base_model = str(model_config.get("base_model", "gemma4:e4b"))
        self.whisper_local_model = str(model_config.get("whisper_local_model", "large-v3"))
        self.transcription_language = str(model_config.get("transcription_language", "de"))

        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.yaml"))
        ollama_client = OllamaClient(base_url=self.ollama_base_url)

        self.recorder = AudioRecorder(samplerate=self.samplerate, channels=self.channels)
        self.transcriber = AudioTranscriber(
            whisper_local_model=self.whisper_local_model,
            language=self.transcription_language,
        )
        self.analyzer = TranscriptAnalyzer(
            model=self.llm_model,
            config_path=config_path,
            ollama_base_url=self.ollama_base_url,
            client=ollama_client,
        )
        self.validator = RequirementsValidator()

        self.overlay = OverlayWindow()
        self.tray = SystemTrayApp(
            on_toggle_recording=self.toggle_recording,
            on_change_output=self.change_output_directory,
            on_exit=self.exit_app,
        )

        self.is_processing = False
        self.running = True
        self.hotkey_listener: keyboard.GlobalHotKeys | None = None

    def _load_config(self) -> dict[str, Any]:
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.yaml"))
        if not os.path.exists(config_path):
            logger.warning("Config file not found at %s. Using defaults.", config_path)
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as handle:
                return yaml.safe_load(handle) or {}
        except Exception as exc:
            logger.error("Failed to load config: %s", exc)
            return {}

    def _absolute_path(self, path: str) -> str:
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(os.path.dirname(__file__), path))

    def save_output_dir_to_config(self, new_dir: str) -> None:
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.yaml"))
        self.config["output_dir"] = new_dir
        try:
            with open(config_path, "w", encoding="utf-8") as handle:
                yaml.safe_dump(self.config, handle, sort_keys=False)
            logger.info("Saved new output directory to config: %s", new_dir)
        except Exception as exc:
            logger.error("Failed to save output directory to config: %s", exc)

    def start(self) -> None:
        self.overlay.start()
        self._report_runtime_status()
        self.tray.run()
        self._bind_hotkey()

        logger.info("Amadeus is running. Press Ctrl+Space to record.")
        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.exit_app()

    def _report_runtime_status(self) -> None:
        try:
            models = self.analyzer.client.list_models()
        except Exception as exc:
            logger.warning("Ollama is not reachable: %s", exc)
            notify_user(
                "Amadeus Runtime Missing",
                "Install Ollama and run: ollama pull gemma4:e4b",
            )
            return

        missing = [model for model in (self.base_model, self.llm_model) if model not in models]
        if missing:
            logger.warning("Missing local Ollama models: %s", ", ".join(missing))
            notify_user(
                "Amadeus Model Missing",
                f"Missing: {', '.join(missing)}",
            )
        else:
            logger.info("Ollama and required Amadeus models are available.")

    def _bind_hotkey(self) -> None:
        hotkey_combo = str(self.config.get("hotkey", "ctrl+space"))
        pynput_combo = (
            hotkey_combo.lower()
            .replace("ctrl", "<ctrl>")
            .replace("shift", "<shift>")
            .replace("space", "<space>")
            .replace("++", "+")
        )

        try:
            self.hotkey_listener = keyboard.GlobalHotKeys({pynput_combo: self.toggle_recording})
            self.hotkey_listener.start()
            logger.info("Global hotkey listener started: %s", hotkey_combo)
        except Exception as exc:
            logger.error("Failed to start hotkey listener: %s", exc)

    def toggle_recording(self) -> None:
        if self.is_processing:
            logger.warning("Amadeus is currently processing. Toggle ignored.")
            return

        if not self.recorder.recording:
            self.overlay.show()
            self.overlay.update_status("Amadeus recording...", "#FF453A")
            success = self.recorder.start_recording(self.temp_filepath)
            if success:
                self.tray.set_recording_state(True)
                threading.Thread(target=self._update_overlay_timer, daemon=True).start()
            return

        self.is_processing = True
        self.tray.set_recording_state(False)
        self.overlay.update_status("Stopping recording...", "#FF9500")
        audio_file = self.recorder.stop_recording()

        if not audio_file or not os.path.exists(audio_file):
            logger.error("Recording failed or no audio data captured.")
            self.overlay.update_status("Error: no audio captured", "#FF3B30")
            self.overlay.hide_delayed(3.0)
            self.is_processing = False
            return

        threading.Thread(target=self._process_pipeline, args=(audio_file,), daemon=True).start()

    def _update_overlay_timer(self) -> None:
        while self.recorder.recording:
            duration = self.recorder.get_duration()
            mins = int(duration // 60)
            secs = int(duration % 60)
            self.overlay.update_status(f"Recording ({mins}:{secs:02d})", "#FF453A")
            time.sleep(0.5)

    def _process_pipeline(self, audio_file: str) -> None:
        try:
            self.overlay.update_status("Transcribing locally...", "#0A84FF")
            transcript = self.transcriber.transcribe(audio_file)
            if not transcript:
                logger.error("Transcription failed.")
                self.overlay.update_status("Error: transcription failed", "#FF3B30")
                self.overlay.hide_delayed(4.0)
                return

            self.overlay.update_status("Analyzing with local Gemma...", "#5E5CE6")
            requirements = self.analyzer.analyze(transcript)
            if not requirements:
                logger.error("Gemma analysis failed.")
                self.overlay.update_status("Error: Gemma analysis failed", "#FF3B30")
                self.overlay.hide_delayed(4.0)
                return

            self.overlay.update_status("Validating handoff plan...", "#FF9500")
            validated_requirements = self.validator.validate(transcript, requirements)

            self.overlay.update_status("Running readiness gate...", "#FF9500")
            result = prepare_handoff_workspace(
                validated_requirements,
                raw_text=transcript,
                output_dir=self.output_dir,
                channel="desktop_speechbar",
                input_kind="audio",
                transcript_language=self.transcription_language,
            )

            if result.blocked:
                logger.warning("Readiness gate blocked workspace build: %s", result.project_path)
                self.overlay.update_status("Readiness review needed", "#FF9500")
                notify_user(
                    "Amadeus Readiness Review",
                    f"Open blockers saved in:\n{result.project_path}",
                )
                self._delete_temp_file(audio_file)
            elif result.built:
                logger.info("Amadeus handoff workspace created at: %s", result.project_path)
                self.overlay.update_status("Handoff workspace ready", "#30D158")
                notify_user(
                    "Amadeus Workspace Ready",
                    f"Created '{validated_requirements.display_name}'",
                )
                self._delete_temp_file(audio_file)
            else:
                logger.error("Workspace scaffolding failed: %s", result.message)
                self.overlay.update_status("Error: workspace build failed", "#FF3B30")

            self.overlay.hide_delayed(4.0)
        except Exception as exc:
            logger.error("Error in Amadeus processing pipeline: %s", exc)
            self.overlay.update_status(f"Error: {str(exc)[:30]}", "#FF3B30")
            self.overlay.hide_delayed(4.0)
        finally:
            self.is_processing = False

    def _write_raw_input(self, project_path: str, transcript: str) -> None:
        logs_dir = os.path.join(project_path, "_logs")
        os.makedirs(logs_dir, exist_ok=True)
        with open(os.path.join(logs_dir, "raw_input.md"), "w", encoding="utf-8") as handle:
            handle.write(f"# Raw Input\n\n{transcript.strip()}\n")

    def _delete_temp_file(self, audio_file: str) -> None:
        try:
            if os.path.exists(audio_file):
                os.remove(audio_file)
        except Exception as exc:
            logger.warning("Could not delete temp file: %s", exc)

    def change_output_directory(self) -> None:
        logger.info("Opening directory select dialog.")

        def _update_output_dir(selected_dir: str) -> None:
            if selected_dir:
                self.output_dir = selected_dir
                self.save_output_dir_to_config(selected_dir)
                notify_user(
                    "Amadeus Output Updated",
                    f"New workspaces will be saved to:\n{selected_dir}",
                )

        self.overlay.select_directory(_update_output_dir)

    def exit_app(self) -> None:
        logger.info("Shutting down Amadeus.")
        self.running = False

        if self.tray:
            self.tray.stop()
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        if self.overlay and self.overlay.root:
            try:
                self.overlay.root.quit()
                self.overlay.root.destroy()
            except Exception:
                pass

        sys.exit(0)


SpeechToCodeApp = AmadeusApp


if __name__ == "__main__":
    app = AmadeusApp()
    app.start()
