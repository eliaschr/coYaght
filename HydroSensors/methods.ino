#define BAT_MULTIPLIER_9V 2.00
#define BAT_MULTIPLIER_12V 2.95

void rightmotor(int dir)
{
 //make sure NEVER set both pins to high, or the h-brige will shortcircuit
 if (dir==1){
     digitalWrite(MR1, HIGH);
     digitalWrite(MR2, LOW);
     digitalWrite(MR_SD, HIGH); 
 }else if (dir==-1){
     digitalWrite(MR1, LOW);
     digitalWrite(MR2, HIGH);
     digitalWrite(MR_SD, HIGH); 
 }else{
    digitalWrite(MR1, LOW);
    digitalWrite(MR2, LOW); 
    digitalWrite(MR_SD, LOW); 
 }  
}

void leftmotor(int dir)
{
 //make sure NEVER set both pins to high, or the h-brige will shortcircuit
 if (dir==1){
     digitalWrite(ML1, HIGH);
     digitalWrite(ML2, LOW);
     digitalWrite(ML_SD, HIGH); 
 }else if (dir==-1){
     digitalWrite(ML1, LOW);
     digitalWrite(ML2, HIGH);
     digitalWrite(ML_SD, HIGH); 
 }else{
    digitalWrite(ML1, LOW);
    digitalWrite(ML2, LOW); 
    digitalWrite(MR_SD, LOW); 
 }  
}

void depthmotor(int dir)
{
 //make sure NEVER set both pins to high, or the h-brige will shortcircuit
 if (dir==1){
     digitalWrite(MD1, HIGH);
     digitalWrite(MD2, LOW);
     digitalWrite(MD_SD, HIGH); 
 }else if (dir==-1){
     digitalWrite(MD1, LOW);
     digitalWrite(MD2, HIGH);
     digitalWrite(MD_SD, HIGH); 
 }else{
    digitalWrite(MD1, LOW);
    digitalWrite(MD2, LOW); 
    digitalWrite(MD_SD, LOW); 
 }  
}

void movemotors(){  
  char charread[2];
  boolean both_motors = false; 
  Serial.readBytesUntil(LINE_FEED, charread,2);
  
  switch (charread[0]){
  case 'm':switch (charread[1]){
           case 'f': rightmotor(1);
                     leftmotor(1);
                     //sprintf(comString,"mmf");
                     break;
           case 'b': rightmotor(-1);
                     leftmotor(-1);                    
                     //sprintf(comString,"mmb");
                     break;   
           case 'l': rightmotor(1);
                     leftmotor(-1);                    
                     //sprintf(comString,"mml");
                     break;  
           case 'r': rightmotor(-1);
                     leftmotor(1);                    
                     //sprintf(comString,"mmr");
                     break;    
           case 's': rightmotor(0);
                     leftmotor(0);                    
                     //sprintf(comString,"mms");
                     break;                      
           }       
          break;
  case 'r':switch (charread[1]){
           case 'f': rightmotor(1);
                     //sprintf(comString,"mrf");
                     break;
           case 'b': rightmotor(-1);
                     //sprintf(comString,"mrb");
                     break;
           default:  rightmotor(0); 
                     //sprintf(comString,"mr");
                     break;        
           }
           break;
  case 'l':switch (charread[1]){
           case 'f': leftmotor(1);
                     //sprintf(comString,"mlf");
                     break;
           case 'b': leftmotor(-1);
                     //sprintf(comString,"mlb");
                     break;
           default:  leftmotor(0);
                     //sprintf(comString,"ml"); 
                     break;        
           }
           break;
  case 'd':switch (charread[1]){
           case 'u': depthmotor(1);
                     //sprintf(comString,"mdu");
                     break;
           case 'd': depthmotor(-1);
                     //sprintf(comString,"mdd");
                     break;
           default:  depthmotor(0);
                     //sprintf(comString,"md"); 
                     break;        
           }  
           break;
  case 's':rightmotor(0);
           leftmotor(0);
           depthmotor(0);   
           //sprintf(comString,"ms"); 
           break;           
  }  
}

void measureLight()
{
  //calculate freqcuence from the number of pulses (frequncy in Hz)
  unsigned long frequency=((unsigned long)cnt_pul_lux*1000)/diffMillis; //scaling is set default to x1
 
  float uw_cm2 = calc_uwatt_cm2(frequency);  //calculate radiant energy
  light = calc_lux_single(uw_cm2, 0.175);  // calculate illuminance for 670nm light (0.175 from table)
  light_overflow = (light-(int)light) * 100;
}

