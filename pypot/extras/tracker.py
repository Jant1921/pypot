from ..creatures.abstractcreature import actual_robot
from threading import Thread

class Tracker(object):
    def __init__(self, camera, move_vertical=True):
        if not actual_robot:
            raise AttributeError('Intitialize a robot to use the tracker')
        self._center_x = camera.resolution[0] / 2
        self._center_y = camera.resolution[1] / 2
        self.camera = camera
        self._center_x_range = self._center_x * 0.03
        self._center_y_range = self._center_y * 0.03
        self._move_vertical = move_vertical
        self._running = False
        self._thread = None

    @property
    def move_vertical(self):
        return self._move_vertical

    @move_vertical.setter
    def move_vertical(self, value):
        self._move_vertical = value

    def track_object_color(self, color):
        if not self._running:
            filter_function = getattr(self.camera, 'filter_{}_objects'.format(color))
            self._thread = Thread(target=self._track_color_loop,
                                  name='track_color',
                                  args=(filter_function,))
            self._thread.daemon = True
            self._running = True
            self._thread.start()

    def _track_color_loop(self, filter_function):
        while self._running:
            img = filter_function()
            res, values = self.camera.get_image_objects(img)
            if values:
                (con, centers, area) = values[0]
                self.center_object(centers)

    def center_object(self, (object_x, object_y)):
        x_distance = self._center_x - object_x
        y_distance = self._center_y - object_y
        abs_x_distance = abs(x_distance)
        abs_y_distance = abs(y_distance)
        if abs_x_distance > self._center_x_range:
            head_z_present_position = actual_robot.head_z.present_position
            if x_distance > 0:
                actual_robot.head_z.goto_position(head_z_present_position + abs_x_distance * 0.3, 1)
            else:
                actual_robot.head_z.goto_position(head_z_present_position - abs_x_distance * 0.3, 1)
        if (abs_y_distance > self._center_y_range) and self._move_vertical:
            head_y_present_position = actual_robot.head_y.present_position
            if y_distance > 0:
                actual_robot.head_y.goto_position(head_y_present_position - abs_y_distance * 0.3, 1)
            else:
                actual_robot.head_y.goto_position(head_y_present_position + abs_y_distance * 0.3, 1)

    def stop_tracker(self):
        self._running = False
        self._thread.join()
        self._thread = None
