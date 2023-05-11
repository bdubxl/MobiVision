import os
import csv
import boto3
import json

sqs = boto3.client(
	'sqs',
	region_name='us-east-1',
	aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
	aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
	)

s3 = boto3.client(
	's3',
	aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
	)

#Purge queue for floating messages
try:
	sqs.purge_queue(QueueUrl=os.environ.get('QueueURL'))
except:
	pass

print('Waiting For Upload...')

while True:
	res = sqs.receive_message(
	QueueUrl=os.environ.get('queueURL'),
	WaitTimeSeconds=20,
	)
	#Poll from queue until message appears, message will have informtaion regarding files that created the event
	if 'Messages' in res:
		body = json.loads(res['Messages'][0]['Body'])
		bucket = body['Records'][0]['s3']['bucket']['name']
		key = body['Records'][0]['s3']['object']['key']
		mp4key = f"{key.split('.')[0]}.mp4"
		txtkey = f"{key.split('.')[0]}.txt"
		s3.download_file(bucket, key, fr'/home/ubuntu/OD/s3files/{key}')

		s3.download_file(bucket, f'{mp4key}', fr'/home/ubuntu/OD/s3files/{mp4key}')
		print(f"FILES '{key}' AND '{mp4key}' HAVE BEEN DOWNLOADED, STARTING OBJECT DETECTION")
		
		#Detect stop signs from downloaded video, redirect output to txt file
		os.system(rf"sudo python3 ~/OD/yolov5/detect.py --weights ~/OD/yolov5/runs/train/exp3/weights/best.pt --source ~/OD/s3files/{mp4key} --conf-thres 0.95 --vid-stride 10 >> ~/OD/DATA/results/{txtkey} 2>&1")

		sqs.delete_message(QueueUrl=os.environ.get('queueURL'), ReceiptHandle=res['Messages'][0]['ReceiptHandle']) #Delete message when done
		print("OBJECT DETECTION COMPLETE, STARTING STAGE 2 CSV WRITING")


		os.system(f'sudo rm -f ~/OD/s3files/{mp4key}')

		#Open txt file produced by object detection script and get times where stop signs were detected.
		with open(fr'/home/ubuntu/OD/DATA/results/{txtkey}', 'r', newline='') as file:
			lines = file.readlines()
			stop_sign = 0
			no_stop = 0
			global stoptimes
			stoptimes = []	# List which stores times where the stop times were detected
			# If 4 stop sign frames occur before 4 frames of no detections, append time to stoptimes.
			for line in lines:
				stop = line.find('stop') 
				if stop != -1: #If current line has "stop" in it
					stop_sign += 1
					if stop_sign == 1:
						no_stop = 0
					if stop_sign == 4:
						x = line.split('(') # Removing line formatting to get frame integer
						y = x[1].split('/')
						s = int(y[0]) / 3 # Divide current frame by 3 to get time in seconds (30fps camera at 10x the speed)
						stoptimes.append(s) # Append time to stoptimes
				else: #If 4 frames of no detections occur before 4 frames with stop sign, filter these out
					no_stop += 1
					if no_stop == 4:
						stop_sign = 0
						no_stop = 0
		
		"""
		Once stop signs times are all appended to 'stoptimes', check speeds in csv between last 2 
		and future 6 seconds of stop time to see if speed was ever under 1.5mph. If speed was under, 
		then you stopped and no flags will be added. Otherwise add 'Ran Stop Sign' flag.
		"""
		csv = open(rf'/home/ubuntu/OD/s3files/{key}', 'r', newline='')
		csv_lines = csv.readlines()
		newlines = []
		speeds = []
		count = 0
		for i, line in enumerate(csv_lines):
			speeds.clear()
			splt = line.split(',')
			try:
				if splt[5] == str(int(stoptimes[count])): #If time in csv == time that stop sign was deteced
					for j in range(i-2, i+6): #Add last 2 seconds and future 8 seconds speeds into 'speeds' list
						speeds.append(csv_lines[j].split(',')[2])
					count += 1 #stoptimes index increment
					if float(min(speeds)) > 1.5: #If lowest speed was above 1.5mph, then add flag
						splt[6] = 'Ran Stop Sign\n'
						line = ','.join(splt)
						newlines.append(line)
				else:
					newlines.append(line)
			except:
				newlines.append(line)


		#Send new csv with stop sign flags added over to stage 3
		final_write = open(fr'/home/ubuntu/OD/s3files/{key}', 'w') #Final file retianes original name which acts as a uuid
		final_write.writelines(newlines)
		final_write.close()
		path = rf'/home/ubuntu/OD/s3files/{key}'
		#final_csv = open(path, 'r', newline='') 
		s3.upload_file(f'/home/ubuntu/OD/s3files/{key}', os.environ.get('stage3bucket'), f'{key}')
		os.system(r'sudo rm -rf ~/OD/yolov5/runs/detect/*')

		print('STAGE 2 CSV COMPLETE UPLOADED TO STAGE3 TO BEGIN SPEED DETECTIONS')
