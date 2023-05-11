import boto3
import json
import os
import pandas as pd

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

#In AWS, a sqs message is triggered upon an csv upload to a specific bucket
#This loop waits for a message to be recieved, and once its recieved will download the file that triggered the message
#and will run the gps visualizer.

try:
	sqs.purge_queue(QueueUrl=os.environ.get('queueURL'))
except:
	pass

print('Waiting For Upload...')

while True:
	res = sqs.receive_message(
	QueueUrl=os.environ.get('queueURL'),
	WaitTimeSeconds=20,
	)

	if 'Messages' in res:
		body = json.loads(res['Messages'][0]['Body'])
		bucket = body['Records'][0]['s3']['bucket']['name']
		key = body['Records'][0]['s3']['object']['key']

		s3.download_file(bucket, key, rf'/home/ubuntu/s3files/{key}')

		df = pd.read_csv(rf"/home/ubuntu/s3files/{key}", usecols=[0,1,6]) #Remove Columns not needed from csv
		df.to_csv(rf"/home/ubuntu/s3files/{key}", index=False)
		
		print(f"FILE '{key}' HAS BEEN DOWNLOADED")

		os.system(rf'sudo python3 /home/ubuntu/mapvis/main.py /home/ubuntu/s3files/{key}') #Begin running gps visualization script from downloaded csv sheet
		os.system(rf'sudo rm -f /home/ubuntu/s3files/{key}')

		sqs.delete_message(QueueUrl=vars[2], ReceiptHandle=res['Messages'][0]['ReceiptHandle']) #Delete message when done

