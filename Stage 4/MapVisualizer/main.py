import test as t
import os
import sys
import drawmap as dm

csv_path = sys.argv[1] # In sqsstuff.py, a command line argument with the path of the file is used to get this variable
t.get_map(csv_path) # Access test.py file which which automates the process of getting cross section of map based on coordinates
dm.create_map(r'/home/ubuntu/map.png', csv_path, [t.min_lat, t.max_lat, t.min_lon, t.max_lon])

os.remove('/home/ubuntu/map.png') # Remove base map generated by test.py
os.system('sudo rm -f /home/ubuntu/mapvis/renderedgpsmaps/*')

print('RENDERED MAP UPLOADED TO S3')
