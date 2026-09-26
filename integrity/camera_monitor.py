from detection_logger import (
    create_event,
    save_event,
    start_new_interview,
)

import cv2
import numpy as np

from pathlib import Path
from datetime import datetime
import time


class CameraMonitor:
    def __init__(
        self,
        camera_index=0,
        missing_face_timeout=3,
        multiple_face_timeout=1,
        gaze_away_timeout=2,
        downward_leeway=1,
        horizontal_threshold=18,
    ):
        self.camera_index = camera_index

        # -----------------------------------------------------
        # Timing thresholds
        # -----------------------------------------------------

        self.missing_face_timeout = missing_face_timeout
        self.multiple_face_timeout = multiple_face_timeout
        self.gaze_away_timeout = gaze_away_timeout

        # -----------------------------------------------------
        # Gaze thresholds
        # -----------------------------------------------------

        self.downward_leeway = downward_leeway
        self.horizontal_threshold = horizontal_threshold

        # -----------------------------------------------------
        # Camera
        # -----------------------------------------------------

        self.camera = None

        # -----------------------------------------------------
        # Recording
        # -----------------------------------------------------

        self.recording_path = (
            Path(__file__).resolve().parent
            / "latest_interview.mp4"
        )

        self.video_writer = None

        # -----------------------------------------------------
        # YuNet face detector
        # -----------------------------------------------------

        model_path = (
            Path(__file__).resolve().parent
            / "face_detection_yunet_2023mar.onnx"
        )

        if not model_path.exists():
            raise FileNotFoundError(
                f"YuNet model not found: {model_path}"
            )

        self.face_detector = cv2.FaceDetectorYN.create(
            str(model_path),
            "",
            (320, 320),
            0.9,
            0.3,
            5000,
        )

        # -----------------------------------------------------
        # State tracking
        # -----------------------------------------------------

        self.missing_face_since = None
        self.multiple_face_since = None

        self.gaze_away_since = None
        self.gaze_direction = None

        # -----------------------------------------------------
        # Event storage
        # -----------------------------------------------------

        self.events = []
        self.last_event = None

    # =========================================================
    # CAMERA CONTROL
    # =========================================================

    def start_monitoring(self):
        """
        Start the camera, reset the integrity log,
        and start recording the latest interview.
        """

        # -----------------------------------------------------
        # Start a fresh integrity log
        # -----------------------------------------------------

        start_new_interview()

        # Reset session state
        self.events = []
        self.last_event = None

        self.missing_face_since = None
        self.multiple_face_since = None
        self.gaze_away_since = None
        self.gaze_direction = None

        # -----------------------------------------------------
        # Delete previous interview recording
        # -----------------------------------------------------

        if self.recording_path.exists():
            self.recording_path.unlink()

        # -----------------------------------------------------
        # Open camera
        # -----------------------------------------------------

        self.camera = cv2.VideoCapture(
            self.camera_index
        )

        if not self.camera.isOpened():
            self.camera = None

            raise RuntimeError(
                "Could not open camera."
            )

        # -----------------------------------------------------
        # Get camera properties
        # -----------------------------------------------------

        width = int(
            self.camera.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            self.camera.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        fps = self.camera.get(
            cv2.CAP_PROP_FPS
        )

        # Some cameras return 0 or an invalid FPS.
        if fps <= 0:
            fps = 30.0

        # -----------------------------------------------------
        # Create video writer
        # -----------------------------------------------------

        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )

        self.video_writer = cv2.VideoWriter(
            str(self.recording_path),
            fourcc,
            fps,
            (width, height),
        )

        if not self.video_writer.isOpened():

            self.video_writer = None

            self.camera.release()
            self.camera = None

            raise RuntimeError(
                "Could not start video recording."
            )

        print(
            "Camera monitoring started."
        )

        print(
            "Monitoring is active."
        )

        print(
            f"Recording latest interview to: "
            f"{self.recording_path}"
        )

    def stop_monitoring(self):
        """
        Stop the camera and save the latest
        interview recording.
        """

        # -----------------------------------------------------
        # Stop recording first
        # -----------------------------------------------------

        if self.video_writer is not None:

            self.video_writer.release()

            self.video_writer = None

        # -----------------------------------------------------
        # Stop camera
        # -----------------------------------------------------

        if self.camera is not None:

            self.camera.release()

            self.camera = None

        # No OpenCV window is used, but this is safe.
        cv2.destroyAllWindows()

        print(
            "Camera monitoring stopped."
        )

        if self.recording_path.exists():

            print(
                "Latest interview recording saved to:"
            )

            print(
                self.recording_path
            )

    # =========================================================
    # FRAME READING
    # =========================================================

    def read_frame(self):
        """
        Read one camera frame and record it.

        The frame is returned for processing but
        is never displayed.
        """

        if self.camera is None:
            raise RuntimeError(
                "Camera monitoring has not been started."
            )

        success, frame = self.camera.read()

        if not success:
            return None

        # -----------------------------------------------------
        # Record frame silently
        # -----------------------------------------------------

        if self.video_writer is not None:

            self.video_writer.write(frame)

        return frame

    # =========================================================
    # FACE DETECTION
    # =========================================================

    def detect_faces(self, frame):
        """
        Detect faces using YuNet.
        """

        height, width = frame.shape[:2]

        self.face_detector.setInputSize(
            (width, height)
        )

        _, faces = self.face_detector.detect(
            frame
        )

        if faces is None:
            return []

        return faces

    # =========================================================
    # EVENT LOGGING
    # =========================================================

    def log_event(
        self,
        event,
        face_count=None,
        duration=None,
        direction=None,
    ):
        """
        Store an integrity event in memory
        and in detection_log.json.
        """

        # -----------------------------------------------------
        # Avoid logging the same event repeatedly
        # -----------------------------------------------------

        if event == self.last_event:
            return

        event_record = create_event(
            event=event,
            face_count=face_count,
            duration=duration,
            direction=direction,
        )

        # Store in current session
        self.events.append(
            event_record
        )

        # Store in current interview log
        save_event(
            event_record
        )

        self.last_event = event

        # -----------------------------------------------------
        # Terminal output
        # -----------------------------------------------------

        print(
            f"[{event_record['timestamp']}] "
            f"{event}"
        )

        if face_count is not None:

            print(
                f"    Face count: "
                f"{face_count}"
            )

        if duration is not None:

            print(
                f"    Duration: "
                f"{round(duration, 2)}s"
            )

        if direction is not None:

            print(
                f"    Direction: "
                f"{direction}"
            )

    # =========================================================
    # GAZE DIRECTION ESTIMATION
    # =========================================================

    def estimate_gaze_direction(self, face):
        """
        Estimate rough gaze/head direction using
        YuNet facial landmarks.

        Returns:
            "left"
            "right"
            "down"
            None
        """

        # YuNet face format:
        #
        # [x, y, width, height,
        #  right_eye_x, right_eye_y,
        #  left_eye_x, left_eye_y,
        #  nose_x, nose_y,
        #  right_mouth_x, right_mouth_y,
        #  left_mouth_x, left_mouth_y,
        #  confidence]

        x = face[0]
        y = face[1]
        width = face[2]
        height = face[3]

        right_eye_x = face[4]
        right_eye_y = face[5]

        left_eye_x = face[6]
        left_eye_y = face[7]

        nose_x = face[8]
        nose_y = face[9]

        # -----------------------------------------------------
        # Face center
        # -----------------------------------------------------

        face_center_x = (
            x + width / 2
        )

        # -----------------------------------------------------
        # Horizontal direction
        # -----------------------------------------------------

        horizontal_offset = (
            nose_x - face_center_x
        )

        if (
            horizontal_offset
            < -self.horizontal_threshold
        ):
            return "left"

        if (
            horizontal_offset
            > self.horizontal_threshold
        ):
            return "right"

        # -----------------------------------------------------
        # Downward direction
        # -----------------------------------------------------

        eye_center_y = (
            right_eye_y
            + left_eye_y
        ) / 2

        vertical_ratio = (
            nose_y - eye_center_y
        ) / max(height, 1)

        # Downward gaze threshold.
        #
        # downward_leeway = 1 is the value
        # currently tuned for your setup.

        if vertical_ratio > (
            0.20
            + self.downward_leeway / 100
        ):
            return "down"

        return None

    # =========================================================
    # GAZE PROCESSING
    # =========================================================

    def process_gaze(self, faces):
        """
        Process gaze direction when exactly
        one face is visible.
        """

        # -----------------------------------------------------
        # No single face
        # -----------------------------------------------------

        if len(faces) != 1:

            self.gaze_away_since = None
            self.gaze_direction = None

            return

        face = faces[0]

        direction = (
            self.estimate_gaze_direction(
                face
            )
        )

        # -----------------------------------------------------
        # Normal gaze
        # -----------------------------------------------------

        if direction is None:

            self.gaze_away_since = None
            self.gaze_direction = None

            return

        # -----------------------------------------------------
        # New gaze direction
        # -----------------------------------------------------

        if direction != self.gaze_direction:

            self.gaze_direction = direction

            self.gaze_away_since = (
                time.time()
            )

            return

        # -----------------------------------------------------
        # Continue existing gaze direction
        # -----------------------------------------------------

        if self.gaze_away_since is None:

            self.gaze_away_since = (
                time.time()
            )

            return

        elapsed = (
            time.time()
            - self.gaze_away_since
        )

        # -----------------------------------------------------
        # Sustained gaze
        # -----------------------------------------------------

        if elapsed >= self.gaze_away_timeout:

            if direction == "down":

                warning = (
                    "Warning: sustained "
                    "downward gaze detected."
                )

            elif direction == "left":

                warning = (
                    "Warning: sustained "
                    "leftward gaze detected."
                )

            elif direction == "right":

                warning = (
                    "Warning: sustained "
                    "rightward gaze detected."
                )

            else:

                warning = (
                    "Warning: sustained "
                    "off-screen gaze detected."
                )

            print(warning)

            self.log_event(
                f"gaze_away_{direction}",
                duration=elapsed,
                direction=direction,
            )

            # Reset timer so the same continuous
            # gaze doesn't generate an event
            # on every frame.

            self.gaze_away_since = (
                time.time()
            )

    # =========================================================
    # FRAME PROCESSING
    # =========================================================

    def process_frame(self, frame):
        """
        Process one camera frame.

        Detects:

        - no face
        - multiple faces
        - single face
        - sustained left gaze
        - sustained right gaze
        - sustained downward gaze
        """

        faces = self.detect_faces(
            frame
        )

        face_count = len(faces)

        # -----------------------------------------------------
        # NO FACE
        # -----------------------------------------------------

        if face_count == 0:

            self.multiple_face_since = None

            if (
                self.missing_face_since
                is None
            ):

                self.missing_face_since = (
                    time.time()
                )

            elapsed = (
                time.time()
                - self.missing_face_since
            )

            if (
                elapsed
                >= self.missing_face_timeout
            ):

                self.log_event(
                    "face_missing",
                    duration=elapsed,
                )

                # Reset timer
                self.missing_face_since = (
                    time.time()
                )

            return faces

        # -----------------------------------------------------
        # Face exists
        # -----------------------------------------------------

        self.missing_face_since = None

        # -----------------------------------------------------
        # MULTIPLE FACES
        # -----------------------------------------------------

        if face_count > 1:

            if (
                self.multiple_face_since
                is None
            ):

                self.multiple_face_since = (
                    time.time()
                )

            elapsed = (
                time.time()
                - self.multiple_face_since
            )

            if (
                elapsed
                >= self.multiple_face_timeout
            ):

                self.log_event(
                    "multiple_faces",
                    face_count=face_count,
                    duration=elapsed,
                )

                # Reset timer
                self.multiple_face_since = (
                    time.time()
                )

            return faces

        # -----------------------------------------------------
        # Exactly one face
        # -----------------------------------------------------

        self.multiple_face_since = None

        self.log_event(
            "face_detected",
            face_count=1,
        )

        # -----------------------------------------------------
        # Gaze check
        # -----------------------------------------------------

        self.process_gaze(
            faces
        )

        return faces

    # =========================================================
    # GET EVENTS
    # =========================================================

    def get_events(self):
        """
        Return all integrity events from
        the current interview session.
        """

        return self.events.copy()


# =============================================================
# STANDALONE TEST
# =============================================================

if __name__ == "__main__":

    monitor = CameraMonitor()

    try:

        monitor.start_monitoring()

        print(
            "Press 'Ctrl+C' to stop monitoring."
        )

        while True:

            frame = monitor.read_frame()

            if frame is None:

                print(
                    "Could not read camera frame."
                )

                break

            monitor.process_frame(
                frame
            )

            # Small delay to avoid
            # unnecessarily high CPU usage.

            time.sleep(0.01)

    except KeyboardInterrupt:

        print(
            "\nMonitoring stopped by user."
        )

    finally:

        monitor.stop_monitoring()

        print(
            "\nSession events:"
        )

        for event in monitor.get_events():

            print(event)