import boto3
import json

#Runs in background waiting for new gps visualizations to be dropped in stage 4 bucket (.png event notification)

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
                print(f'FILE {key} RECEIVED')
                s3.download_file(bucket, key, rf'/home/ubuntu/mobivision/src/mvapp/static/{key}')

                sqs.delete_message(QueueUrl=os.environ.get('queueURL'), ReceiptHandle=res['Messages'][0]['ReceiptHandle']) #Delete message when done
