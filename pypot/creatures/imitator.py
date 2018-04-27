import requests
import json
from threading import Thread


class Imitator(object):
    def __init__(self, remote_robots=[], simulated_robot=None, real_robot=None):
        self._simulated_robot = simulated_robot
        self._real_robot = real_robot
        self._remote_robots = remote_robots
        self._responses = []

    @property
    def simulated_robot(self):
        return self._simulated_robot

    @property
    def real_robot(self):
        return self._real_robot

    @property
    def remote_robots(self):
        return self._remote_robots

    def _run_command_on_local_robot(self, robot, command, get_value=True):
        formatted_command = '{}.{}'.format(robot, command)
        try:
            if get_value:
                return {'result': eval(formatted_command)}
            else:
                exec formatted_command
                return {'result': None}
        except Exception as error:
            return {'error': error}

    def _get_remote_response(self, ip_and_port, payload):
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
            expected_responses += 1
            simulated_robot_result = self._run_command_on_local_robot('self.simulated_robot', command, get_value)
            self._responses.append(simulated_robot_result)

        if self.real_robot:
            expected_responses += 1
            real_robot_result = self._run_command_on_local_robot('self.real_robot', command, get_value)
            self._responses.append(real_robot_result)

        for robot_ip_and_port in self._remote_robots:
            request_body = {'instruction': command, 'get': get_value}
            Thread(name=robot_ip_and_port,
                   target=self._get_remote_response,
                   args=(robot_ip_and_port, request_body,)
                   ).start()

        while len(self._responses) != expected_responses:
            pass

        return self._responses
