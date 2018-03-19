import cv2

from .abstractcam import AbstractCamera


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

        AbstractCamera.__init__(self, name, resolution, fps)

    @property
    def index(self):
        return self._index

    def grab(self):
        rval, frame = self.capture.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if not rval:
            raise EnvironmentError('Can not grab image from the camera!')
        return frame

    def close(self):
        AbstractCamera.close(self)
        self.capture.release()
