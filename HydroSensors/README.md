# DeepSeaRobotix - coYaght
---

![coYaght Image](../images/sensors.jpg)

## Arduino Subsystem

The Raspberry Pi of the coYaght is connected with an Arduino Uno subsystem. Its purpose is to observe the values of some sensors and control three motors for coYaght navigation in the sea. The code is based on [EUGENIDES FOUNDATION](http://www.eugenfound.edu.gr) code, part of the program [hydrobots](http://www.hydrobots.gr). The program is modified according to the needs of coYaght.

Arduino runs the code that is consisted of four files:

* [_hydrosensor\_shield.ino_](hydrosensor_shield.ino): Is the main program that initializes the system and keeps tracking of the serial communications.

* [_clock.ino_](clock.ino): Is a library of necessary functions to handle the real time clock DS1307
* [_light.ino_](light.ino): Is a library of functions to handle the light sensor.
* [_methods.ino_](methods.ino): Is a library of functions to handle the motors, make measurements and send a complete line of them through the serial port.

### [_hydrosensor\_shield.ino_](hydrosensor_shield.ino)

The main program and entry point. Contains the _setup()_ and _loop()_ functions.

*	_setup()_ is responsible for initializing the serial port as UART at 9600 bps, the I/O pins, the timer that will be used for the timing functions and the initialization of the sensors. This is the place that some normalization of the sensors takes place. This takes time and the system cannot accept any commands during that time. When it starts and when it ends, it sends appropriate messages to the serial port. So the server knows when the initialization mode runs.
*	_loop()_: is the main part. It is the process that never ends. It checks for incoming commands from the serial port and acts depending on them. For most of the commands it dispatches to other functions that execute the necessary steps to complete the actions needed. When it is time and if the measurements are enabled, the system takes measurements of all the sensors and sends the results to the serial port. The commands the system accepts are:

	* _T_: Sets the Date and Time of the RTC chip, DS1307.
	* _m_: It is the starting letter of a movement command. The commands that start with _m_ activate or deactivate one or more motors.
	* _R_: Resets the Arduino's processor. Everything starts from the beginning.
	* _B_: Sets the battery type used to power the system. The type of the battery is set by the following digit. By default a 12V battery is considered to power coYaght. The possible settings are:
		* _B0_: A 9V battery is used (normally the second character can be anything other than _1_).
		* _B1_: A 12V battery is used.
	* _N_: Toggles number mode. There are two modes of output. One is the **String Mode** where the system outputs a whole string of data with labels and values as text and the **Number Mode** where the measurements are being sent as bytes. On boot the system is set to String Mode. The two settings are:
		* _N0_: String Mode is used (normally the second character can be anything other than _1_).
		* _N1_: Number Mode is used
	* _S_: Toggles the measurement making. Every time the system takes one packet of measurements, it sends them to the serial port. Using this command set the user can start or stop the measurement process. By default, on boot, the system does not make measurements until it is commanded to. The two settings are:
		* _S0_: Stop making measurements (normally the second character can be anything other than _1_).
		* _S1_: Starts making measurements.
	* _D_: Return the Date / Time of the RTC chip. It is always followed by another character. So the command is like _D?_, where **?** expresses any character. The Date / Time string is returned in the form **YYYY-MM-DD HH:mm:dd**, where _YYYY_ is the full year, _MM_ is the month as a two digit number (01 to 12), _DD_ is the day of month as a two digit number (1 to 31), _HH_ is the hour as a two digit number (00 to 23), _mm_ is the minutes as a two digit number (00 to 59) and _ss_ is the seconds as a two digit number (00 to 59).

	
### [_clock.ino_](clock.ino)

A library of functions to handle the Real Time Clock DS1307. The defined functions are:

* decToBcd(val): Takes a value of byte in parameter _val_ and converts it to a BCD one. This is necessary because DS1307 uses BCD numbers for the timekeeping counters.
* bcdToDec(val): Takes a value of a BCD number on parameter _val_ and converts it to a byte.
* setDateTimeDS1307(): It is used to tak ethe rest of the input of the 'T' command from the serial port and set the registers of the DS1307 according to those settings. More specifically, reads 17 characters from the serial input and uses:
	* First two characters as the day number
	* 4th and 5th characters are used for the month number
	* 7th and 8th characters to define the year number (only the two last digits)
	* 10th and 11th characters define the hours
	* 13th and 14th characters define the minutes
	* 16th and 17th characters define the seconds
	* the rest of the characters (3rd, 6th, 9th, 12th and 15th) are ignored
* getDateTimeDS1307(): Sets the global variables _second_, _minute_, _hour_, _dayOfWeek_, _dayOfMonth_, _month_ and _year_ with the values read from DS1307, as binary values (not BCD)


### [_light.ino_](light.ino)

A library for handling the light sensor of the system. The overflow vector of Timer 1 is hooked. Every time there is and overflow this interrupt vector is triggered and increases a counter which is used for the rest of the converting process. The defined functions are:

* wait(interval): It waits for an _interval_ time in **ms**.
* calc_uwatt_cm2(freq): Converts the frequency _freq_ of the sensor pulses measured to μWatts/cm^2
* cals_lux_single(uc\_cm2, efficiensy): Converts the μWatts/cm^2 _uc\_cm2_ to **Lux** taking account of the _efficiensy_.


### [_methods.ino_](methods.ino)

Defines functions for controlling the motors of the coYaght, the functions to measure the system's parameters, the zeroing of the pressure sensor and the sending of data to the serial port. A list of those functions follow:

* rightmotor(dir): Sets the values of the associated to the right motor digital I/O pins according to the _dir_ parameter. If _dir_ is 0 the right motor is stopped, if it is 1 moves the right motor forward and if it is -1 it moves the right motor backwards.
* leftmotor(dir): Sets the values of the associated to the left motor digital I/O pins according to the _dir_ parameter. If _dir_ is 0 the left motor is stopped, if it is 1 moves the left motor forward and if it is -1 it moves the left motor backwards.
* depthmotor(dir): Sets the values of the associated to the depth motor digital I/O pins according to the _dir_ parameter. If _dir_ is 0 the depth motor is stopped, if it is 1 moves the depth motor forward and if it is -1 it moves the depth motor backwards.
* movemotors(): It is called when a _m_ command is issued through the serial port. It checks the 2nd and 3rd characters of the input and activates or deactivated the necessary motors to execute the issued navigation movement. The commands that are accepted are:
	* _mmf_: Move forward by activating both left and right motors forward
	* _mmb_: Move backwards by activating both left and right motors backwards
	* _mml_: Rotate counter clockwise by activating the right motor forward and the left motor backwards
	* _mmr_: Rotate clockwise by activating the right motor backwards and the left motor forward
	* _mms_: Stop both right and left motors (stops the horizontal only movement)
	* _mrf_: Activate the right motor forward
	* _mrb_: Activate the right motor backwards
	* _mr?_: Deactivate the right motor (? expresses any character different than _f_ and _b_)
	* _mlf_: Activate the left motor forward
	* _mlb_: Activate the left motor backwards
	* _ml?_: Deactivate the left motor (? expresses any character different than _f_ and _b_)
	* _mdu_: Activate the diving motor for Ascending to surface
	* _mdd_: Activate the diving motor for Diving
	* _md?_: Deactivate the diving motor (? expresses any character different than _d_ and _u_)
	* _ms_: Deactivates all three motors
* measureLight(): Makes a light measurement and stores the value in _light_ and _light\_overflow_ variables
* measurePressure(): Makes a pressure measurement and stores its value in _pressure_ and _pressure\_overflow_ variables
* measureTemperature(): Makes a temperature measurement and stores its value in _temp_ and _temp\_overflow_ variables
* measureBatt(): Makes a battery voltage measurement and stores its value in _batt_ and _batt\_overflow_ variables
* calculateDepth(): Calculates the depth according to the pressure measurement. The result is stored in _delth_ and _depth\_overflow_ variables.
* zeroPressureSensor(): It measures the pressure at the surface of the sea. It is assumed that when the system is powered on it is at depth 0 (surface of the sea, or out in the air near the sea level). The zeroing of the pressure sensor is made only once upon initialization of the system.
* SendDataToSerial(): Formats the data measured according to the Number Mode and sends the result to the serial port.

