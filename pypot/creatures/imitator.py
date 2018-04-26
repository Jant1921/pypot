import requests
import json

class Imitator(object):
    def __init__(self, remote_robots=[], simulated_robot=None):
        self._simulated_robot = simulated_robot
        self._remote_robots = remote_robots

    @property
    def simulated_robot(self):
        return self._simulated_robot

    @property
    def remote_robots(self):
        return self._remote_robots

    def _run_command_on_simulation(self, command, get_value=True):
        formatted_command = 'self.simulated_robot.{}'.format(command)
        if get_value:
            return eval(formatted_command)
        else:
            exec formatted_command
            return None

    def imitate(self, command, get_value=True):
        results = []
        if self.simulated_robot:
            simulated_result = self._run_command_on_simulation(command, get_value)
            results.append({'result': simulated_result})
        for robot_ip_and_port in self._remote_robots:
            request_body = {'instruction': command, 'get': get_value}
            request = requests.post('http://{}/run_instruction'.format(robot_ip_and_port),
                                    data=json.dumps(request_body),
                                    headers={'content-type': 'application/json'})
            response = request.json()
            results.append(response)

        return results
