from threading import Thread
from .tracker import Tracker
from .image_display import ImageDisplay
from time import time
try:
    from .recognition import FaceRecognition
except ImportError:
    raise ImportError("FaceRecognition can't be imported. Missing Dependencies.")

from ..creatures.abstractcreature import actual_robot

if not actual_robot:
    raise AttributeError('Intitialize a robot to use the tracker')

def close_thread(thread):
    if thread is not None:
        thread.join()
        thread = None


class BehaviorController(object):
    def __init__(self, camera, get_capacitive_function=None):
        self._display = None
        self._face_recognition = FaceRecognition(camera)
        self._tracker = Tracker(camera)
        self._is_capacitive_enabled = get_capacitive_function
        self._recognizer_frequency = 0.5
        self._face_recognized = False
        self._running = False
        self._greet = False
        # behavior threads
        self._recognizer_thread = None
        self._tracker_thread = None
        self._greeting_thread = None

    @property
    def display(self):
        return self._display

    @property
    def face_recognition(self):
        return self._face_recognition

    @property
    def tracker(self):
        return self._tracker

    def _start_thread(self, thread, target_function, thread_name, force=False):
        if not self._running or force:
            thread = Thread(target=target_function, name=thread_name)
            thread.daemon = True
            self._running = True
            thread.start()

    def start_display(self, animations, default_animation):
        self._display = ImageDisplay(animations, default_animation)

    def stop_display(self):
        if self._display is not None:
            self._display.close()

    def start_tracker(self):
        pass

    def stop_tracker(self):
        self._running = False
        close_thread(self._tracker_thread)

    def change_face_animation(self, animation_name):
        if self._display is not None:
            self._display.change_animation(animation_name)

    def start_recognition(self, frequency=0.5):
        self._recognizer_frequency = frequency
        self._start_thread(self._recognizer_thread,
                           self._recognizer_loop,
                           'recognition')

    def stop_recognition(self):
        self._face_recognized = False
        self._running = False
        close_thread(self._recognizer_thread)

    def _recognizer_loop(self):
        # process_this_frame = True
        last_frame_time = 0
        while self._running:
            if time() - last_frame_time > self._recognizer_frequency:#process_this_frame:
                self._face_recognized, face_names = self._face_recognition.recognize_faces()
                if self._face_recognized:
                    self.change_face_animation('face_detected')
                else:
                    self.change_face_animation('idle')
                last_frame_time = time()
            # process_this_frame = not process_this_frame

    def start_greeting(self):
        from ..creatures.abstractcreature import actual_robot
        if not actual_robot:
            raise AttributeError('Intitialize a robot to use greeting behavior')
        self._greet = True
        self._start_thread(self._greeting_thread,
                           self._greeting_loop,
                           'greeting',
                           force=True)

    def stop_greeting(self):
        self._greet = False
        close_thread(self._greeting_thread)

    def _face_found(self):
        lado = actual_robot.head_z.present_position
        print 'moviendo r_arm_z to ' + str(lado)
        actual_robot.r_arm_z.goto_position(lado, 1.0, wait=True)
        actual_robot.r_shoulder_y.goto_position(0, 1.0, wait=True)
        extended_since = time()
        while time() - extended_since > 2:
            print 'waiting'
            if self._is_capacitive_enabled is not None:
                while self._is_capacitive_enabled():
                    print 'cap activated'
                    pass
        print 'fuera'
        actual_robot.r_arm_z.goto_position(0, 1.0, wait=True)
        actual_robot.r_shoulder_y.goto_position(0, 1.0, wait=True)

    def _greeting_loop(self):
        min_angle = -70
        max_angle = 70
        go_min = True
        go_max = False
        pos = 0
        amp = 2
        while self._greet:
            if go_min and pos > min_angle:
                actual_robot.head_z.goto_position(pos, 0.5, wait=True)
                pos -= amp
            elif go_max and pos < max_angle:
                actual_robot.head_z.goto_position(pos, 0.5, wait=True)
                pos += amp
            else:
                go_min = not go_min
                go_max = not go_max
            if self._face_recognized:
                self._face_found()

    def stop(self):
        self.stop_recognition()
        self.stop_display()
        self.stop_tracker()
        self.stop_greeting()
