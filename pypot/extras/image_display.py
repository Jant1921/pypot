import cv2
from threading import Thread

WINDOW_NAME = 'faceDisplay'


class ImageDisplay(object):
    def __init__(self, animations, default_animation):
        if not animations:
            raise AttributeError('No animations specified')
        if default_animation not in animations:
            raise AttributeError("Default animation '{}' doesn't exists in animations".format(default_animation))
        self.animations = animations
        self._actual_animation = None
        self.change_animation(default_animation)
        self._running = False
        self._display_thread = None
        self.start()

    def start(self):
        self._display_thread = Thread(target=self._display_loop)
        self._display_thread.daemon = True
        self._running = True
        self._display_thread.start()

    def _load_video(self, animation_name):
        video = cv2.VideoCapture(self.animations[animation_name])
        if video.isOpened():
            return video
        else:
            raise ImportError("Can't open {} video".format(self.animations[animation_name]))

    def change_animation(self, animation_name):
        if animation_name in self.animations:
            self._actual_animation = self._load_video(animation_name)

    def _display_loop(self):
        while self._running:
            if self._actual_animation.isOpened():
                ret, frame = self._actual_animation.read()
                cv2.namedWindow(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                if ret:
                    cv2.imshow(WINDOW_NAME, frame)
                else:
                    self._actual_animation.set(cv2.CAP_PROP_POS_FRAMES, 1)
                cv2.waitKey(1)

    def close(self):
        self._running = False
        self._display_thread.join()
        cv2.destroyWindow(WINDOW_NAME)
