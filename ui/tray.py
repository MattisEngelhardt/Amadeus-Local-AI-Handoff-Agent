import logging
import threading
import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

class SystemTrayApp:
    def __init__(self, on_toggle_recording, on_change_output, on_exit):
        """
        Initialize the System Tray App.
        :param on_toggle_recording: Callback function when toggling record.
        :param on_change_output: Callback function when changing output directory.
        :param on_exit: Callback function when exiting the application.
        """
        self.icon = None
        self.on_toggle_recording = on_toggle_recording
        self.on_change_output = on_change_output
        self.on_exit = on_exit
        self.recording_state = False
        self.tray_thread = None

    def _create_icon_image(self):
        """Generates a dynamic RGBA image for the system tray icon."""
        width, height = 64, 64
        # Red when recording, blue when idle
        accent_color = "#FF453A" if self.recording_state else "#0A84FF"
        
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Outer Ring
        dc.ellipse([6, 6, 58, 58], fill="#1C1C1E", outline=accent_color, width=4)
        # Inner microphone core
        dc.ellipse([22, 22, 42, 42], fill=accent_color)
        
        return image

    def set_recording_state(self, state: bool):
        """Updates the tray icon image and tooltip title based on recording state."""
        self.recording_state = state
        if self.icon:
            self.icon.icon = self._create_icon_image()
            self.icon.title = "Speech to Code (Recording...)" if state else "Speech to Code - Ready"
            logger.info(f"System tray icon updated. Recording state: {state}")

    def run(self):
        """Runs the pystray icon in a background daemon thread."""
        logger.info("Starting system tray icon...")
        
        menu = pystray.Menu(
            pystray.MenuItem("Toggle Recording (Ctrl+Space)", lambda icon, item: self.on_toggle_recording()),
            pystray.MenuItem("Set Output Directory...", lambda icon, item: self.on_change_output()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", lambda icon, item: self.on_exit())
        )
        
        self.icon = pystray.Icon(
            name="SpeechToCode",
            icon=self._create_icon_image(),
            title="Speech to Code - Ready",
            menu=menu
        )

        # Run in a background thread to prevent blocking Tkinter and hotkey loops
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()
        logger.info("System tray thread launched.")

    def stop(self):
        """Stops the system tray loop and cleans up."""
        if self.icon:
            logger.info("Stopping system tray icon...")
            self.icon.stop()
