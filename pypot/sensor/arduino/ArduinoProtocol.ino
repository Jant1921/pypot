const uint8_t OUTPUT_HEADER_START_SYMBOL = '~';
const uint8_t INPUT_HEADER_START_SYMBOL = '|';

const int ledBuiltIn =  LED_BUILTIN;// the number of the LED pin

unsigned long previousTransmitMillis = 0;
unsigned long transmitMillis = millis();
const int transmitInterval = 1000;

#pragma region Messages Codes
const int CODE_STATUS_MESSAGE = 0x00;
#pragma endregion

#pragma region Header Buffer Registers
const uint8_t OUTPUT_HEADER_BUFFER_SIZE = 0x04;
uint8_t output_header_buffer[OUTPUT_HEADER_BUFFER_SIZE];
const uint8_t INPUT_HEADER_BUFFER_SIZE = 0x04;
uint8_t input_header_buffer[INPUT_HEADER_BUFFER_SIZE];
const int HEADER_START_CODE = 0;
const int HEADER_MESSAGE_TYPE = 1;
const int HEADER_DATA_SIZE = 2;
const int HEADER_CHECKSUM = 3;
#pragma endregion

#pragma region Data Buffer Registers
const uint8_t OUTPUT_DATA_BUFFER_SIZE = 0x11;
uint8_t output_data_buffer[OUTPUT_DATA_BUFFER_SIZE];

const int DATA_CAPACITIVE_1 = 0;
const int DATA_CAPACIVITE_2 = 1;
const int DATA_CAPACITIVE_3 = 2;
const int DATA_CAPACITIVE_4 = 3;

const int DATA_MIC_1_0 = 4;
const int DATA_MIC_1_1 = 5;
const int DATA_MIC_1_2 = 6;
const int DATA_MIC_1_3 = 7;

const int DATA_MIC_2_0 = 8;
const int DATA_MIC_3_1 = 9;
const int DATA_MIC_4_2 = 10;
const int DATA_MIC_5_3 = 11;

const int DATA_MOTOR_1_0 = 12;
const int DATA_MOTOR_1_1 = 13;

const int DATA_MOTOR_2_0 = 14;
const int DATA_MOTOR_2_1 = 15;

const int DATA_CHECKSUM = 16;
#pragma endregion

void setup() {
  pinMode(ledBuiltIn, OUTPUT);
  while (!Serial);
  Serial.begin(115200);
  output_header_buffer[HEADER_START_CODE] = OUTPUT_HEADER_START_SYMBOL;
  input_header_buffer[HEADER_START_CODE] = INPUT_HEADER_START_SYMBOL;
}

void fillStatusDataBuffer(){
  // TO_DO replace with real data 
  output_data_buffer[DATA_CAPACITIVE_1] = 0x01;
  output_data_buffer[DATA_CAPACIVITE_2] = 0x02;
  output_data_buffer[DATA_CAPACITIVE_3] = 0x03;
  output_data_buffer[DATA_CAPACITIVE_4] = 0x04;
  
  output_data_buffer[DATA_MIC_1_0] = 0x05;
  output_data_buffer[DATA_MIC_1_1] = 0x06;
  output_data_buffer[DATA_MIC_1_2] = 0x07;
  output_data_buffer[DATA_MIC_1_3] = 0x08;
  
  output_data_buffer[DATA_MIC_2_0] = 0x09;
  output_data_buffer[DATA_MIC_3_1] = 0x0A;
  output_data_buffer[DATA_MIC_4_2] = 0x0B;
  output_data_buffer[DATA_MIC_5_3] = 0x0C;
  
  output_data_buffer[DATA_MOTOR_1_0] = 0x0D;
  output_data_buffer[DATA_MOTOR_1_1] = 0x0E;
  
  output_data_buffer[DATA_MOTOR_2_0] = 0x0F;
  output_data_buffer[DATA_MOTOR_2_1] = 0x10;
  // don't change this line since calculates the checksum of the data
  output_data_buffer[DATA_CHECKSUM] = buffer_checksum(output_data_buffer, OUTPUT_DATA_BUFFER_SIZE);
}

void sendStatusMessage(){
  output_header_buffer[HEADER_MESSAGE_TYPE] = CODE_STATUS_MESSAGE;
  output_header_buffer[HEADER_DATA_SIZE] = OUTPUT_DATA_BUFFER_SIZE;
  output_header_buffer[HEADER_CHECKSUM] = buffer_checksum(output_header_buffer, OUTPUT_HEADER_BUFFER_SIZE);
  fillStatusDataBuffer();
  Serial.write(output_header_buffer, OUTPUT_HEADER_BUFFER_SIZE);
  Serial.write(output_data_buffer, OUTPUT_DATA_BUFFER_SIZE);
}

void verifyIncomingData(){
  int incomingByte = Serial.read();
  if (incomingByte != -1) {
    if (incomingByte == '1') {
      digitalWrite(ledBuiltIn, HIGH);
    } else {
      digitalWrite(ledBuiltIn, LOW);
    }
  }
}

void loop() {
  verifyIncomingData();

  transmitMillis = millis();
  if (transmitMillis - previousTransmitMillis >= transmitInterval) {
    previousTransmitMillis = transmitMillis;
    sendStatusMessage();
  }
}

uint8_t buffer_checksum(uint8_t pBuffer[], uint8_t bufferSize) {
  uint8_t result = 0;
  uint16_t sum = 0;
  for (uint8_t i = 0; i < (bufferSize - 1); i++) {
    sum += pBuffer[i];
  }
  result = sum & 0xFF;
  return result;
}

