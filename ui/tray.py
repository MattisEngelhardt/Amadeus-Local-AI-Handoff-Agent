import logging
import threading

import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


class SystemTrayApp:
    def __init__(self, on_toggle_recording, on_change_output, on_exit) -> None:
        self.icon: pystray.Icon | None = None
        self.on_toggle_recording = on_toggle_recording
        self.on_change_output = on_change_output
        self.on_exit = on_exit
        self.recording_state = False
        self.tray_thread: threading.Thread | None = None

    def _create_icon_image(self) -> Image.Image:
        width, height = 64, 64
        accent_color = "#FF453A" if self.recording_state else "#0A84FF"

        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        dc.ellipse([6, 6, 58, 58], fill="#1C1C1E", outline=accent_color, width=4)
        dc.ellipse([22, 22, 42, 42], fill=accent_color)
        return image

    def set_recording_state(self, state: bool) -> None:
        self.recording_state = state
        if self.icon:
            self.icon.icon = self._create_icon_image()
            self.icon.title = "Amadeus (Recording...)" if state else "Amadeus - Ready"
            logger.info("System tray recording state: %s", state)

    def run(self) -> None:
        logger.info("Starting Amadeus system tray icon.")
        menu = pystray.Menu(
            pystray.MenuItem(
                "Toggle Recording (Ctrl+Space)",
                lambda _icon, _item: self.on_toggle_recording(),
            ),
            pystray.MenuItem(
                "Set Output Directory...",
                lambda _icon, _item: self.on_change_output(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", lambda _icon, _item: self.on_exit()),
        )

        self.icon = pystray.Icon(
            name="Amadeus",
            icon=self._create_icon_image(),
            title="Amadeus - Ready",
            menu=menu,
        )
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()
        logger.info("System tray thread launched.")

    def stop(self) -> None:
        if self.icon:
            logger.info("Stopping system tray icon.")
            self.icon.stop()
