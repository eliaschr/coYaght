//
//  Light Sensor
//  ------------------------------------------------------------
ISR(TIMER1_OVF_vect)
{
  // Capture Timer1 overflow (if any)
  cnt_pul_ovs++;
}

void wait(unsigned long interval)
{
  if (resetcounter){
      bitSet(TIMSK1,TOIE1);  // Enable timer1 overflow interrupt
  
      // save the last time
      previousMillis = millis();
      TCNT1 = 0; // reset the hardware counter
      resetcounter = false;
      cnt_pul_ovs = 0;
  }   
  
  if(millis() - previousMillis > interval) {
    //We measure the pulses form lux sensor and total millisecons elapsed
    diffMillis = millis() - previousMillis;
    // stop the counting 
    bitClear(TIMSK1,TOIE1);  // disable timer1 overflow interrupt
    cnt_pul_lux = (unsigned long)(cnt_pul_ovs*65536) + TCNT1;
    // after the delay we can sample all the sensors
    domeasure=true;
  }
}

float calc_uwatt_cm2(unsigned long freq)  {
  // Calculate Irradiance from the diagram
  // Use the sensitivity_factor. It is calculated from the diagram (for 640nm wavelength)
  float uw_cm2 = (float) freq / (float) TSL_CONVERT_FACTOR;
  //uw_cm2 *= ((float) 1 / (float) 0.0136);
  return (uw_cm2);
}


float calc_lux_single(float uw_cm2, float efficiency)  {
  // calculate lux (lm/m^2), using standard formula:
  // Xv = Xl * V(l) * Km
  // Xl is W/m^2 (calculate actual receied uW/cm^2, extrapolate from sensor size (0.0136cm^2)
  // to whole cm size, then convert uW to W)
  // V(l) = efficiency function (provided via argument)
  // Km = constant, lm/W @ 555nm = 683 (555nm has efficiency function of nearly 1.0)
  //
  // Only a single wavelength is calculated - you'd better make sure that your
  // source is of a single wavelength...  Otherwise, you should be using
  // calc_lux_gauss() for multiple wavelengths
  float w_m2 = (uw_cm2 / (float) 100);  // convert to uW/cm^2 to W/m^2
  float lux = w_m2 * efficiency * (float) 683;
  return (lux);
}
  
