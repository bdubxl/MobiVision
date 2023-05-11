import boto3
import os

def start_ec2(): #Start stage 2 and stage 4 EC2 VM's for processing after intital data has been captured
	ec2 = boto3.client(
		'ec2',
		region_name='us-east-1',
		)

	ec2.start_instances(
		InstanceIds=[os.environ.get('instanceid1'), os.environ.get('instanceid2')], 
		)

def export_file(filename): #Send csv and mp4 to stage 2 bucket
	s3 = boto3.client('s3')
	s3.upload_file(filename, os.environ.get('stage2bucket'), filename.split('/')[-1])
