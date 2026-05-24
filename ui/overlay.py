import logging
import queue
import threading
import time
import tkinter as tk

logger = logging.getLogger(__name__)


class OverlayWindow:
    def __init__(self) -> None:
        self.msg_queue: queue.Queue[dict[str, str]] = queue.Queue()
        self.root: tk.Tk | None = None
        self.label: tk.Label | None = None
        self.border_frame: tk.Frame | None = None
        self.thread: threading.Thread | None = None
        self.is_running = False

    def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Tkinter overlay thread started.")

    def _run(self) -> None:
        try:
            self.root = tk.Tk()
            self.root.overrideredirect(True)
            self.root.attributes("-topmost", True)
            self.root.attributes("-alpha", 0.90)
            self.root.configure(bg="#121212")

            screen_width = self.root.winfo_screenwidth()
            width = 320
            height = 80
            x = screen_width - width - 30
            y = 30
            self.root.geometry(f"{width}x{height}+{x}+{y}")

            self.border_frame = tk.Frame(self.root, bg="#FF453A", bd=2)
            self.border_frame.pack(fill=tk.BOTH, expand=True)

            inner_frame = tk.Frame(self.border_frame, bg="#1E1E1E")
            inner_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

            self.label = tk.Label(
                inner_frame,
                text="Amadeus initialized",
                fg="#E5E5EA",
                bg="#1E1E1E",
                font=("Segoe UI", 11, "bold"),
                justify="center",
                wraplength=280,
            )
            self.label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

            self.root.withdraw()
            self._poll_queue()
            self.root.mainloop()
        except Exception as exc:
            logger.error("Error in Tkinter overlay: %s", exc)
        finally:
            self.is_running = False

    def _poll_queue(self) -> None:
        if not self.root:
            return

        try:
            while True:
                msg = self.msg_queue.get_nowait()
                action = msg.get("action")
                if action == "show":
                    self.root.deiconify()
                    self.root.attributes("-topmost", True)
                elif action == "hide":
                    self.root.withdraw()
                elif action == "update":
                    text = msg.get("text", "")
                    color = msg.get("color", "#3A3A3C")
                    if self.label:
                        self.label.configure(text=text)
                    if self.border_frame:
                        self.border_frame.configure(bg=color)
        except queue.Empty:
            pass

        try:
            if self.root:
                self.root.after(50, self._poll_queue)
        except tk.TclError:
            pass

    def show(self) -> None:
        self.msg_queue.put({"action": "show"})

    def hide(self) -> None:
        self.msg_queue.put({"action": "hide"})

    def update_status(self, text: str, color_hex: str = "#3A3A3C") -> None:
        self.msg_queue.put({"action": "update", "text": text, "color": color_hex})

    def hide_delayed(self, delay_seconds: float = 3.0) -> None:
        def _delay() -> None:
            time.sleep(delay_seconds)
            self.hide()

        threading.Thread(target=_delay, daemon=True).start()

    def select_directory(self, callback_func) -> None:
        def _select() -> None:
            from tkinter import filedialog

            if not self.root:
                return

            was_hidden = not self.root.winfo_viewable()
            if was_hidden:
                self.root.deiconify()

            folder = filedialog.askdirectory(
                parent=self.root,
                title="Select Amadeus Output Directory",
            )
            if was_hidden:
                self.root.withdraw()
            if folder:
                callback_func(folder)

        try:
            if self.root:
                self.root.after(0, _select)
        except Exception as exc:
            logger.error("Error launching directory selection dialog: %s", exc)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    overlay = OverlayWindow()
    overlay.start()
    overlay.show()
    overlay.update_status("Recording... (0:00)", "#FF453A")
    time.sleep(2)
    overlay.update_status("Transcribing audio...", "#0A84FF")
    time.sleep(2)
    overlay.update_status("Workspace scaffolded", "#30D158")
    overlay.hide_delayed(2)
    time.sleep(3)
