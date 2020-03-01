/* 
This is a test sketch for the Adafruit assembled Motor Shield for Arduino v2
It won't work with v1.x motor shields! Only for the v2's with built in PWM
control

For use with the Adafruit Motor Shield v2 
---->	http://www.adafruit.com/products/1438
*/

#include <Wire.h>
#include <Adafruit_MotorShield.h>

Adafruit_MotorShield AFMSbot(0x61); // Rightmost jumper closed
Adafruit_MotorShield AFMStop(0x60); // Default address, no jumpers

// On the top shield, connect two steppers, each with 200 steps
Adafruit_StepperMotor *Y = AFMStop.getStepper(200, 1);
Adafruit_StepperMotor *Z = AFMStop.getStepper(200, 2);

// On the bottom shield connect a stepper to port M3/M4 with 200 steps
Adafruit_StepperMotor *X = AFMSbot.getStepper(200, 2);
// And a DC Motor to port M1

String readString;

double curr_x = 0;
double curr_y = 0;
double curr_z = 0;

int steps_per_mm = 132;

void setup() {
  while (!Serial);
  Serial.begin(9600);           // set up Serial library at 9600 bps
  Serial.println("MMMMotor party!");

  AFMSbot.begin(); // Start the bottom shield
  AFMStop.begin(); // Start the top shield
}

void goto_xy(float x, float y){
  uint8_t dir_x = FORWARD;
  uint8_t dir_y = FORWARD;
  if (x < curr_x) dir_x = BACKWARD;
  if (y < curr_y) dir_y = BACKWARD;
  int xsteps = abs(x * steps_per_mm);
  int ysteps = abs(y * steps_per_mm);
  for (int i = 0; i<max(xsteps, ysteps); i++){
    if (i < xsteps) X->onestep(dir_x, INTERLEAVE);
    if (i < ysteps) Y->onestep(dir_y, INTERLEAVE);
  }
}

void goto_z(float z){
  uint8_t dir_z = FORWARD;
  if (z < curr_z) dir_z = BACKWARD;
  int zsteps = abs(z * steps_per_mm);
  for (int i = 0; i<zsteps; i++){
    Z->onestep(dir_z, INTERLEAVE);
  }
}

void loop()
{
    while (!Serial.available()) {} // wait for data to arrive

    while (Serial.available())
    {
        if (Serial.available())
        {
            char c = Serial.read();
            readString += c;
            delay(2);
        }
    }

    char *readin = (char *)readString.c_str();
    char *x = strtok(readin, ",");
    char *y = strtok(NULL, ",");

    if (strcmp(x, "z") == 0)
    {
        goto_z(atof(y));
        Serial.println(1);
    } else
    {
        goto_xy(atof(x), atof(y));
        Serial.println(1);
    }
    Serial.flush();
    readString = "";
}
