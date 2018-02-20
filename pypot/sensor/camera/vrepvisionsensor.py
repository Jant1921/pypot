from .abstractcam import AbstractCamera
import numpy as np


class VrepVisionSensor(AbstractCamera):
    registers = AbstractCamera.registers
    simulator_only = True

    def __init__(self, name, vrep_io):
        try:
            vision_sensor_handler = vrep_io.get_object_handle(name)
        except:
            raise Exception('Can not load ' + name + ' from V-REP')
        resolution, image = vrep_io.get_vision_sensor_image(vision_sensor_handler, streaming=True)

        def get_vision_sensor_image():
            return vrep_io.get_vision_sensor_image(vision_sensor_handler, buffer=True)
        self._grab = get_vision_sensor_image
        AbstractCamera.__init__(self, name, resolution, 30)

    def grab(self):
        resolution, image = self._grab()
        image = np.array(image, dtype=np.uint8)
        image.resize([resolution[0], resolution[1], 3])
        image = np.rot90(image, 2)
        image = np.fliplr(image)
        return image

    def close(self):
        AbstractCamera.close()
