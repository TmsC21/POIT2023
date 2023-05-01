import serial
import time
import json

ser=serial.Serial("/dev/ttyACM0",9600)
ser.baudrate=9600
while True:
	arr = ser.readline().strip().decode( "utf-8" ).split("|", 2)
	if float(arr[2]) < 50:
		print("Temp:"+arr[0]+" Him:"+arr[1]+" Dist:"+arr[2])
