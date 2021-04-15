#!/usr/bin/env python3
'''
Module to handle kikusui PCR 500MA
'''
from sys import stderr
from time import sleep
import sys
import vxi11

WaitTimeStep  = 15.  # Seconds (same as PB2)
WaitTimeForce = 10.
WaitTimeEmerg = 5.
VoltStep   = 1.      # Minimum step sige to change voltage (integer)
VoltLimit  = 51.     # Safety limit for too high voltage
SwitchLimit = 5.     # Safety limit to turn on or off heater

class PCR500MA:
   
   def __init__(self, ipaddr):
      self.instr=0
      self.Voltage=0.
      try:
          #print "try", devname, baudrate
          self.instr=vxi11.Instrument(ipaddr)
          self.getVoltage()
      except:
          print("device not found", tempser)
          #sleep(0.05)

      #self.checkID()

   def __w(self, data):
       self.instr.write(data)

   def __a(self, data):
       return self.instr.ask(data)

   def checkID(self):
       print(self.__a("*IDN?"))
       print("output is ", self.__a("OUTP?"))

   def switchOn(self):
       if(self.Voltage > SwitchLimit):
          print("It is dangerous!")
          return
       self.__w('OUTP 1')

   def switchOff(self):
       if(self.Voltage > SwitchLimit):
          print("It is dangerous!")
          return
       self.instr.__w('OUTP 0')

   def getVoltage(self):
      self.Voltage = float(self.__a('MEAS:VOLT:AC?'))
      return self.Voltage

   def getCurrent(self):
      curr = float(self.__a('MEAS:CURR:AC?'))
      print("curr(peak) =", curr)
      return curr

   def getPower(self):
      power = float(self.__a('MEAS:POW:AC?'))
      print("power =", power)
      return power

   def setVoltage(self,volt):
      if(self.Voltage-volt > SwitchLimit or volt-self.Voltage > SwitchLimit):
          print("It is dangerous!")
          return
      self.Voltage = volt
      print("set ", self.Voltage)
      self.__w('SOUR:VOLT '+str(volt))

