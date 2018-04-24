
class Imitator(object):
    def __init__(self, real_robot=None, simulated_robot=None):
        self._simulated_robot = simulated_robot
        self._real_robot = real_robot

    @property
    def simulated_robot(self):
        return self.

    @property
    def real_robot(self):
        return self._real_robot

    def _run_command(self, robot_name, command, get_value=True):
        formatted_command = '{}.{}'.format(robot_name, command)
        if get_value:
            return eval(formatted_command)
        else:
            exec formatted_command
            return None

    def imitate(self, command, get_value=True):
        real_result = None
        simulated_result = None
        if self.real_robot:
            real_result = self._run_command('self.real_robot', command, get_value)
        if self.simulated_robot:
            simulated_result = self._run_command('self.simulated_robot', command, get_value)
        return real_result, simulated_result
