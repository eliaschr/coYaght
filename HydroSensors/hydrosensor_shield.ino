/* Hydrobot sensor v3 (with optional h-bridges)
 by Dimitris Piperidis
 For EUGENIDES FOUNDATION (http://www.eugenfound.edu.gr)
 part of the program hydrobots (www.hydrobots.gr)
--------------------------------------------------------
ATTENTION! THE following copyright message is for historical reasons only.
This version has almost nothing in common with the original

original version: Sensor V3.1.1
MIT Sea Grant College Program
SeaPerch.MIT.edu
March 28 2011
Copyright 2011 MIT Sea Grant Collsege Program
*/

/*  ATTENTION! USE arduino-1.0.5 to compile
   
    Download link: 
    http://hydrobots.gr/index/wp-content/uploads/arduino-1.0.5-windows.zip
   
   
 */


/*  Copyright for this version (GPL)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

/*  The program is modified by 1st Junior High School of Gerakas for the project
 *   of coYaght, program "Junior Achievement Greece". The coYaght is the product of
 *   the virtual company DeepSeaRobotix.
 *   
 *   Students:
 *      Panagiotis Adamantiades
 *      Efstratios Amerikanos
 *      John Drosakis
 *      Helen Zografou
 *      Eleytheria Kalavrou
 *      Antonis Lekkas
 *      Antigoni Bouki
 *      
 *   Teachers:
 *      Theodore Kourtesis
 *      Elias Chrysocheris
 */

  // IMPORT LIBRARIES     
  //#include "SdFat.h"            // Library for micoSD card (Not used by coYaght)
  #include "stdio.h"              // Standard C input/output library
  #include "stdlib.h"             // Standoard C library
  #include "Wire.h"               // Serial communications library

  // DEFINE GLOBAL CONSTANTS
  //
  #define READ_SENSORS_DELAY 1000 //Interval at which data is taken (in msec)  
  
  // Define outputs for controlling the motors
  #define MR1 4 //digital D4
  #define MR2 3 //digital D3 (PWM)
  #define MR_SD 11
  #define ML1 7 //digital D7
  #define ML2 6 //digital D6 (PWM)
  #define ML_SD 12
  #define MD1 8 //digital D8
  #define MD2 9 //digital D9 (PWM)
  #define MD_SD 10
  
  // Digital pins 
  #define TSL_FREQ_PIN 5          // Light sensor OUT
  #define TSL_CONVERT_FACTOR 100


  #define DS1307_I2C_ADDRESS 0x68 // This is the I2C address
  
  // Analog pins
  #define aTemperature 2          // Temperature value
  #define aPressure 1             // Pressure value
  #define aBatt 0                 // Battery value
  
  #define LINE_FEED 10            // Line-Feed character
  
  // GLOBAL VARIABLES
  boolean resetcounter = true;
  unsigned long previousMillis = 0;
  unsigned long diffMillis;
  boolean domeasure = false;
  boolean serwrite = false;
  unsigned long cnt_pul_lux = 0;
  volatile byte cnt_pul_ovs = 0;
  char bat_type = 1;              // Changed by 1st Gym Geraka to reflect 12V battery

  // Block for SD Card Read/Write (Not used by coYaght)
  //sdcard
  //const uint8_t SD_CHIP_SELECT = SS;
  //SdFat sd;
  //SdFile file;

  //boolean writetosd = true;
  boolean numbermode = false;
  
  char command = 0;  // This is the command char, in ascii form, sent from the serial port   

  byte second, minute, hour, dayOfWeek, dayOfMonth, month, year;
  
  double pressure;
  double pressure0;
  double depth;
  double temp; 
  double light; 
  double batt;

  int light_overflow;
  int pressure_overflow;
  int temp_overflow;
  int depth_overflow;
  int batt_overflow;

  char printString[90];
  
  //Software reset function
void(* resetFunc) (void) = 0;//declare reset function at address 0  

  //Setup procedure
