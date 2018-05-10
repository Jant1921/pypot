const uint8_t OUTPUT_HEADER_START_VALUE = 0x7e;
const uint8_t INPUT_HEADER_START_VALUE = 0x7c;

const int ledBuiltIn =  LED_BUILTIN;// the number of the LED pin

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
const uint8_t INPUT_HEADER_BUFFER_SIZE = 0x04;
uint8_t inputHeaderBuffer[INPUT_HEADER_BUFFER_SIZE];
int inputHeaderActualPosition = 0;
bool inputHeaderFound = false;
bool isHeader = false;
uint8_t soundLengthBytes[2];
uint8_t soundTrack = 0x00;
uint8_t trackLength = 0x0000;

uint8_t buffer_checksum(uint8_t pBuffer[], uint8_t bufferSize) {
  uint8_t result = 0;
  uint16_t sum = 0;
  for (uint8_t i = 0; i < (bufferSize - 1); i++) {
    sum += pBuffer[i];
  }
  result = sum & 0xFF;
  return result;
}

/************************************************************************/
/************************************************************************/
/************************************************************************/
/*
 * Receiver Methods
 */
uint16_t parseBytesToNumber(uint8_t bytes[], int arraySize){
  uint16_t value = 0;
  for (int i = 0; i < arraySize; i++){
    value = value * 256;
    value += bytes[i];
  }
  return value;
}

void clearInputBuffers(){
  inputHeaderActualPosition = 0;
}

void checkHeaderStart(uint8_t byte){
  if(byte == INPUT_HEADER_START_VALUE){
    if(!inputHeaderFound){
      isHeader = true;
      inputHeaderFound = true;
      clearInputBuffers();
    } 
  }
}

bool isHeaderBufferFull(){
  return inputHeaderActualPosition == INPUT_HEADER_BUFFER_SIZE;
}

bool isValidChecksum(uint8_t pBuffer[], uint8_t pBufferSize, uint8_t pChecksum){
  uint8_t calculatedChecksum = buffer_checksum(pBuffer,pBufferSize);
  return calculatedChecksum == pChecksum;
}

void resetInputData(){
  clearInputBuffers();
  inputHeaderFound = false;
  isHeader = false;
}

void processData(uint8_t pMessageType, uint8_t pMessageData[]){
  switch (pMessageType){
    case MOVE_MOTORS_MESSAGE_CODE:
      digitalWrite(ledBuiltIn, HIGH);
      break;
    case PLAY_SOUND_MESSAGE_CODE:
      soundLengthBytes[0] = pMessageData[1];
      soundLengthBytes[1] = pMessageData[2];
      soundTrack = pMessageData[0];
      trackLength = parseBytesToNumber(soundLengthBytes, 2);
      // play
      digitalWrite(ledBuiltIn, HIGH);
      break;
    case CONFIG_FREQUENCY_MESSAGE_CODE:
      transmitInterval = parseBytesToNumber(pMessageData, 4);
      digitalWrite(ledBuiltIn, HIGH);
      break;
    case ODROID_ACK_MESSAGE_CODE:
      digitalWrite(ledBuiltIn, HIGH);
      break;
    default:
      break;
  }
}

bool processInputData(uint8_t dataBufferSize){
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

void verifyIncomingData(){
  int incomingByte = Serial.read();
  if (incomingByte != -1) {
    checkHeaderStart(incomingByte);
    inputHeaderBuffer[inputHeaderActualPosition] = incomingByte;
    inputHeaderActualPosition++;
    if(isHeaderBufferFull()){
      if(isValidChecksum(inputHeaderBuffer, INPUT_HEADER_BUFFER_SIZE, incomingByte)){
        processInputData(inputHeaderBuffer[HEADER_DATA_SIZE]);
      }
      resetInputData();
    }
  }
}

/************************************************************************/
/************************************************************************/
/************************************************************************/
/*
 * Sender Methods
 */
void fillStatusDataBuffer(){
  // TO_DO replace with real data 
  outputDataBuffer[DATA_CAPACITIVE_1] = 0x01;
  outputDataBuffer[DATA_CAPACIVITE_2] = 0x02;
  outputDataBuffer[DATA_CAPACITIVE_3] = 0x03;
  outputDataBuffer[DATA_CAPACITIVE_4] = 0x04;
  
  outputDataBuffer[DATA_MIC_1_0] = 0x05;
  outputDataBuffer[DATA_MIC_1_1] = 0x06;
  outputDataBuffer[DATA_MIC_1_2] = 0x07;
  outputDataBuffer[DATA_MIC_1_3] = 0x08;
  
  outputDataBuffer[DATA_MIC_2_0] = 0x09;
  outputDataBuffer[DATA_MIC_3_1] = 0x0A;
  outputDataBuffer[DATA_MIC_4_2] = 0x0B;
  outputDataBuffer[DATA_MIC_5_3] = 0x0C;
  
  outputDataBuffer[DATA_MOTOR_1_0] = 0x0D;
  outputDataBuffer[DATA_MOTOR_1_1] = 0x0E;
  
  outputDataBuffer[DATA_MOTOR_2_0] = 0x0F;
  outputDataBuffer[DATA_MOTOR_2_1] = 0x10;
  // don't change this line since calculates the checksum of the data
  outputDataBuffer[DATA_CHECKSUM] = buffer_checksum(outputDataBuffer, OUTPUT_DATA_BUFFER_SIZE);
}

void sendStatusMessage(){
  outputHeaderBuffer[HEADER_MESSAGE_TYPE] = STATUS_MESSAGE_CODE;
  outputHeaderBuffer[HEADER_DATA_SIZE] = OUTPUT_DATA_BUFFER_SIZE;
  outputHeaderBuffer[HEADER_CHECKSUM] = buffer_checksum(outputHeaderBuffer, OUTPUT_HEADER_BUFFER_SIZE);
  fillStatusDataBuffer();
  Serial.write(outputHeaderBuffer, OUTPUT_HEADER_BUFFER_SIZE);
  Serial.write(outputDataBuffer, OUTPUT_DATA_BUFFER_SIZE);
}
/************************************************************************/
/************************************************************************/
/************************************************************************/
/*
 * Arduino Functions
 */
void setup() {
  pinMode(ledBuiltIn, OUTPUT);
  while (!Serial);
  Serial.begin(115200);
  outputHeaderBuffer[HEADER_START_CODE] = OUTPUT_HEADER_START_VALUE;
}

void loop() {
  verifyIncomingData();
  transmitMillis = millis();
  if (transmitMillis - previousTransmitMillis >= transmitInterval) {
    previousTransmitMillis = transmitMillis;
    sendStatusMessage();
    digitalWrite(ledBuiltIn, LOW);
  }
}

