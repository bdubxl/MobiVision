from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd

#Script will automate gps visualization by using selenium to access OpenStreetMaps.org to get portion of map

def get_map(csv_path):
	# Retrieves the min and max lon and lat cooridnates for bounding box of section of map to get
	df = pd.read_csv(rf'{csv_path}', names=['lat', 'lon', 'flag']) # Remove all columns except for lat, lon and flags which are needed

	global min_lat, max_lat, min_lon, max_lon
	
	# Get minimum and maximum latitiude and longitude from the cvs. Also add/subtract constant for padding around the image
	min_lat = df['lat'].min() - 0.001
	min_lon = df['lon'].min() - 0.001
	max_lat = df['lat'].max() + 0.001
	max_lon = df['lon'].max() + 0.001


	options = webdriver.ChromeOptions()
	options.add_argument('--headless')
	options.add_argument('--no-sandbox')
	options.add_argument('--disable-gpu')
	options.add_experimental_option("prefs", {
	  "download.default_directory": r"/home/ubuntu/mapvis/renderedgpsmaps/",
	  "download.prompt_for_download": False,
	  "download.directory_upgrade": True,
	  "safebrowsing.enabled": True
	})

	# Modifying elements of html to use input csv's coordinates to capture section of map
	driver = webdriver.Chrome(executable_path=r'/usr/bin/chromedriver', options=options)
	driver.get(r'https://www.openstreetmap.org/export#map=13/41.6178/-72.7686')

	element = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[3]/div[4]/form/input[1]')
	driver.execute_script(f"arguments[0].setAttribute('value', '{min_lon}')", element)

	element = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[3]/div[4]/form/input[2]')
	driver.execute_script(f"arguments[0].setAttribute('value', '{min_lat}')", element)

	element = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[3]/div[4]/form/input[3]')
	driver.execute_script(f"arguments[0].setAttribute('value', '{max_lon}')", element)

	element = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[3]/div[4]/form/input[4]')
	driver.execute_script(f"arguments[0].setAttribute('value', '{max_lat}')", element)

	element = driver.find_element(By.XPATH, '/html/body/div/div[2]/div[3]/div[4]/form/input[7]')
	driver.execute_script(f"arguments[0].click()", element)

	time.sleep(5)
	driver.quit()
