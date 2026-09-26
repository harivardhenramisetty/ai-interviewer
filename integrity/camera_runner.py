import sys
import threading
import time
from pathlib import Path


INTEGRITY_DIR = Path(__file__).resolve().parent

if str(INTEGRITY_DIR) not in sys.path:
    sys.path.insert(0, str(INTEGRITY_DIR))

from camera_monitor import CameraMonitor


class CameraRunner:
    """
    Runs CameraMonitor continuously in a background thread.

    The camera feed is never displayed to the candidate.
    """

    def __init__(self):
        self.monitor = CameraMonitor()
        self.thread = None
        self.running = False

    def start(self):
        """Start camera monitoring in the background."""

        if self.running:
            return

        self.monitor.start_monitoring()

        self.running = True

        self.thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
        )

        self.thread.start()

    def _monitor_loop(self):
        """Continuously capture and process camera frames."""

        while self.running:
            try:
                frame = self.monitor.read_frame()

                if frame is None:
                    break

                self.monitor.process_frame(frame)

                time.sleep(0.01)

            except Exception as exc:
                print(f"Camera monitoring error: {exc}")
                break

    def stop(self):
        """Stop background monitoring and release the camera."""

        if not self.running:
            return

        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=2)
            self.thread = None

        self.monitor.stop_monitoring()

    def get_events(self):
        """Return integrity events for the current interview."""

        return self.monitor.get_events()