void measurePressure()
{
  //analogRead(aPressure);
  int pValue = analogRead(aPressure); // value from 0 to 1023 
  double pVolt =(double)pValue*(5.0/1023.0);  // 1024 values correspond to 5 volts
  pressure = 50*pVolt+10; //conversion from material data sheet
  pressure_overflow = (pressure - (int)pressure) * 100;
  
}

void measureTemperature()
{
  // Temperature sensor LM35 10mV/oC
  // set analog refernce voltage to 1.1V for more accurancy
  //analogReference(INTERNAL);
  analogRead(aTemperature);
  int tValue =  analogRead(aTemperature); //Keep the second measurement
  double tVolt =(double)tValue/204.8;  // 1024 values correspond to 5 volts
  temp = (tVolt*100); // 10 mV / C
  temp_overflow = (temp-(int)temp)*100;
  //analogReference(DEFAULT);
}

void measureBATT()
{
  analogRead(aBatt);
  int tValue = analogRead(aBatt); // value from 0 to 1024 
  double tVolt =(double)tValue/204.8;  //1024 values correspond to 5 volts
  switch (bat_type){
  case 0:batt = tVolt*BAT_MULTIPLIER_9V; // Battery voltage is divided by a factor 2
         break;
  case 1:batt = tVolt*BAT_MULTIPLIER_12V; // Battery voltage is divided by a factor 2,93
         break;   
  }
  batt_overflow = (batt-(int)batt) * 100;
}

void calculateDepth()
{
  //depth in meters
  // p = rho*g*h
 float density = 1025; //kg/m^3  1000kg m/s^2
 depth = (pressure - pressure0)*1000/(9.806*density);
 depth_overflow = (depth - (int)depth) * 1000; 

 if(depth < 0)
 {
   depth_overflow = 0;
 }
 
}

void zeroPressureSensor()
{
  
  float pSum = 0;
  for( int x = 0; x < 10; x++)
  {
    measurePressure();
    pSum = pSum + pressure;
    delay(500);
  }
  pressure0 = pSum/10;
}

 
//void WriteDataToCard()
//{
//  if (writetosd){
//    sprintf(printString, "%02d/%02d/20%02d , %02d:%02d:%02d , %d.%02d , %d.%02d , %d.%03d , %d.%02d", dayOfMonth, month, year,hour, minute, second,(int)temp, temp_overflow, (int)pressure, pressure_overflow, (int)depth, depth_overflow, (int)light, light_overflow);
//    writeToCard(printString);
//  }  
//}

void SendDataToSerial()
{
  if (numbermode){
    Serial.write(255);
    Serial.write(255);
    // Send first date and time
    Serial.write((byte)year);
    Serial.write((byte)month);
    Serial.write((byte)dayOfMonth);
    Serial.write((byte)hour);
    Serial.write((byte)minute);
    Serial.write((byte)second);   
    // Send sensor values
    Serial.write((byte)temp+127);
    Serial.write((byte)temp_overflow); 
    Serial.write((byte)((int)pressure/256));
    Serial.write((byte)((int)pressure%256));
    Serial.write((byte)pressure_overflow); 
    Serial.write((byte)depth);
    Serial.write((byte)((int)depth_overflow/256)); 
    Serial.write((byte)((int)depth_overflow%256)); 
    Serial.write((byte)((int)light/256));
    Serial.write((byte)((int)light%256));
    Serial.write((byte)light_overflow);
    Serial.write((byte)batt);
    Serial.write((byte)batt_overflow);    
  }else{
    sprintf(printString, "Date=20%02d-%02d-%02d %02d:%02d:%02d, Temp=%d.%02d, P=%d.%02d, Depth=%d.%03d, Lux=%d.%02d, Batt=%d.%02d\r\n", year, month, dayOfMonth,hour, minute, second,(int)temp, temp_overflow, (int)pressure, pressure_overflow, (int)depth, depth_overflow, (int)light, light_overflow, (int)batt, batt_overflow);
    Serial.print(printString);
  }   
}

//void writeToCard(char *stringOut)
//{
//  uint8_t n;
//  // Create the file if not exist
//  if (!file.open("DATA.LOG", O_CREAT | O_APPEND | O_WRITE)) {
//      Serial.print("Failed to open file");
//    }
  
//  for (n = 0; stringOut[n]; n++);
//  file.write((uint8_t *)stringOut, n);  
//  if (file.writeError) Serial.println("Write Failed");
//  file.write((uint8_t*)"\r\n", 2);
  
//  if (!file.close()) Serial.println("Close Failed");
//}
