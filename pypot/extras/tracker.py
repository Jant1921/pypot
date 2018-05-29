from ..creatures.abstractcreature import actual_robot


class Tracker(object):
    def __init__(self, camera):
        if not actual_robot:
            raise AttributeError('Intitialize a robot to use the tracker')
        self._center_x = camera.resolution[0] / 2
        self._center_y = camera.resolution[1] / 2
        self._center_x_range = self._center_x * 0.03
        self._center_y_range = self._center_y * 0.03

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
        if abs_y_distance > self._center_y_range:
            head_y_present_position = actual_robot.head_y.present_position
            if y_distance > 0:
                actual_robot.head_y.goto_position(head_y_present_position - abs_y_distance * 0.3, 1)
            else:
                actual_robot.head_y.goto_position(head_y_present_position + abs_y_distance * 0.3, 1)
