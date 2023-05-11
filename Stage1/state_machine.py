import RPi.GPIO as GPIO

"""
Breadboard is attatched to phsycial device with LED's used to determine where
in the code its currently running. For automation pruposes it's essential to 
make use of a state machine to be able to determine if the device is operating
correctly.
"""
#Configuring GPIO ports for LED activation
red = 18
green = 23
yellow = 24
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(red, GPIO.OUT)
GPIO.setup(green, GPIO.OUT)
GPIO.setup(yellow, GPIO.OUT)

leds = (red,green,yellow)

def green_on():
	GPIO.output(green, GPIO.HIGH)
def yellow_on():
	GPIO.output(yellow, GPIO.HIGH)
def red_on():
	GPIO.output(red, GPIO.HIGH)

def state_machine_set(state):
	GPIO.output(leds, GPIO.LOW)
	if state == 'starting':
		green_on()
		yellow_on()
		red_on()
	elif state == 'running':
		green_on()
	elif state == 'waiting':
		yellow_on()
	elif state == 'error':
		red_on()
	elif state == 'uploading':
		green_on()
		yellow_on()
	elif state == 'testing':
		green_on()
		red_on()
	elif state == 'waitingmove':
		red_on()
		yellow_on()



