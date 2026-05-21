import queue
import threading
import time
import logging
import tkinter as tk

logger = logging.getLogger(__name__)

class OverlayWindow:
    def __init__(self):
        self.msg_queue = queue.Queue()
        self.root = None
        self.label = None
        self.border_frame = None
        self.thread = None
        self.is_running = False

    def start(self):
        """Starts the Tkinter overlay in a background thread."""
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Tkinter overlay thread started.")

    def _run(self):
        """Tkinter main thread execution loop."""
        try:
            self.root = tk.Tk()
            self.root.overrideredirect(True)      # Frameless
            self.root.attributes("-topmost", True)  # Always on top
            self.root.attributes("-alpha", 0.90)    # Translucent glassmorphism
            self.root.configure(bg="#121212")

            # Center/Position Window: Top Right Corner
            screen_width = self.root.winfo_screenwidth()
            width = 320
            height = 80
            x = screen_width - width - 30
            y = 30
            self.root.geometry(f"{width}x{height}+{x}+{y}")

            # Accent Border Frame
            self.border_frame = tk.Frame(self.root, bg="#FF453A", bd=2) # Default red
            self.border_frame.pack(fill=tk.BOTH, expand=True)

            # Dark Background Inner Box
            inner_frame = tk.Frame(self.border_frame, bg="#1E1E1E")
            inner_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

            # Message Label
            self.label = tk.Label(
                inner_frame, 
                text="🎙️ Speech to Code Initialized", 
                fg="#E5E5EA", 
                bg="#1E1E1E",
                font=("Segoe UI", 11, "bold"),
                justify="center",
                wraplength=280
            )
            self.label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

            # Hide initially
            self.root.withdraw()

            # Start queue poll loop
            self._poll_queue()
            
            # Tkinter main event loop
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error in Tkinter overlay: {e}")
        finally:
            self.is_running = False

    def _poll_queue(self):
        """Polls the message queue for updates from other threads."""
        if not self.root:
            return

        try:
            while True:
                msg = self.msg_queue.get_nowait()
                action = msg.get("action")
                
                if action == "show":
                    self.root.deiconify()
                    # Force window on top again
                    self.root.attributes("-topmost", True)
                elif action == "hide":
                    self.root.withdraw()
                elif action == "update":
                    text = msg.get("text", "")
                    color = msg.get("color", "#3A3A3C") # Gray default
                    if self.label:
                        self.label.configure(text=text)
                    if self.border_frame:
                        self.border_frame.configure(bg=color)
        except queue.Empty:
            pass

        # Schedule next poll
        try:
            if self.root:
                self.root.after(50, self._poll_queue)
        except tk.TclError:
            pass

    def show(self):
        """Make the overlay visible."""
        self.msg_queue.put({"action": "show"})

    def hide(self):
        """Hide the overlay."""
        self.msg_queue.put({"action": "hide"})

    def update_status(self, text, color_hex="#3A3A3C"):
        """
        Updates the text and accent color of the overlay.
        :param text: Text to show (e.g. "🔴 Recording...").
        :param color_hex: Accent color for the frame border (e.g. Red for recording, Blue for processing).
        """
        self.msg_queue.put({
            "action": "update",
            "text": text,
            "color": color_hex
        })

    def hide_delayed(self, delay_seconds=3.0):
        """Hides the overlay after a delay."""
        def _delay():
            time.sleep(delay_seconds)
            self.hide()
        threading.Thread(target=_delay, daemon=True).start()

    def select_directory(self, callback_func):
        """
        Safely opens a directory selection dialog on the Tkinter thread.
        :param callback_func: Callback function receiving the selected directory path.
        """
        def _select():
            from tkinter import filedialog
            # Temporarily un-withdraw to ensure dialog is parented properly
            was_hidden = not self.root.winfo_viewable()
            if was_hidden:
                self.root.deiconify()
            
            folder = filedialog.askdirectory(
                parent=self.root,
                title="Select Speech to Code Output Directory"
            )
            
            if was_hidden:
                self.root.withdraw()
                
            if folder:
                callback_func(folder)

        try:
            if self.root:
                self.root.after(0, _select)
        except Exception as e:
            logger.error(f"Error launching directory selection dialog: {e}")

# Local manual test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    overlay = OverlayWindow()
    overlay.start()
    
    print("Showing overlay...")
    overlay.show()
    overlay.update_status("🎙️ Recording... (0:00)", "#FF453A")
    time.sleep(2)
    
    print("Updating to Transcribing...")
    overlay.update_status("☁️ Transcribing audio...", "#0A84FF")
    time.sleep(2)

    print("Updating to Generating...")
    overlay.update_status("🧠 Generating files...", "#5E5CE6")
    time.sleep(2)

    print("Updating to Done...")
    overlay.update_status("✅ Project Scaffolded!", "#30D158")
    overlay.hide_delayed(2)
    time.sleep(3)
    print("Finished.")
