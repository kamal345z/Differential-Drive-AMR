// IMU
#include <MPU6050_tockn.h>
#include <Wire.h>

// Constants
#define REFRESH_RATE 65.0 // Hz
#define TICKS_PER_REV 400
const float PID_K[2][3] = {
    {20.0, 0.01, 10.0}, // PID constants for R
    {20.0, 0.01, 10.0}  // PID constants for L
};

// MPU6050 mpu;
MPU6050 mpu6050(Wire);

// Pins
const byte EncoderX[2] = {3, 5}; // X encoder pins
const byte EncoderY[2] = {2, 4}; // Y encoder pins
const byte MotorR[2] = {9, 8};   // Right motor pins (PWM, DIR)
const byte MotorL[2] = {10, 7};  // Left motor pins (PWM, DIR)

// Variables
volatile long encTicks[2]; // 0 = Right 1 = Left
double velocity[2];
double angles[2], prevAngles[2];
unsigned long prevMillis;
String data;
float ang[2];
float prev_P[2];
float I[2];

// PID Function
float calc_PID(boolean is_left)
{
  float error = velocity[is_left] - ang[is_left];
  I[is_left] += error;
  I[is_left]=constrain(I[is_left], -1000 , 1000); 
  float d = prev_P[is_left] - error;
  prev_P[is_left] = error;
  return error * PID_K[is_left][0] + I[is_left] * PID_K[is_left][1] + d * PID_K[is_left][2];
}

// Interrupt Service Routines
void leftEncoderISR()
{
  if (digitalRead(EncoderX[1]) == HIGH)
  {
    encTicks[1]++;
  }
  else
  {
    encTicks[1]--;
  }
}

void rightEncoderISR()
{
  if (digitalRead(EncoderY[1]) != HIGH)
  {
    encTicks[0]++;
  }
  else
  {
    encTicks[0]--;
  }
}

void setup()
{
  Serial.begin(115200);
  while (!Serial)
    delay(10);
  Serial.setTimeout(3);

  // Set up IMU
  Wire.setClock(200000); // 200kHz I2C clock. Comment on this line if having compilation difficulties
  Wire.begin();
  mpu6050.begin();
  mpu6050.calcGyroOffsets(true);
  Serial.println(F("Ready"));

  // Set up motors
  for (byte i = 0; i < 2; i++)
  {
    pinMode(MotorR[i], OUTPUT);
    pinMode(MotorL[i], OUTPUT);
  }

  // Set up encoders
  for (byte i = 0; i < 2; i++)
  {
    pinMode(EncoderX[i], INPUT_PULLUP);
    pinMode(EncoderY[i], INPUT_PULLUP);
  }

  // Attach interrupts
  attachInterrupt(digitalPinToInterrupt(EncoderX[0]), leftEncoderISR, RISING);
  attachInterrupt(digitalPinToInterrupt(EncoderY[0]), rightEncoderISR, RISING);

  // Reserve space for encoder data
  data.reserve(25);

  // Initialize Sync
  while (Serial.read() != '?')
  {
    delay(10);
  }
  while (Serial.available())
    Serial.read(); // Clear the buffer
  Serial.write('#');
  while (Serial.read() != '!')
  {
    delay(10);
  }
}

void loop()
{
  // Calculate target interval based on REFRESH_RATE
  unsigned long interval = (unsigned long)(1000.0 / REFRESH_RATE);
  unsigned long currentMillis = millis();

  // Check if enough time has passed since last data send
  if (currentMillis - prevMillis >= interval)
  {
    prevMillis = currentMillis;

    // Send encoder data
    Serial.write('{');
    // Calculate Angles
    for (byte i = 0; i < 2; i++)
    {
      angles[i] = (encTicks[i] * 2.0 * PI) / TICKS_PER_REV;
      Serial.print(angles[i]);
      Serial.write('|');
    }

    // Calucalte Velocites
    for (byte i = 0; i < 2; i++)
    {
      velocity[i] = (angles[i] - prevAngles[i]) * REFRESH_RATE; // rad/s
      prevAngles[i] = angles[i];
      Serial.print(velocity[i]);
      Serial.write('|');
    }

    // Calculate Yaw
    mpu6050.update();
    float yaw = mpu6050.getAngleZ();
    if (yaw == 0b0)
      yaw = 0.0;
    Serial.print(yaw * DEG_TO_RAD);
    Serial.print(F("}\n"));
    Serial.flush(); // Ensure all data is sent before delay
  }
  // Parse Angular Velocity commands (non-blocking, can happen anytime)
  if (Serial.available() > 0)
  {
    data = Serial.readStringUntil('\n');
    data.trim(); // Remove any leading/trailing whitespace
    while (Serial.available() > 0)
      Serial.read(); // Clear the buffer
    if (data.startsWith("[") && data.endsWith("]"))
    {
      data.remove(0, 1);
      data.remove(data.length() - 1, 1); // Remove '[' and ']'

      // Parse data for 3 values
      ang[0] = data.substring(0, data.indexOf("|")).toFloat();      // Right Motor
      ang[1] = data.substring(data.lastIndexOf("|") + 1).toFloat(); // Left Motor
    }
  }

  // PID - Angular Velocity to PWM
  for (byte i = 0; i < 2; i++)
  {
    float pid_output = -calc_PID(i);
    int pwm_value = constrain((int)pid_output, -255, 255);
    // Serial.print("i=");
    // Serial.print(i);
    // Serial.print("\t");
    // Serial.print(pwm_value);
    // Serial.print("\t");

    // Set motor direction and speed
    if (i == 1)
    {
      digitalWrite(MotorR[1], pwm_value > 0 ? HIGH : LOW);
      analogWrite(MotorR[0], abs(pwm_value));
    }
    else
    {
      digitalWrite(MotorL[1], pwm_value > 0 ? HIGH : LOW);
      analogWrite(MotorL[0], abs(pwm_value));
    }
  }
  // Serial.println();
}