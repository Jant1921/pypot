#include "capacitive.h"
// Capacitive sensors
Capacitive capacitive1(4);
Capacitive capacitive2(6);
Capacitive capacitive3(8);
Capacitive capacitive4(5);
// Header start codes
const uint8_t OUTPUT_HEADER_START_VALUE = 0x7e;
const uint8_t INPUT_HEADER_START_VALUE = 0x7c;
// the number of the LED pin
const int ledBuiltIn =  LED_BUILTIN;
// Frequency interval varaibles
unsigned long previousTransmitMillis = 0;
unsigned long transmitMillis = millis();
unsigned long transmitInterval = 5000;
/** Messages Codes **/
const int STATUS_MESSAGE_CODE = 0x00;
const int MOVE_MOTORS_MESSAGE_CODE = 0x01;
const int PLAY_SOUND_MESSAGE_CODE = 0x02;
const int CONFIG_FREQUENCY_MESSAGE_CODE = 0x03;
const int ODROID_ACK_MESSAGE_CODE = 0x10;
const int ARDUINO_ACK_MESSAGE_CODE = 0x11;
/** Header Buffer Registers **/
// Output Header
const uint8_t OUTPUT_HEADER_BUFFER_SIZE = 0x04;
uint8_t outputHeaderBuffer[OUTPUT_HEADER_BUFFER_SIZE];
// Header data position
const int HEADER_START_CODE = 0;
const int HEADER_MESSAGE_TYPE = 1;
const int HEADER_DATA_SIZE = 2;
const int HEADER_CHECKSUM = 3;
/** Data Buffer Registers **/
// Output Buffer
const uint8_t OUTPUT_DATA_BUFFER_SIZE = 0x11;
uint8_t outputDataBuffer[OUTPUT_DATA_BUFFER_SIZE];
// Capacitives
const int DATA_CAPACITIVE_1 = 0;
const int DATA_CAPACIVITE_2 = 1;
const int DATA_CAPACITIVE_3 = 2;
const int DATA_CAPACITIVE_4 = 3;
// Microphone 1
const int DATA_MIC_1_0 = 4;
const int DATA_MIC_1_1 = 5;
const int DATA_MIC_1_2 = 6;
const int DATA_MIC_1_3 = 7;
// Microphone 2
const int DATA_MIC_2_0 = 8;
const int DATA_MIC_3_1 = 9;
const int DATA_MIC_4_2 = 10;
const int DATA_MIC_5_3 = 11;
// Motor 1
const int DATA_MOTOR_1_0 = 12;
const int DATA_MOTOR_1_1 = 13;
// Motor 2
const int DATA_MOTOR_2_0 = 14;
const int DATA_MOTOR_2_1 = 15;
// Checksum position
const int DATA_CHECKSUM = 16;
// Receiver Variables
const int TRACK_LENGTH_DATA_SIZE = 2;
const int FREQUENCY_DATA_SIZE = 4;
const int MOTOR_POSITION_DATA_SIZE = 4;
const uint8_t INPUT_HEADER_BUFFER_SIZE = 0x04;
uint8_t inputHeaderBuffer[INPUT_HEADER_BUFFER_SIZE];
int inputHeaderActualPosition = 0;
bool inputHeaderFound = false;
bool isHeader = false;
uint8_t trackLengthBytes[TRACK_LENGTH_DATA_SIZE];
uint8_t motorPositionBytes[MOTOR_POSITION_DATA_SIZE];
uint8_t trackNumber = 0x00;
uint8_t trackLength = 0x0000;
uint8_t motor1Direction = 0x00;
uint8_t motor2Direction = 0x00;
uint8_t motor1Position = 0x00000000;
uint8_t motor2Position = 0x00000000;

bool messageReceived = false;

/* Generates a checksum from the given buffer */
uint8_t buffer_checksum(uint8_t pBuffer[], uint8_t bufferSize) {
  uint8_t result = 0;
  uint16_t sum = 0;
  for (uint8_t i = 0; i < (bufferSize - 1); i++) {
    sum += pBuffer[i];
  }
  result = sum & 0xFF;
  return result;
}

/************************************************************************
 ************************Receiver Methods********************************
 ************************************************************************/

/* Verify if the header message type is valid */
bool isValidHeaderMessageType(uint8_t pMessageType){
  switch (pMessageType){
    case MOVE_MOTORS_MESSAGE_CODE:
      break;
    case PLAY_SOUND_MESSAGE_CODE:
      break;
    case CONFIG_FREQUENCY_MESSAGE_CODE:
      break;
    case ODROID_ACK_MESSAGE_CODE:
      break;
    default:
      return false;
  }
  return true;
}

