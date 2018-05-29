from threading import Thread
from .tracker import Tracker
from .image_display import ImageDisplay
try:
    from .recognition import FaceRecognition
except ImportError:
    raise ImportError("FaceRecognition can't be imported. Missing Dependencies.")


def close_thread(thread):
    if thread is not None:
        thread.join()
        thread = None


class BehaviourController(object):
    def __init__(self, camera, get_capacitive_function=None):
        self._display = None
        self._face_recognition = FaceRecognition(camera)
        self._tracker = Tracker(camera)
        self._is_capacitive_enabled = get_capacitive_function
        self._running = False
        self._recognizer_thread = None
        self._tracker_thread = None

    @property
    def display(self):
        return self._display

    @property
    def face_recognition(self):
        return self._face_recognition

    @property
    def tracker(self):
        return self._tracker

    def start_display(self, animations, default_animation):
        self._display = ImageDisplay(animations, default_animation)

    def stop_display(self):
        if self._display is not None:
            self._display.close()

    def _start_thread(self, thread, target_function):
        if not self._running:
            thread = Thread(target=target_function)
            thread.daemon = True
            self._running = True
            thread.start()

    def change_face_animation(self, animation_name):
        if self._display is not None:
            self._display.change_animation(animation_name)

    def recognize(self):
        self._start_thread(self._recognizer_thread, self._recognizer_loop)

    def _recognizer_loop(self):
        process_this_frame = True
        while self._running:
            if process_this_frame:
                face_recognized, face_names = self._face_recognition.recognize_faces()
                if face_recognized:
                    self.change_face_animation('face_detected')
                else:
                    self.change_face_animation('idle')
            process_this_frame = not process_this_frame

    def close(self):
        self._running = False
        close_thread(self._recognizer_thread)
        close_thread(self._tracker_thread)