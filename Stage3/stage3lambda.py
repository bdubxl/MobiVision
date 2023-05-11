import boto3
import csv
import json
import os
import requests

s3 = boto3.client('s3')

def get_speed_limit(lat, lon):
    latitude = str(round(float(lat), 6))
    longitude = str(round(float(lon), 6))
    key = str(os.environ.get('azure_key'))

    r = requests.get(rf'https://atlas.microsoft.com/search/address/reverse/json?api-version=1.0&query={latitude},{longitude}&returnSpeedLimit=true')
    response = r.json()

    try:
        speed_limit = float(response['addresses'][0]['address']['speedLimit'].split("M")[0])
        return speed_limit
    except:
        return None

def insert_events(reader, key):
    headers = {'x-api-key': str(os.environ.get('xapikey'))}
    for row in reader:
        if row[6] != '*':
            requests.post(rf'https://sbebc8tcb4.execute-api.us-east-1.amazonaws.com/one/upload?tripdate={key}&lat={row[0]}&lon={row[1]}&speed={row[2]}&x={row[3]}&y={row[4]}&time={row[5]}&flag={row[6]}', headers=headers)

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    s3.download_file(Bucket=bucket, Key=key, Filename=rf'/tmp/{key}')

    read_file = open(rf'/tmp/{key}', 'r', newline='')
    write_file = open(rf'/tmp/write{key}', 'w+', newline='')
    
    reader = csv.reader(read_file)
    writer = csv.writer(write_file)

    for i, row in enumerate(reader):
        if i % 10 == 0:  # Check speeds every 10 rows (10 seconds)
            speed = float(row[2]) # Get speed from csv row
            if speed < 65:
                speed_limit = get_speed_limit(row[0], row[1])  # Get speed limit with latitude and longitude for api
                if speed_limit == None: #If speed limit data not available, rewrite current row as is
                    writer.writerow(row)
                elif (speed - speed_limit) > 5: # If over speed limit by 5 mph
                    row[6] = 'Speeding' # Add speeding flag to current row
                    writer.writerow(row) # Write row to new file
                else:
                    writer.writerow(row) #Add row as is
            else:
                writer.writerow(row) #Add row as is
        else:
            writer.writerow(row) #Add row as is
            
    read_file.close()
    write_file.close()
    final_file = open(rf'/tmp/write{key}', 'r', newline='')
    final_reader = csv.reader(final_file)
    
    # Insert all rows with flags into database
    insert_events(final_reader, key.split(".")[0])
    
    # Upload updated csv to stage 3
    s3.upload_file(rf'/tmp/write{key}', 'stage4mv', key)
