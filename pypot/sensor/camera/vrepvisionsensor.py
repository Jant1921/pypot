from .abstractcam import AbstractCamera
import numpy as np
import cv2


class VrepVisionSensor(AbstractCamera):
    registers = AbstractCamera.registers
    simulator_only = True

    def __init__(self, name, fps, vrep_io):
        try:
            vision_sensor_handler = vrep_io.get_object_handle(name)
        except:
            raise Exception('Can not load ' + name + ' from V-REP')
        self._res, image = vrep_io.get_vision_sensor_image(vision_sensor_handler, streaming=True)

        def get_vision_sensor_image():
            return vrep_io.get_vision_sensor_image(vision_sensor_handler, buffer=True)

        self._grab = get_vision_sensor_image
        AbstractCamera.__init__(self, name, self._res, fps)

    def grab(self):
        """v-rep image grab
        :returns formatted image as array of BGR values
        """
        self._res, image = self._grab()
        if image is None:
            return None
        image = np.array(image, dtype=np.uint8)
        image.resize([self._res[0], self._res[1], 3])
        image = np.rot90(image, 2)
        image = np.fliplr(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return image
