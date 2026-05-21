import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Ensure parent directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from speech_to_code.main import SpeechToCodeApp
from speech_to_code.core.recorder import AudioRecorder
from speech_to_code.core.transcriber import AudioTranscriber
from speech_to_code.core.analyzer import TranscriptAnalyzer
from speech_to_code.core.validator import RequirementsValidator
from speech_to_code.core.generator import ProjectGenerator
from speech_to_code.core.scaffolder import ProjectScaffolder
from speech_to_code.models.requirements import RequirementsModel

class SpeechToCodeIntegrationAudit(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_patcher = patch("speech_to_code.main.SpeechToCodeApp._load_config")
        self.mock_load_config = self.config_patcher.start()
        self.mock_load_config.return_value = {
            "output_dir": self.test_dir,
            "hotkey": "ctrl+space",
            "audio": {
                "samplerate": 16000,
                "channels": 1,
                "temp_filename": "temp_recording.wav"
            },
            "models": {
                "whisper": "whisper-1",
                "claude": "claude-3-5-sonnet-20241022"
            }
        }

    def tearDown(self):
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_agent_1_audio_record_lifecycle(self):
        """Agent 1: Verify audio recorder lifecycle transitions and stream initialization."""
        recorder = AudioRecorder(samplerate=16000, channels=1)
        self.assertFalse(recorder.recording)
        
        temp_wav = os.path.join(self.test_dir, "temp.wav")
        # Mock sounddevice InputStream to not open real audio hardware in tests
        with patch("speech_to_code.core.recorder.sd.InputStream") as mock_input_stream:
            success = recorder.start_recording(temp_wav)
            self.assertTrue(success)
            self.assertTrue(recorder.recording)
            
            # Put dummy data to audio queue to simulate recording callback
            import numpy as np
            recorder.audio_queue.put(np.zeros((1600, 1), dtype=np.int16))
            
            # Stop capture
            file_path = recorder.stop_recording()
            self.assertFalse(recorder.recording)
            self.assertEqual(file_path, temp_wav)
            self.assertTrue(os.path.exists(temp_wav))

    def test_agent_2_and_3_llm_and_scaffolder(self):
        """Agent 2 & 3: Audit structured requirements analysis and scaffolding template writer."""
        model_data = {
            "project_name": "retail-price-scraper",
            "display_name": "Retail Price Scraper",
            "short_description": "Scrapes retail product prices and exports to CSV.",
            "project_type": "Python CLI Tool",
            "tech_stack": ["Python", "BeautifulSoup", "pandas"],
            "dependencies": ["beautifulsoup4", "pandas", "requests"],
            "specifications": ["Scrape web page", "Parse tables", "Export CSV"],
            "quality_criteria": ["Clean code", "PEP 8 compliant"],
            "files_to_create": [
                {
                    "file_path": "scraper.py",
                    "purpose": "Core scraping operations"
                },
                {
                    "file_path": "utils.py",
                    "purpose": "Parsing price helper functions"
                }
            ]
        }
        requirements = RequirementsModel(**model_data)

        # Mock generated file contents
        from speech_to_code.models.project import ProjectFileModel
        generated_files = [
            ProjectFileModel(file_path="scraper.py", content="print('Scraping retail prices...')", purpose="Core scraper"),
            ProjectFileModel(file_path="utils.py", content="def parse_price(txt):\n    return float(txt)", purpose="Price helper"),
            ProjectFileModel(file_path="README.md", content="# Retail Price Scraper\nThis is pandas retail price scraper.", purpose="Readme"),
            ProjectFileModel(file_path="CLAUDE.md", content="## CLAUDE.md guidelines", purpose="Claude guidelines")
        ]

        # Verify scaffolding creates target structure
        scaffolder = ProjectScaffolder(base_output_dir=self.test_dir)
        project_path = scaffolder.scaffold(requirements, generated_files)
        
        self.assertTrue(os.path.exists(project_path))
        self.assertTrue(os.path.exists(os.path.join(project_path, "scraper.py")))
        self.assertTrue(os.path.exists(os.path.join(project_path, "utils.py")))
        self.assertTrue(os.path.exists(os.path.join(project_path, "README.md")))
        self.assertTrue(os.path.exists(os.path.join(project_path, "CLAUDE.md")))

        # Verify Jinja2 variables were rendered correctly inside README
        with open(os.path.join(project_path, "README.md"), "r", encoding="utf-8") as f:
            readme_text = f.read()
            self.assertIn("Retail Price Scraper", readme_text)
            self.assertIn("pandas", readme_text)

    def test_agent_4_ui_overlay_threading(self):
        """Agent 4: Audit Tkinter overlay window message routing safety."""
        from speech_to_code.ui.overlay import OverlayWindow
        overlay = OverlayWindow()
        
        # Overlay message queue can accept text updates without a running tkinter mainloop
        overlay.update_status("Testing Status", "#0A84FF")
        self.assertFalse(overlay.msg_queue.empty())
        
        msg = overlay.msg_queue.get()
        self.assertEqual(msg["action"], "update")
        self.assertEqual(msg["text"], "Testing Status")
        self.assertEqual(msg["color"], "#0A84FF")

    def test_agent_5_app_orchestration(self):
        """Agent 5: Audit main application orchestrator lifecycle and pipeline routing."""
        app = SpeechToCodeApp()
        
        # Stub the core pipeline components to verify clean flow
        app.transcriber.transcribe = MagicMock(return_value="Scrape prices")
        app.analyzer.analyze = MagicMock(return_value=RequirementsModel(
            project_name="stub-app",
            display_name="Stub App",
            short_description="A stub application",
            project_type="Python CLI",
            tech_stack=[],
            dependencies=[],
            specifications=[],
            quality_criteria=[],
            files_to_create=[]
        ))
        app.validator.validate = MagicMock(side_effect=lambda t, r: r)
        from speech_to_code.models.project import ProjectFileModel
        app.generator.generate_all_files = MagicMock(return_value=[
            ProjectFileModel(file_path="app.py", content="print('hello')", purpose="Main entrypoint")
        ])
        app.scaffolder.scaffold = MagicMock(return_value=os.path.join(self.test_dir, "stub-app"))

        # Run process pipeline with dummy wav path
        dummy_wav = os.path.join(self.test_dir, "dummy.wav")
        with open(dummy_wav, "w") as f:
            f.write("mock audio data")
            
        app._process_pipeline(dummy_wav)
        
        # Verify components were invoked correctly
        app.transcriber.transcribe.assert_called_once_with(dummy_wav)
        app.analyzer.analyze.assert_called_once_with("Scrape prices")
        app.generator.generate_all_files.assert_called_once()
        app.scaffolder.scaffold.assert_called_once()
        # Verify dummy file clean up was done
        self.assertFalse(os.path.exists(dummy_wav))

    def test_local_whisper_transcription(self):
        """Audit the local offline faster-whisper transcription path and FFMPEG bypass numpy loading."""
        from speech_to_code.core.transcriber import AudioTranscriber
        transcriber = AudioTranscriber(whisper_mode="local", whisper_local_model="tiny")
        
        # Mock faster_whisper WhisperModel
        mock_model = MagicMock()
        mock_segment = MagicMock()
        mock_segment.text = "Hello from local Whisper."
        mock_model.transcribe.return_value = ([mock_segment], None)
        
        # Inject the mock model so we don't download or run it
        transcriber._local_model = mock_model
        
        # Create a dummy WAV file
        import tempfile
        import scipy.io.wavfile as wav
        import numpy as np
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_path = temp_wav.name
        
        try:
            # Write 1 second of silent 16kHz float32 audio
            rate = 16000
            data = np.zeros(rate, dtype=np.int16)
            wav.write(temp_path, rate, data)
            
            result = transcriber.transcribe(temp_path)
            self.assertEqual(result, "Hello from local Whisper.")
            
            # Verify numpy array was passed to transcribe method (since we bypass ffmpeg)
            mock_model.transcribe.assert_called_once()
            called_args, called_kwargs = mock_model.transcribe.call_args
            # The first argument should be a numpy array
            self.assertIsInstance(called_args[0], np.ndarray)
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
