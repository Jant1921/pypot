import requests
import json
from threading import Thread


class Imitator(object):
    def __init__(self, remote_robots=[], simulated_robot=None):
        self._simulated_robot = simulated_robot
        self._remote_robots = remote_robots
        self._responses = []

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

    def _get_response(self, ip_and_port, payload):
        try:
            request = requests.post('http://{}/run_instruction'.format(ip_and_port),
                                    data=json.dumps(payload),
                                    headers={'content-type': 'application/json'},
                                    timeout=5)
            response = request.json()
            self._responses.append(response)
        except requests.exceptions.ConnectionError as error:
            self._responses.append({'error': error})

    def imitate(self, command, get_value=True):
        self._responses = []
        expected_responses = len(self._remote_robots)
        if self.simulated_robot:
            simulated_result = self._run_command_on_simulation(command, get_value)
            self._responses.append({'result': simulated_result})
        for robot_ip_and_port in self._remote_robots:
            request_body = {'instruction': command, 'get': get_value}
            Thread(name=robot_ip_and_port, target=self._get_response, args=(robot_ip_and_port, request_body,)).start()
        while len(self._responses) != expected_responses:
            pass
        return self._responses
