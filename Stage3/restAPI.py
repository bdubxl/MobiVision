import json
import psycopg2
import os

def lambda_handler(event, context):

    tripdate = event['queryStringParameters']['tripdate']
    lat = event['queryStringParameters']['lat']
    lon = event['queryStringParameters']['lon']
    speed = event['queryStringParameters']['speed']
    x = event['queryStringParameters']['x']
    y = event['queryStringParameters']['y']
    time = event['queryStringParameters']['time']
    flag = event['queryStringParameters']['flag']
    
    hostname = os.environ.get('hostname')
    port = os.environ.get('port')
    username = os.environ.get('username')
    password = os.environ.get('password')
    
    conn = psycopg2.connect(dbname='MobiVisionTables', host=hostname, port=port, user=username, password=password)
    cursor = conn.cursor()
    
    # Return if entry in 'Trips' table already exist for current tripdate
    cursor.execute(f"SELECT * FROM Trips WHERE tripdate='{tripdate}'")
    results = cursor.fetchone()

    # If no entries exist, insert trip into 'Trips' table first for foreign key reference in 'Events' table 
    if results == None:
        cursor.execute(f"INSERT INTO Trips(tripdate) VALUES ('{tripdate}')")
        cursor.execute(f"INSERT INTO Events(tripdate, lat, lon, speed, xacc, yacc, sec, flags) VALUES('{tripdate}', '{lat}', '{lon}', '{speed}', '{x}', '{y}', '{time}', '{flag}')")
    else: # Else insert into events table only
        cursor.execute(f"INSERT INTO Events(tripdate, lat, lon, speed, xacc, yacc, sec, flags) VALUES('{tripdate}', '{lat}', '{lon}', '{speed}', '{x}', '{y}', '{time}', '{flag}')")

    conn.commit()
    cursor.close()
    conn.close()
    
    return {
        'statusCode' : 200,
        'body' : 'DATA UPDATE SUCCESSFUL',
    }
