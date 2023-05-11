import serial
import csv
import pynmea2
from datetime import datetime
import board
import busio
import adafruit_adxl34x
import time
import os
import state_machine as sm
import requests
import start_instances as si

gps = serial.Serial('/dev/ttyACM0') #GPS module device file path
i2c = busio.I2C(board.SCL, board.SDA) #Acceleromter i2c port read
x = adafruit_adxl34x.ADXL345(i2c) #Read/Format incoming data from i2c

#Main function running on the physical device logs all data from trip into one csv sheet. Once trip is finished, csv will be sent to aws infrastructure
def start_trip():
	sm.state_machine_set('testing') #Change state to testing
	
	#Attempt start up of necessary EC2's from AWS infrastructure for post processing
	#If service is not available to do so, trip will still be logged into csv but
	#it's possible when the trip is over data will not be sent over.
	try:
		si.start_ec2()
	except:
		print('no internet')
		sm.state_machine_set('error')
		time.sleep(5)

	sm.state_machine_set('starting')
	now = datetime.now()

	#date variable serves as a uuid for every trip, no two trips will have the same date and time,
	#making it easy to identify exactly which trip is being reffered too in later processing.
	date = now.strftime("%m-%d-%Y_%Hh%Mm%Ss")

	#Creeate directory to log csv and mp4 files in
	os.system(f"sudo mkdir /home/mykesb/ACC/tripsdata/{date}")

	#Time tracker of running loop below
	programtime = 0

	datefile = f"/home/mykesb/ACC/tripsdata/{date}/{date}.csv"
	mp4file = f"/home/mykesb/ACC/tripsdata/{date}/{date}.mp4"

	#List are used to keep track of data between previous loop iteration and current iteration
	#Use of these list is in the main loop below
	speed_table = [0,10] #Because trip start once you've reached 10mph, its important for the head of the list to be same.
	not_moving = []
	acc_table = [0,0]

	#Start recording video
	os.system(f'ffmpeg -f v4l2 -video_size 640x480 -i /dev/video0 -pix_fmt yuv420p {mp4file} &')
	
	#2 second wait put on main loop for data to be in synch with video being recorded
	time.sleep(2)
	
	with open (datefile, 'w+', newline='') as file:
		writer = csv.writer(file)
		#Main loop will loop every second and record important data to be added to csv
		while True:
			#If GPS service isnt available, try except handler is used to prevent program from dying when data can be retrieved
			try:
				line = gps.readline() #Read data from GPS device file
				data = line.split(b',') #Delimit data by commas as this is how the data is separated in NMEA formatting
				
				if data[0] == b"$GNRMC": # GNRMC data is what we need for relevant geographic positional data, ignore other besides this
					sm.state_machine_set('running')
					nmea = pynmea2.parse(line.decode('utf-8'))
					
					#Retrieve Latitiude, Longitude, and Speed and store them in variables
					lat = float(round(nmea.latitude, 6))
					lon = float(round(nmea.longitude, 6))
					vel = round(float(nmea.spd_over_grnd) * 1.151, 1) #Speed comes in knots, converted to mph

					acc = x.acceleration #Retrieve accelerometer data 

					flag = '*' #Default character used for flags when no flags are present

					#Logic behind list that were created outside of running loop to record data from previous to current second
					speed_table.append(vel)  #Append current speed
					del speed_table[0] #remove previous speed

					acc_table.append(acc[1]) #Append current y-axis acceleration
					del acc_table[0] #remove previous y-axis acceleration

					#Speeding has the highest priority among all flags currently being recorded and
					#therefor all other flags will be ignored if driver is above 70mph.
					#Speeds above 70mph will automatically trigger a speeding flag while speeds under 65mph 
					#will be checked for in post processing (Stage 3) of current data.
					if vel > 70: 
						flag = 'Speeding'

					if flag == 'Speeding':
						pass
					else: 
						#Reads list for previous speed and current speed. If speed has increased or decreased more then 6mph
						#in one second, appropriate flag will be added. 
						if (float(speed_table[1]) - float(speed_table[0])) > 6:
							flag = "Hard Acceleration"
						elif (float(speed_table[0]) - float(speed_table[1])) > 6:
							flag = "Hard Breaking"
						#'Hard Cornering' flag takes average of previous second and current second to filter out possible
						#random spikes on the y-axis
						elif (acc_table[0] + acc_table[1])/2 > 3:
							flag = "Hard Cornering"
							
					#print statement used for real time debugging of device
					print(f"Lat: {lat}, Lon: {lon}, Speed: {vel}, xAcc: {acc[0]}, yAcc: {acc[1]}, Time: {programtime}, Flag: {flag}")

					#Write all recorded variables into current csv row, this row will represent the current second of the trip
					writer.writerow([lat, lon, vel, round(acc[0], 3), round(acc[1], 3), programtime, flag])
					
					#Loop will run everysecond to keep track of time on the current trip
					time.sleep(1)
					programtime += 1 #Add 1 second to current time

					# If speed is under 8mph, length of not_moving list will be increased.
					# If the length of the not_moving is greater or equal to 60, trip will be ended
					# due to lack of movement for over a minute and data will be sent to cloud.
					# If speed does reach over 8mph, restart the not_moving counter to prevent trip from ending
					if len(not_moving) >= 60:
						break
					elif vel < 8:
						not_moving.append(vel)
					elif vel > 8:
						not_moving.clear()
			except: #If at anytime the GPS is not getting sattelight service, catch the error and simply wait for data instead of ending trip
				sm.state_machine_set('waiting')
				print(f'Waiting For Data... ')
				programtime += 1 # Time will stillbe trakced in the event that gps data was mising

	# End process running video recording
	os.system('sudo pkill ffmpeg')

	#Attempt to upload csv and mp4 file to stage 2 (AWS cloud infrastructure)
	try:
		sm.state_machine_set('uploading')
		si.export_file(mp4file)
		si.export_file(datefile)
	except:
		sm.state_machine_set('error')
		time.sleep(5)
		print('no internet')

		
#Before main function gets excecuted, make sure the device has internet service to be able to upload data to the cloud
while True:
	try: # If internet is available, begin loop to start Stage 1
		requests.get("https://www.google.com")
		print("Internet Service is Available")
		break
	except: # Else, wait for internet to become available
		sm.state_machine_set('error')
		print("No Internet Service")
		time.sleep(5)

#A trip will not star being recorded until your speed has surpassed 10mph, once threshold has been reached the main function will be called
while True:
	try:
		line = gps.readline()
		data = line.split(b',')

		if data[0] == b"$GNRMC": #Read GPS data for speed
			nmea = pynmea2.parse(line.decode('utf-8'))
			vel = round(float(nmea.spd_over_grnd) * 1.151, 1)
			if vel < 10:
				sm.state_machine_set('waitingmove')
				print(f'waiting for speed over 10mph. Current Speed {vel}')
			else: # Once speed has reached 10mph, main loop will begin and data will start being tracked into csv
				start_trip()
			time.sleep(1)

	except: # If GPS service not available, wait for service
		sm.state_machine_set('waiting')
		print('waiting')
		time.sleep(1)
