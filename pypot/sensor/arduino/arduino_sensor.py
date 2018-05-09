from serial import Serial
from time import sleep
from threading import Thread
from ...robot.sensor import Sensor

STATUS_MESSAGE_CODE = 0x00 # DONE
MOVE_MOTORS_MESSAGE_CODE = 0x01 # TODO
PLAY_SOUND_MESSAGE_CODE = 0x02 # TODO
CONFIG_FREQUENCY_MESSAGE_CODE = 0x03 # TODO
ODROID_ACK_MESSAGE_CODE = 0x10 # TODO
ARDUINO_ACK_MESSAGE_CODE = 0x11 # ADAFRUIT

HEADER_START_SYMBOL = '~'
DATA_START_SYMBOL = '|'

HEADER_START_CODE = 0
HEADER_MESSAGE_TYPE = 1
HEADER_DATA_SIZE = 2
HEADER_CHECKSUM = 3


def valid_checksum(buffer_list):
    value = 0
    for byte in range(0, len(buffer_list) - 1):
        value = value + int(buffer_list[byte], 16)
    return ("%02x" % value)[-2:] == buffer_list[-1]  # checksum value & 0xFF


def hex_string_to_int(hex_string):
    return int(hex_string, 16)


class Sender(object):
    def __init__(self, arduino):
        self.arduino = arduino
        self._output_header_buffer = []
        self._output_data_buffer = []
        self._header_start_code = "%02x" % ord(DATA_START_SYMBOL)  # "%02x" converts to hex

    def _clear_output_buffers(self):
        self._output_header_buffer = [self._header_start_code]
        self._output_data_buffer = []

    def _send_data(self):
        self.arduino.write(self._output_header_buffer + self._output_data_buffer)
        self._clear_output_buffers()

    def move_motors(self):
        self._output_header_buffer[HEADER_MESSAGE_TYPE] = MOVE_MOTORS_MESSAGE_CODE
        # final
        self._send_data()
        pass # TODO se debe enviar posicion nueva a ambos motores?

    def play_sound(self):
        self._output_header_buffer[HEADER_MESSAGE_TYPE] = PLAY_SOUND_MESSAGE_CODE
        # final
        self._send_data()
        pass

    def config_frequency(self):
        self._output_header_buffer[HEADER_MESSAGE_TYPE] = CONFIG_FREQUENCY_MESSAGE_CODE
        # final
        self._send_data()
        pass

    def send_ack_message(self):
        self._output_header_buffer[HEADER_MESSAGE_TYPE] = ODROID_ACK_MESSAGE_CODE
        self._output_header_buffer[HEADER_DATA_SIZE] = 0x00
        self._output_header_buffer[HEADER_CHECKSUM] = valid_checksum(self._output_header_buffer)
        self._send_data()

class Receiver(object):
    def __init__(self, arduino):
        self.arduino = arduino
        self._input_header_buffer = []
        self._input_data_buffer = []
        self._input_header_size = 4
        self._input_header_found = False
        self._is_header = False
        self._header_start_code = "%02x" % ord(HEADER_START_SYMBOL)  # "%02x" converts to hex
        self.running = True

    def _clear_input_buffers(self):
        self._input_header_buffer = []
        self._input_data_buffer = []

    def _reset_data(self):
        self._clear_input_buffers()
        self._input_header_found = False
        self._is_header = False

    def _get_byte(self):
        input_data = self.arduino.read(1)  # arduino.read(1)
        if len(input_data) > 0:
            return "%02x" % ord(input_data)
        return None

    def _process_incomming_message(self):
        if hex_string_to_int(self._input_header_buffer[HEADER_MESSAGE_TYPE]) == STATUS_MESSAGE_CODE:
            print 'status message'
        elif hex_string_to_int(self._input_header_buffer[HEADER_MESSAGE_TYPE]) == ARDUINO_ACK_MESSAGE_CODE:
            print 'Ack message'

    def _read_data(self, buffer_size):
        if buffer_size == 0:  # message without data
            print 'data 0'
            return True
        while buffer_size > 0:
            hex_input = self._get_byte()
            if hex_input:
                self._input_data_buffer.append(hex_input)
                buffer_size -= 1
        print self._input_data_buffer
        if valid_checksum(self._input_data_buffer):
            self._process_incomming_message()
            print 'valid data'
            return True
        else:
            # invalid data
            print 'invalid data'
            return False

    def _check_header_start(self, byte):
        if byte == self._header_start_code:
            if not self._input_header_found:
                self._is_header = True
                self._input_header_found = True
                self._clear_input_buffers()

    def _header_buffer_full(self):
        return len(self._input_header_buffer) == self._input_header_size

    def loop(self):
        while self.running:
            hex_input = self._get_byte()
            if hex_input:
                self._check_header_start(hex_input)
                self._input_header_buffer.append(hex_input)
                if self._header_buffer_full():
                    print self._input_header_buffer
                    if valid_checksum(self._input_header_buffer):
                        print 'valid header'
                        self._read_data(int(self._input_header_buffer[HEADER_DATA_SIZE], 16))
                    else:
                        print 'invalid header'
                    self._reset_data()


class ArduinoSensor(Sensor):
    registers = Sensor.registers + ['port', 'baud']

    def __init__(self, name, port, baud):
        Sensor.__init__(self, name)
        self.port = port
        self.baud = baud
        self._arduino = None
        self._receiver = None
        self._sender = None
        self._status_loop = None
        self.running = False
        self.start()

    def start(self):
        self._arduino = Serial(self.port, self.baud, timeout=0.03)  # Windows
        sleep(1)  # give the connection a second to settle
        self._receiver = Receiver(self._arduino)
        self._sender = Sender(self._arduino)
        self._status_loop = Thread(target=self._receiver.loop)
        self._status_loop.daemon = True
        self._status_loop.start()
        self.running = True

    def close(self):
        self.running = False
        self._receiver.running = False
        self._status_loop.join()
        self._arduino.close()
