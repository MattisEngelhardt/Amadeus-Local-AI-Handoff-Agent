import os
import sys
import time
import logging
import threading
import yaml
from dotenv import load_dotenv
from pynput import keyboard

# Import application modules
from speech_to_code.core.recorder import AudioRecorder
from speech_to_code.core.transcriber import AudioTranscriber
from speech_to_code.core.analyzer import TranscriptAnalyzer
from speech_to_code.core.validator import RequirementsValidator
from speech_to_code.core.generator import ProjectGenerator
from speech_to_code.core.scaffolder import ProjectScaffolder
from speech_to_code.ui.overlay import OverlayWindow
from speech_to_code.ui.tray import SystemTrayApp
from speech_to_code.ui.notification import notify_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("speech_to_code.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

class SpeechToCodeApp:
    def __init__(self):
        load_dotenv()
        self.config = self._load_config()

        # Resolve output directory
        self.output_dir = self.config.get("output_dir", "./output")
        if not os.path.isabs(self.output_dir):
            self.output_dir = os.path.abspath(self.output_dir)

        # Audio settings
        audio_config = self.config.get("audio", {})
        self.samplerate = audio_config.get("samplerate", 16000)
        self.channels = audio_config.get("channels", 1)
        self.temp_filename = audio_config.get("temp_filename", "temp_recording.wav")
        self.temp_filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", self.temp_filename))

        # Model settings
        model_config = self.config.get("models", {})
        self.whisper_model = model_config.get("whisper", "whisper-1")
        self.claude_model = model_config.get("claude", "claude-3-5-sonnet-20241022")
        self.gemini_model = model_config.get("gemini", "gemini-1.5-pro")
        self.llm_provider = model_config.get("llm_provider", "claude")
        self.whisper_mode = model_config.get("whisper_mode", "api")
        self.whisper_local_model = model_config.get("whisper_local_model", "base")

        if self.llm_provider == "gemini":
            self.llm_model = self.gemini_model
        else:
            self.llm_model = self.claude_model

        # Initialize core elements
        self.recorder = AudioRecorder(samplerate=self.samplerate, channels=self.channels)
        self.transcriber = AudioTranscriber(
            model=self.whisper_model,
            whisper_mode=self.whisper_mode,
            whisper_local_model=self.whisper_local_model
        )
        
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.yaml"))
        self.analyzer = TranscriptAnalyzer(model=self.llm_model, config_path=config_path, llm_provider=self.llm_provider)
        self.validator = RequirementsValidator(model=self.llm_model, llm_provider=self.llm_provider)
        self.generator = ProjectGenerator(model=self.llm_model, llm_provider=self.llm_provider)
        self.scaffolder = ProjectScaffolder(base_output_dir=self.output_dir)

        # Initialize UI elements
        self.overlay = OverlayWindow()
        self.tray = SystemTrayApp(
            on_toggle_recording=self.toggle_recording,
            on_change_output=self.change_output_directory,
            on_exit=self.exit_app
        )

        self.is_processing = False
        self.running = True
        self.hotkey_listener = None

    def _load_config(self):
        """Loads configuration from config.yaml."""
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.yaml"))
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}. Using empty default config.")
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def save_output_dir_to_config(self, new_dir):
        """Saves a new output directory into the config.yaml."""
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.yaml"))
        self.config["output_dir"] = new_dir
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.config, f)
            logger.info(f"Saved new output directory to config: {new_dir}")
        except Exception as e:
            logger.error(f"Failed to save output dir to config file: {e}")

    def start(self):
        """Starts all components of the application."""
        # 1. Start overlay
        self.overlay.start()

        # 2. Check API keys depending on configuration
        missing_keys = []
        if self.whisper_mode == "api" and not os.getenv("OPENAI_API_KEY"):
            missing_keys.append("OPENAI_API_KEY (required for Cloud Whisper)")
        
        if self.llm_provider == "claude" and not os.getenv("ANTHROPIC_API_KEY"):
            missing_keys.append("ANTHROPIC_API_KEY (required for Claude)")
        elif self.llm_provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
            missing_keys.append("GEMINI_API_KEY (required for Google Gemini)")

        if missing_keys:
            msg = f"Missing API keys: {', '.join(missing_keys)}. Please define them in your .env file."
            logger.error(msg)
            notify_user("Speech to Code Error", "API Keys are missing in .env file.")
            # Show overlay with error message
            time.sleep(1) # wait for overlay thread to init
            self.overlay.show()
            self.overlay.update_status("❌ Error: API Keys Missing", "#FF3B30")
            self.overlay.hide_delayed(10.0)

        # 3. Start system tray
        self.tray.run()

        # 4. Bind global hotkey
        hotkey_combo = self.config.get("hotkey", "ctrl+space")
        logger.info(f"Binding global hotkey: {hotkey_combo}")
        
        # pynput keyboard mapping helper
        # pynput requires format like '<ctrl>+<space>' or '<ctrl_l>+<space>'
        # Normalize the configuration string
        pynput_combo = hotkey_combo.lower().replace("ctrl", "<ctrl>").replace("shift", "<shift>").replace("space", "<space>")
        pynput_combo = pynput_combo.replace("++", "+") # catch duplicate formatting

        try:
            self.hotkey_listener = keyboard.GlobalHotKeys({
                pynput_combo: self.toggle_recording
            })
            self.hotkey_listener.start()
            logger.info("Global hotkey listener started.")
        except Exception as e:
            logger.error(f"Failed to start hotkey listener: {e}")

        # Keep main thread alive
        logger.info("Speech to Code is running. Press Ctrl+Space to record.")
        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received.")
            self.exit_app()

    def toggle_recording(self):
        """Action handler when hotkey is triggered."""
        if self.is_processing:
            logger.warning("Application is currently processing. Toggle recording request ignored.")
            return

        if not self.recorder.recording:
            # START RECORDING
            self.overlay.show()
            self.overlay.update_status("🎙️ Starting recording...", "#FF453A")
            success = self.recorder.start_recording(self.temp_filepath)
            
            if success:
                self.tray.set_recording_state(True)
                # Launch thread to update duration in overlay
                threading.Thread(target=self._update_overlay_timer, daemon=True).start()
        else:
            # STOP RECORDING & PROCESS
            self.is_processing = True
            self.tray.set_recording_state(False)
            self.overlay.update_status("🛑 Stopping recording...", "#FF9500")
            
            # Stop recorder and get filename
            audio_file = self.recorder.stop_recording()
            
            if not audio_file or not os.path.exists(audio_file):
                logger.error("Recording failed or no audio data captured.")
                self.overlay.update_status("❌ Error: No audio captured", "#FF3B30")
                self.overlay.hide_delayed(3.0)
                self.is_processing = False
                return

            # Start pipeline in worker thread to prevent locking the tray/GUI threads
            threading.Thread(target=self._process_pipeline, args=(audio_file,), daemon=True).start()

    def _update_overlay_timer(self):
        """Periodically updates the overlay text with the current recording duration."""
        while self.recorder.recording:
            duration = self.recorder.get_duration()
            mins = int(duration // 60)
            secs = int(duration % 60)
            status_text = f"🔴 Recording ({mins}:{secs:02d})"
            self.overlay.update_status(status_text, "#FF453A")
            time.sleep(0.5)

    def _process_pipeline(self, audio_file):
        """Background worker executing transcription, analysis, validation, and scaffolding."""
        try:
            # 1. Transcribe
            self.overlay.update_status("☁️ Transcribing audio...", "#0A84FF")
            transcript = self.transcriber.transcribe(audio_file)
            
            if not transcript:
                logger.error("Transcription failed.")
                self.overlay.update_status("❌ Error: Transcription failed", "#FF3B30")
                self.overlay.hide_delayed(4.0)
                return

            logger.info(f"Transcript received: {transcript[:100]}...")

            # 2. Analyze
            self.overlay.update_status("🧠 Analyzing requirements...", "#5E5CE6")
            requirements = self.analyzer.analyze(transcript)
            if not requirements:
                logger.error("Analysis failed.")
                self.overlay.update_status("❌ Error: Requirements analysis failed", "#FF3B30")
                self.overlay.hide_delayed(4.0)
                return

            # 3. Validate
            self.overlay.update_status("⚖️ Auditing requirements...", "#FF9500")
            validated_requirements = self.validator.validate(transcript, requirements)

            # 4. Generate
            self.overlay.update_status("⚙️ Generating project code...", "#BF5AF2")
            generated_files = self.generator.generate_all_files(validated_requirements)
            if not generated_files:
                logger.error("Code generation failed.")
                self.overlay.update_status("❌ Error: Code generation failed", "#FF3B30")
                self.overlay.hide_delayed(4.0)
                return

            # 5. Scaffold
            self.overlay.update_status("📂 Scaffolding files...", "#30D158")
            # Refresh output directory path in case it changed in config
            self.scaffolder.base_output_dir = self.output_dir
            project_path = self.scaffolder.scaffold(validated_requirements, generated_files)
            
            if project_path:
                logger.info(f"Project created at: {project_path}")
                self.overlay.update_status("✅ Project generated successfully!", "#30D158")
                notify_user(
                    "Speech to Code Success", 
                    f"Scaffolded '{validated_requirements.display_name}' in {validated_requirements.project_name}/"
                )
                
                # Cleanup temp file
                try:
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
                except Exception as e:
                    logger.warning(f"Could not delete temp file: {e}")
            else:
                logger.error("Scaffolding failed.")
                self.overlay.update_status("❌ Error: Directory scaffolding failed", "#FF3B30")

            self.overlay.hide_delayed(4.0)

        except Exception as e:
            logger.error(f"Error in Speech to Code processing pipeline: {e}")
            self.overlay.update_status(f"❌ Error: {str(e)[:30]}...", "#FF3B30")
            self.overlay.hide_delayed(4.0)
        finally:
            self.is_processing = False

    def change_output_directory(self):
        """Triggers the directory chooser dialog thread-safely."""
        logger.info("Opening directory select dialog...")
        
        def _update_output_dir(selected_dir):
            if selected_dir:
                self.output_dir = selected_dir
                self.save_output_dir_to_config(selected_dir)
                notify_user("Output Directory Updated", f"New projects will be saved to:\n{selected_dir}")
                logger.info(f"Updated output directory to: {selected_dir}")

        self.overlay.select_directory(_update_output_dir)

    def exit_app(self):
        """Stops listeners and exits cleanly."""
        logger.info("Shutting down Speech to Code...")
        self.running = False
        
        # Stop tray icon
        if self.tray:
            self.tray.stop()
            
        # Stop hotkey listener
        if self.hotkey_listener:
            self.hotkey_listener.stop()

        # Close Tkinter overlay
        if self.overlay and self.overlay.root:
            try:
                self.overlay.root.quit()
                self.overlay.root.destroy()
            except Exception:
                pass

        sys.exit(0)

if __name__ == "__main__":
    app = SpeechToCodeApp()
    app.start()
