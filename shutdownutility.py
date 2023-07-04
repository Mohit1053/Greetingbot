import RPi.GPIO as GPIO
import os
#pin 17 is used
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
while(1):
	state = GPIO.input(17)  #if state is low
	if not state:
		print("Shutting down")
		os.system("sudo shutdown now")
