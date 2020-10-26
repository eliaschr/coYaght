// Convert normal decimal numbers to binary coded decimal
byte decToBcd(byte val){
  return ( (val/10*16) + (val%10) );
}

// Convert binary coded decimal to normal decimal numbers
byte bcdToDec(byte val){
  return ( (val/16*10) + (val%16) );
}


// Sets the date and time from the ds1307
void setDateTimeDS1307(){

   
   char charread[17];
   Serial.readBytesUntil(LINE_FEED, charread,17);

   dayOfMonth = (byte) ((charread[0] - 48)*10 + (charread[1] - 48));  // Use of (byte) type casting and ascii math to achieve result.
   month = (byte) ((charread[3] - 48)*10 + (charread[4] - 48));  // Use of (byte) type casting and ascii math to achieve result.
   year = (byte) ((charread[6] - 48)*10 + (charread[7] - 48));  // Use of (byte) type casting and ascii math to achieve result.
   

   hour = (byte) ((charread[9] - 48)*10 + (charread[10] - 48));  // Use of (byte) type casting and ascii math to achieve result.
   minute = (byte) ((charread[12] - 48)*10 + (charread[13] - 48));  // Use of (byte) type casting and ascii math to achieve result.
   second = (byte) ((charread[15] - 48)*10 + (charread[16] - 48));  // Use of (byte) type casting and ascii math to achieve result.  
    
    
   Wire.beginTransmission(DS1307_I2C_ADDRESS);
   Wire.write(0x00);
   Wire.write(decToBcd(second));    // 0 to bit 7 starts the clock
   Wire.write(decToBcd(minute));
   Wire.write(decToBcd(hour));      // If you want 12 hour am/pm you need to set
                                   // bit 6 (also need to change readDateDs1307)
   Wire.write(decToBcd(dayOfWeek));
   Wire.write(decToBcd(dayOfMonth));
   Wire.write(decToBcd(month));
   Wire.write(decToBcd(year));
   Wire.endTransmission();

}

// Gets the date and time from the ds1307
void getDateTimeDS1307(){
  // Reset the register pointer
  Wire.beginTransmission(DS1307_I2C_ADDRESS);
  Wire.write(0x00);
  Wire.endTransmission();

  Wire.requestFrom(DS1307_I2C_ADDRESS, 7);

  // A few of these need masks because certain bits are control bits
  second     = bcdToDec(Wire.read() & 0x7f);
  minute     = bcdToDec(Wire.read());
  hour       = bcdToDec(Wire.read() & 0x3f);  // Need to change this if 12 hour am/pm
  dayOfWeek  = bcdToDec(Wire.read());
  dayOfMonth = bcdToDec(Wire.read());
  month      = bcdToDec(Wire.read());
  year       = bcdToDec(Wire.read());
 
}