/* Returns a value from separated bytes 
 * For example: from bytes 0x07, 0x81 returns 0x0781 
*/
uint16_t parseBytesToNumber(uint8_t bytes[], int arraySize){
  uint16_t value = 0;
  for (int i = 0; i < arraySize; i++){
    value = value << 8;
    value += bytes[i];
  }
  return value;
}

/* Moves the header buffer pointer to the beginning */
void clearInputBuffers(){
  inputHeaderActualPosition = 0;
}

/* If a header message start code is found,
 * initializes the parameters to start to read the header message
 */
void checkHeaderStart(uint8_t byte){
  if(byte == INPUT_HEADER_START_VALUE){
    if(!inputHeaderFound){
      isHeader = true;
      inputHeaderFound = true;
      clearInputBuffers();
    } 
  }
}

/* Checks if header buffer is full */
bool isHeaderBufferFull(){
  return inputHeaderActualPosition == INPUT_HEADER_BUFFER_SIZE;
}

/* Compares the received checksum and the checksum generated with received data  */
bool isValidChecksum(uint8_t pBuffer[], uint8_t pBufferSize, uint8_t pChecksum){
  uint8_t calculatedChecksum = buffer_checksum(pBuffer,pBufferSize);
  return calculatedChecksum == pChecksum;
}

/* Clear reciever buffers */
void resetInputData(){
  clearInputBuffers();
  inputHeaderFound = false;
  isHeader = false;
}

/* Returns the real value of separated bytes that indicates the new motor position */
uint8_t getMotorPositionValueFromBytes(uint8_t byte0, uint8_t byte1, uint8_t byte2, uint8_t byte3){
  motorPositionBytes[0] = byte0;
  motorPositionBytes[1] = byte1;
  motorPositionBytes[2] = byte2;
  motorPositionBytes[3] = byte3;
  return parseBytesToNumber(motorPositionBytes, MOTOR_POSITION_DATA_SIZE);
}

/* Checks the message type and perform an specific task for each type */
void processData(uint8_t pMessageType, uint8_t pMessageData[]){
  switch (pMessageType){
    case MOVE_MOTORS_MESSAGE_CODE:
      motor1Direction = pMessageData[0];
      motor2Direction = pMessageData[1];
      motor1Position = getMotorPositionValueFromBytes(pMessageData[2], pMessageData[3], pMessageData[4], pMessageData[5]);
      motor2Position = getMotorPositionValueFromBytes(pMessageData[6], pMessageData[7], pMessageData[8], pMessageData[9]);
      // move motors function
      digitalWrite(ledBuiltIn, HIGH);
      messageReceived = true;
      break;
    case PLAY_SOUND_MESSAGE_CODE:
      trackLengthBytes[0] = pMessageData[1];
      trackLengthBytes[1] = pMessageData[2];
      trackNumber = pMessageData[0];
      trackLength = parseBytesToNumber(trackLengthBytes, TRACK_LENGTH_DATA_SIZE);
      // play function
      digitalWrite(ledBuiltIn, HIGH);
      messageReceived = true;
      break;
    case CONFIG_FREQUENCY_MESSAGE_CODE:
      transmitInterval = parseBytesToNumber(pMessageData, FREQUENCY_DATA_SIZE);
      digitalWrite(ledBuiltIn, HIGH);
      messageReceived = true;
      break;
    case ODROID_ACK_MESSAGE_CODE:
      digitalWrite(ledBuiltIn, HIGH);
      messageReceived = true;
      break;
    default:
      break;
  }
}

/* Given the data size, reads an specific number of bytes to check if is valid */
bool verifyIncomingMessageData(uint8_t dataBufferSize){
  if(dataBufferSize == 0){
    processData(inputHeaderBuffer[HEADER_MESSAGE_TYPE], new uint8_t[0]);
    return true;
  }
  uint8_t inputDataBuffer[dataBufferSize];
  int bytePosition = 0;
  int incomingDataByte = -1;
  while (bytePosition < dataBufferSize){
    incomingDataByte = Serial.read();
    if (incomingDataByte != -1) {
      inputDataBuffer[bytePosition] = incomingDataByte;
      bytePosition++;
    }
  }
  if(isValidChecksum(inputDataBuffer, dataBufferSize, incomingDataByte)){
    processData(inputHeaderBuffer[HEADER_MESSAGE_TYPE], inputDataBuffer);
    return true;
  } else{
    return false;
  }
}

