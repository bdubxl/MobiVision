from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import os
import csv
import sys
import boto3

s3 = boto3.client('s3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    )

def get_color(flag, colors):
    return colors[f'{flag[1], flag[0]}']

def convert_minmax(row): #Convert min/max set of coordinates to min/max set of pixels of image
    lat_coor = hei - (float(row[0]) - min_lat) / (max_lat - min_lat) * (hei - 0) + 0
    lon_coor = (float(row[1]) - min_lon) / (max_lon - min_lon) * (wid - 0) + 0
    return lat_coor, lon_coor

def create_map(path, csv_path, coords): #Visualize points from csv onto map with trace of coordinates

    key = csv_path.split('.')[0].split('/')[-1]

    global min_lat, max_lat, min_lon, max_lon
    min_lat = coords[0]
    max_lat = coords[1]
    min_lon = coords[2]
    max_lon = coords[3]

    img = Image.open(path)
    global wid, hei
    wid, hei = img.size #Width and height of image in pixles
    pixels = wid*hei #Total number of pixels in image
    f_const = 0

    if pixels >= 4000000: #Change flag constant depending on the size of the image so size of circles will change
    	f_const = pixels * 0.0000025
    elif pixels >= 2000000:
        f_const = pixels * 0.000005
    elif pixels >= 1000000:
        f_const = pixels * 0.00001
    elif pixels >= 500000:
        f_const = pixels * 0.00002
    elif pixels >= 250000:
        f_const = pixels * 0.00004
    elif pixels >= 125000:
        f_const = pixels * 0.00008
    elif pixels >= 62500:
        f_const = pixels * 0.00016
    elif pixels >= 31250:
        f_const = pixels * 0.00032
    elif pixels >= 15625:
        f_const = pixels * 0.00064
    else:
        f_const = pixels * 0.00128

    file = open(csv_path, 'r', newline='')
    reader = csv.reader(file)

    img_points = []
    flag_points = []
    start_point = []
    end_point = []
    colors = {}
    reader_list = list(reader)

    for row in reader_list: #Convert starting point of list and append to start_point
        lat_coor, lon_coor = convert_minmax(row)
        start_point.append([lon_coor, lat_coor])
        break

    for row in reader_list[::-1]: #Convert ending point of list and append to end_point
        lat_coor, lon_coor = convert_minmax(row)
        end_point.append([lon_coor, lat_coor])
        break

    for row in reader_list: #Convert all points in list and add to img_points
        lat_coor, lon_coor = convert_minmax(row)
        img_points.append([lon_coor, lat_coor])
        if row[2] != '*':
            flag = row[2]
            if flag == 'Speeding':
                flag_points.append([lon_coor, lat_coor]) #If current row has flag in it append point to flag_points
                colors[f'{lat_coor, lon_coor}'] = '#7d0000' #Color of circle will change depending on flag type
            elif flag == 'Hard Acceleration':
                flag_points.append([lon_coor, lat_coor])
                colors[f'{lat_coor, lon_coor}'] = '#ff7300'
            elif flag == 'Hard Breaking':
                flag_points.append([lon_coor, lat_coor])
                colors[f'{lat_coor, lon_coor}'] = '#0048ff'
            elif flag == 'Hard Cornering':
                flag_points.append([lon_coor, lat_coor])
                colors[f'{lat_coor, lon_coor}'] = '#00a118'
            elif flag == 'Ran Stop Sign':
                flag_points.append([lon_coor, lat_coor])
                colors[f'{lat_coor, lon_coor}'] = 'red'

    draw = ImageDraw.Draw(img)

    #Draw line for image points and circle with color for flag points
    for i in range(len(img_points)):
        try:
            if img_points[i+1]:
                line = img_points[i][0], img_points[i][1], img_points[i+1][0], img_points[i+1][1]
                draw.line(line, fill=(0,0,255), width=4)
            else:
                break
        except:
            break

    for flag in flag_points: #Draw flag circles
        draw.ellipse((flag[0]-f_const, flag[1]-f_const, flag[0]+f_const, flag[1]+f_const), fill=get_color(flag, colors), outline=(0,0,0))

    for flag in start_point: #Draw start circle
        draw.ellipse((flag[0]-f_const, flag[1]-f_const, flag[0]+f_const, flag[1]+f_const), fill='white', outline=(0,0,0))

    for flag in end_point: #Draw end circle
        draw.ellipse((flag[0]-f_const, flag[1]-f_const, flag[0]+f_const, flag[1]+f_const), fill='black', outline=(0,0,0))

    img.save(rf"/home/ubuntu/mapvis/renderedgpsmaps/{key}.png")
    s3.upload_file(Filename=rf"/home/ubuntu/mapvis/renderedgpsmaps/{key}.png", Bucket=os.environ.get('webbucket'), Key=fr"{key}.png")
