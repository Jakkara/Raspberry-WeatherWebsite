from picamera import PiCamera
from time import sleep
import datetime
import time
import sys
import ftplib
import os

# functions
def parse_temperature():
	lines = read_file_data()    # call the method for parsing
	while lines[0].strip()[-3:] != 'YES': # the sensor will show a 'YES' on succesful reading
		time.sleep(2)         # sleep on failure, try again later
		lines = read_file_data()
	temperature = lines[1].find('t=') #luetaann
	if temperature != -1:
		temperature_numbers = lines[1].strip()[temperature+2:]
		celsius = float(temperature_numbers) / 1000.0
		return celsius

def read_file_data():
	file_reader = open(sensor_output_path,'r')  # scan the temperature reading file
	lines = file_reader.readlines()     # read the result
	file_reader.close()     # close the reader
	return lines

# initialize system for temperature readings and activate camera
os.system('modprobe w1-gpio')		#activate gpio for temperature
os.system('modprobe w1-therm')      #library for temp readings
sensor_output_path = '/sys/bus/w1/devices/28-0417618cabff/w1_slave'
camera = PiCamera()

# temperature 
temperature = parse_temperature()

# temperature readings history
with open('/tmp/templog') as input:
    readings = input.readlines() 
readings = [x.strip() for x in readings]
print(readings)

# calculate the change rate
readings.pop(0)
readings.append(temperature)
average_growth_rate = (int(readings[4]) - int(readings[0])) / 5.0

# save readings back to file
with open('/tmp/templog', 'w') as f:
    for item in readings:
        f.write("%s\n" % item)

# make decisions from growth rate
growth_results = ""
if average_growth_rate >= 0:
    growth_results = "Temperature rising: "
else:
    growth_results = "Cooling down: "
growth_results += str(average_growth_rate)

timestamp = datetime.datetime.utcnow()
image_filepath = '/home/pi/FtpCamera/photos/' + str(timestamp) + '.jpg'
camera.rotation = 180
sleep(2)
camera.capture(image_filepath)
sleep(1)
print("Captured photo " + image_filepath)


# create an html file from the information
with open('/home/pi/FtpCamera/index_template.html', 'r') as myfile:
    index_html = myfile.read()
    myfile.close()
first_part_of_page = index_html[0:index_html.index("<!--HERE-->")] + "Temperature: " + str(temperature)[:4] + " C <br>" + growth_results + " C per minute."
second_part_of_the_page = index_html[index_html.index("<!--HERE-->"):]
ready_index_html = first_part_of_page + second_part_of_the_page
index_file = open("/home/pi/FtpCamera/index.html", "w+")
index_file.write(ready_index_html)
index_file.close()

# initialize FTP
print("Opening FTP connection...")
with open('credentials.pass') as f:
    content = f.readlines()
content = [x.strip() for x in content]
session = ftplib.FTP(content[0],content[1],content[2])

# transmit image
image_file = open(image_filepath, 'rb')
session.storbinary('STOR public_html/Raspi/photos/snap.jpg', image_file)  # send the file
print("Image sent.")
image_file.close()

# transmit index.html
html_filepath = '/home/pi/FtpCamera/index.html'
html_file = open(html_filepath, 'rb')
session.storbinary('STOR public_html/Raspi/index.html', html_file)
print("Index.html sent")
html_file.close()

session.quit()

# delete images from local folder
if os.path.isfile(image_filepath):
    print("Deleting local image file...")
    os.remove(image_filepath)
print("Finished run.")