void setup(void) {
  Serial.begin (9600);
  Serial.println("STATUS: Initializing");
  
  // Set analog reference voltage to 5V
  analogReference(DEFAULT);
  
  pinMode(TSL_FREQ_PIN, INPUT);
  pinMode(A0, INPUT);
  pinMode(A1, INPUT);
  pinMode(A2, INPUT);
  //Set pull up resistor
  //digitalWrite(A5, HIGH);
  
  // Motors
  pinMode(MR1, OUTPUT);
  pinMode(MR2, OUTPUT);
  pinMode(MR_SD, OUTPUT);
  pinMode(ML1, OUTPUT);
  pinMode(ML2, OUTPUT);
  pinMode(ML_SD, OUTPUT);
  pinMode(MD1, OUTPUT);
  pinMode(MD2, OUTPUT);
  pinMode(MD_SD, OUTPUT);
  rightmotor(0);
  leftmotor(0);
  depthmotor(0);
  // Hardware Timer/Counter setup (for measuring pulses of lux sensor)
  TCCR1A=0;              // Reset Timer/Counter Control Register A
  bitSet(TCCR1B ,CS12);  // Counter Clock source is external pin
  bitSet(TCCR1B ,CS11);  // Clock on rising edge 
  bitSet(TCCR1B ,CS10);  
  
  // Initialize RTC Clock
  Wire.begin();
  
  delay(1000);
  zeroPressureSensor();
  
  // initialize the SD card at SPI_HALF_SPEED to avoid bus errors with
  // breadboards.  use SPI_FULL_SPEED for better performance.
  // The following block is commented out as it is NOT used in coYaght
  //if (!sd.begin(SD_CHIP_SELECT, SPI_HALF_SPEED)){
  //   Serial.println("ERROR: SD card problem or missing");
  //   writetosd = false;
  //}
  
  // Write the Reset message
  //writeToCard("\r\nRESET\r\n"); //Not used in coYaght
  Serial.println("STATUS: Setup complete");
}

void loop(void) {
  char charread[1];   
  // Read Serial data if any 
  if (Serial.available()) {  // Look for char in serial que and process if found
     command = Serial.read();
     switch (command){
     // Command "T" is for setting the date of DS1307 RTC
     case 'T':
             setDateTimeDS1307();
             //sprintf(comString,"T");
             break;

     // Command "W" is used for toggling the SD Card Write flag. Not used in coYaght
     // so it is commented out
     //case 'W':
            //Toggle write to SD card flag. When is on data are not written to the SD card 
            // Default is on
            //Serial.readBytesUntil(LINE_FEED, charread,1);
            //if (charread[0]=='1') writetosd = true;
            //else writetosd = false;
            //digitalWrite(POWER_LED, LOW);
            //sprintf(comString,"W");
            //break;
     
     // Command "m" is used for controlling the motors
     case 'm':
            movemotors();
            break;

     // Command "R" is used for resetting the Arduino
     case 'R':
            resetFunc(); //call reset 
            break;

     // Command "B" is used to alter the battery divider
     case 'B':
            // Change battery (change voltage divider)
            // Supported batteries (12V and 9V). Default is 9V
            Serial.readBytesUntil(LINE_FEED, charread,1);
            if (charread[0]=='1') bat_type = 1;              
            else bat_type = 0;               
             
            //sprintf(comString,"B");
            break;

     // Command "N" is used to toggle numeric output.
     case 'N':
            // Toggle number mode
            // When is on the program sends only the values of the sensors and thus communication is faster 
            // Default is off
            Serial.readBytesUntil(LINE_FEED, charread,1);
            if (charread[0]=='1') numbermode = true;
            else numbermode = false;
            //sprintf(comString,"N");
            break;        

     // Command "S" is used to Start/Stop serial recording of measuremens
     case 'S':
            //Toggle serial port writing
            Serial.readBytesUntil(LINE_FEED, charread, 1);
            if (charread[0]=='1') serwrite = true;
            else serwrite = false;
            break;

     // Command "D" is used to read the Date and Time from RTC
     // This command works only when the serial port is not used for sending
     // measurements. When the serial port is started by using command "S1" then
     // "D" command is ignored in order not to spoil the measurement lines being
     // printed
     case 'D':
            Serial.readBytesUntil(LINE_FEED, charread, 1);
            if(!serwrite) {
              getDateTimeDS1307();
              sprintf(printString, "20%02d-%02d-%02d %02d:%02d:%02d\r\n", year, month, dayOfMonth, hour, minute, second);
              Serial.print(printString);
            }
            break;
     }

     
     //Serial.print("Command: ");
     //Echo command
     //Serial.println(comString);
     //sprintf(comString,"invalid");
  }
  command = 0; // reset command 
     
  
 //sample data from the sensors and get time from RTC
 if (domeasure){ 
     // check battery state       
     measureBATT();

     // Get time and date
     getDateTimeDS1307();
     
     // Take Sensor Measurements
     measurePressure();
     measureTemperature();
     measureLight();
     calculateDepth(); 

     // Write and Print Information
     // Blink power LED to notify user data are written to SD card
     //digitalWrite(POWER_LED, HIGH);
     //WriteDataToCard();
     if(serwrite)
        SendDataToSerial(); 
     //digitalWrite(POWER_LED, LOW);
        
     //Ok, data where taken
     domeasure = false;
     resetcounter = true;    
  }    
 // delay
 wait(READ_SENSORS_DELAY);
}
