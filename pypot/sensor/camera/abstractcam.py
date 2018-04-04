import time
import numpy as np
import cv2

from threading import Thread

from ...robot.sensor import Sensor

hsv_color_ranges = {
    "green": ([34, 50, 50], [80, 220, 200]),
    "red":  ([0, 50, 50], [20, 255, 255]),
    "yellow": ([20, 50, 50], [60, 255, 255])
}


class AbstractCamera(Sensor):
    registers = Sensor.registers + ['frame', 'resolution', 'fps']

    def __init__(self, name, resolution, fps):
        Sensor.__init__(self, name)

        self._res, self._fps = resolution, fps
        self._last_frame = self._grab_and_process()
        self._custom_filters = {}
        self.running = True
        # self._processing = Thread(target=self._process_loop)
        # self._processing.daemon = True
        # self._processing.start()
        self._contours_array_index = 1 if cv2.__version__.startswith("3.") else 0

    @property
    def frame(self):
        self._last_frame = self._grab_and_process()
        return self._last_frame

    def post_processing(self, image):
        return image

    def grab(self):
        raise NotImplementedError

    def _grab_and_process(self):
        return self.post_processing(self.grab())

    """
    def _process_loop(self):
        period = 1.0 / self.fps

        while self.running:
            self._last_frame = self._grab_and_process()
            time.sleep(period)
    """

    @property
    def resolution(self):
        return list(reversed(self.frame.shape[:2]))

    @property
    def fps(self):
        return self._fps

    def filter_objects_by_color_range(self, lower_hsv_range, upper_hsv_range):
        """Filter image objects between a given color range
        :param lower_hsv_range: lower color range in hsv format
        :param upper_hsv_range: upper color range in hsv format
        :return: filtered image array
        """
        image = self.grab()
        lower = np.array(lower_hsv_range, dtype=np.uint8)
        upper = np.array(upper_hsv_range, dtype=np.uint8)
        mask = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(mask, lower, upper)
        output = cv2.bitwise_and(image, image, mask=mask)
        return output

    def _filter_by_predefined_color(self, color_tuple):
        lower, upper = color_tuple
        return self.filter_objects_by_color_range(lower, upper)

    def filter_red_objects(self):
        return self._filter_by_predefined_color(hsv_color_ranges["red"])

    def filter_green_objects(self):
        return self._filter_by_predefined_color(hsv_color_ranges["green"])

    def filter_yellow_objects(self):
        return self._filter_by_predefined_color(hsv_color_ranges["yellow"])

    def add_custom_filter(self, filter_name, custom_filter_function):
        """Add custom image filters to the camera class
        :param filter_name: The filter name
        :param custom_filter_function: filter function
        """
        self._custom_filters[filter_name] = custom_filter_function

    def run_custom_filter(self, name):
        """Executes previously added custom filters
        :param name: name of the added filter
        :return: Custom filter result. None if the filter name is not found
        """
        try:
            return self._custom_filters[name](self.grab())
        except KeyError:
            return None

    def get_objects_center(self, image, draw_contours=False):
        """ Gets contours and center of objects found in an image
        :param image: BGR image array
        :param draw_contours: to draw the contours and centers in the original image
        :return: BGR image array, array of (x,y) center elements, contours array
        """
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)
        thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)[1]
        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[self._contours_array_index]
        centers = []
        for contour in contours:
            # compute the center of the contour
            M = cv2.moments(contour)
            try:
                center_x = int(M["m10"] / M["m00"])
                center_y = int(M["m01"] / M["m00"])
                centers.append((center_x, center_y))
                if draw_contours:
                    cv2.drawContours(image, [contour], -1, (0, 255, 0), 2)
                    cv2.circle(image, (center_x, center_y), 4, (255, 255, 255), -1)
            except:
                pass
        return image, centers, contours

    def close(self):
        self.running = False
        # self._processing.join()