/* Read the input message header, trying to find a valid header.
 * If a valid header is found, proceed to process the message data.
 */
void verifyIncomingMessageHeader(){
  int incomingByte = Serial.read();
  if (incomingByte != -1) {
    checkHeaderStart(incomingByte);
    inputHeaderBuffer[inputHeaderActualPosition] = incomingByte;
    inputHeaderActualPosition++;
    if(isHeaderBufferFull()){
      if(isValidChecksum(inputHeaderBuffer, INPUT_HEADER_BUFFER_SIZE, incomingByte)
          && isValidHeaderMessageType(inputHeaderBuffer[HEADER_MESSAGE_TYPE])){
        verifyIncomingMessageData(inputHeaderBuffer[HEADER_DATA_SIZE]);
      }
      resetInputData();
    }
  }
}

/************************************************************************
 **************************Sender Methods********************************
 ************************************************************************/

/* Fills the status message data buffer with sensors values */
void fillStatusDataBuffer(){
  // TO_DO replace with real data 
  // Capacitives Data
  outputDataBuffer[DATA_CAPACITIVE_1] = capacitive1.getState();
  outputDataBuffer[DATA_CAPACIVITE_2] = capacitive2.getState();
  outputDataBuffer[DATA_CAPACITIVE_3] = capacitive3.getState();
  outputDataBuffer[DATA_CAPACITIVE_4] = capacitive4.getState();
  // Microphone 1 data
  outputDataBuffer[DATA_MIC_1_0] = 0x05;
  outputDataBuffer[DATA_MIC_1_1] = 0x06;
  outputDataBuffer[DATA_MIC_1_2] = 0x07;
  outputDataBuffer[DATA_MIC_1_3] = 0x08;
  // Microphone 2 data
  outputDataBuffer[DATA_MIC_2_0] = 0x09;
  outputDataBuffer[DATA_MIC_3_1] = 0x0A;
  outputDataBuffer[DATA_MIC_4_2] = 0x0B;
  outputDataBuffer[DATA_MIC_5_3] = 0x0C;
  // Motor 1 Position
  outputDataBuffer[DATA_MOTOR_1_0] = 0x0D;
  outputDataBuffer[DATA_MOTOR_1_1] = 0x0E;
  //Motor 2 position
  outputDataBuffer[DATA_MOTOR_2_0] = 0x0F;
  outputDataBuffer[DATA_MOTOR_2_1] = 0x10;
  // don't change this line bellow since calculates the checksum of the data
  outputDataBuffer[DATA_CHECKSUM] = buffer_checksum(outputDataBuffer, OUTPUT_DATA_BUFFER_SIZE);
}

void fillHeaderBuffer(uint8_t pMessageCode, uint8_t pDataSize){
  outputHeaderBuffer[HEADER_MESSAGE_TYPE] = pMessageCode;
  outputHeaderBuffer[HEADER_DATA_SIZE] = pDataSize;
  outputHeaderBuffer[HEADER_CHECKSUM] = buffer_checksum(outputHeaderBuffer, OUTPUT_HEADER_BUFFER_SIZE);
}

/* Initialize the output header to send the status message*/
void sendStatusMessage(){
  fillHeaderBuffer(STATUS_MESSAGE_CODE, OUTPUT_DATA_BUFFER_SIZE);
  fillStatusDataBuffer();
  Serial.write(outputHeaderBuffer, OUTPUT_HEADER_BUFFER_SIZE);
  Serial.write(outputDataBuffer, OUTPUT_DATA_BUFFER_SIZE);
}

void sendAckMessage(){
  fillHeaderBuffer(ARDUINO_ACK_MESSAGE_CODE, 0);
  Serial.write(outputHeaderBuffer, OUTPUT_HEADER_BUFFER_SIZE);
}

/************************************************************************
 ************************Arduino Functions*******************************
 ************************************************************************/
void setup() {
  pinMode(ledBuiltIn, OUTPUT);
  while (!Serial);
  Serial.begin(115200);
  outputHeaderBuffer[HEADER_START_CODE] = OUTPUT_HEADER_START_VALUE;
}

void loop() {
  verifyIncomingMessageHeader();
  transmitMillis = millis();
  if (messageReceived){
    messageReceived = false;
    sendAckMessage();
  }
  if (transmitMillis - previousTransmitMillis >= transmitInterval) {
    previousTransmitMillis = transmitMillis;
    sendStatusMessage();
    digitalWrite(ledBuiltIn, LOW);
  }
}
