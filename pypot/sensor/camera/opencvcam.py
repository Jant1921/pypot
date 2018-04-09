import cv2

from .abstractcam import AbstractCamera
from threading import Thread
from time import time

class OpenCVCamera(AbstractCamera):
    registers = AbstractCamera.registers + ['index']

    def __init__(self, name, index, fps, resolution=None):
        self._index = index
        self.capture = cv2.VideoCapture(self.index)
        self.capture.set(cv2.CAP_PROP_FPS, fps)
        if resolution is not None:
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        if not self.capture.isOpened():
            raise ValueError('Can not open camera device {}. You should start your robot with argument camera=\'dummy\'. E.g. p = PoppyErgoJr(camera=\'dummy\')'.format(index))
        self.running = True
        """
        self._processing = Thread(target=self._process_loop)
        self._processing.daemon = True
        self._processing.start()
        """
        AbstractCamera.__init__(self, name, resolution, fps)

    @property
    def frame(self):
        return self.grab()
        # return self._last_frame

    @property
    def index(self):
        return self._index

    def grab(self):
        """OpenCV image grab
        :returns formatted image as array of BGR values
        """
        rval, frame = self.capture.read()
        if not rval:
            raise EnvironmentError('Can not grab image from the camera!')
        return frame

    """
    def _process_loop(self):
        period = 1.0 / self.fps
        last_frame_time = time()
        while self.running:
            if time() - last_frame_time > period:
                self._last_frame = self._grab_and_process()
                last_frame_time = time()
    """

    def close(self):
        # self._processing.join()
        AbstractCamera.close(self)
        self.capture.release()
