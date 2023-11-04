#!/usr/bin/python3

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time
import requests
import threading
from datetime import datetime, timedelta
import board
import json 
import adafruit_dht
import random

taps_board = [ 29, 31, 33, 36, 35, 38, 40, 37 ]
taps = [5, 6, 13, 16, 19, 20, 21, 26]
first_three_taps = [5, 6, 13]
states = [ 0, 0, 0, 0, 0, 0, 0, 0 ]
scheduled_day_tasks = []
scheduled_tasks = []
web_data = []
sensor = adafruit_dht.DHT11(board.D4)
client = mqtt.Client()

now = datetime.now().replace(second=0, microsecond=0)
print(now)
#def is_internet_connected():
	#try:
	#	response = requests.get("http://www.uktc-edu.eu", timeout=5)
	#	return response.status_code == 200
	#except requests.ConnectionError:
	#	return False

#def wait_for_internet():
	#while not is_internet_connected():
	#	time.sleep(1)

    
def activate_relays(taps):
    GPIO.output(taps[0], GPIO.LOW)
    GPIO.output(taps[1],GPIO.LOW)


 
def convert_days_to_numbers(days):
	day_mapping = {
        'Mon': 1,
        'Tue': 2,
        'Wed': 3,
        'Thu': 4,
        'Fri': 5,
        'Sat': 6,
        'Sun': 7
    }
	
	converted_days = []
	for day in days.split(','):
		converted_days.append(day_mapping[day.strip()])

	return converted_days
		


def handle_scheduled_data(data):
	schedule_days = convert_days_to_numbers(data['days'])
	schedule_time_start = data['time_start']
	schedule_time_end = data['time_end']
	
	scheduled_day_tasks.append({'schedule_days': schedule_days, 'schedule_time_start': schedule_time_start, 'schedule_time_end': schedule_time_end})
	client.publish("active_presets", json.dumps(scheduled_day_tasks))
	edited_schedule_days = str(schedule_days)[1:-1]
	print(scheduled_day_tasks)
	print(f"Scheduled Days: {schedule_days}") 
	print(edited_schedule_days)
 

def on_message(client, userdata, message):
	try:
		if message.topic == 'settaps':
			num = int(message.payload.decode("utf-8"))
			num -= 1
			
			if states[num] == 0:
				states[num] = 1
				GPIO.output(taps[num], GPIO.LOW)
				
			else:
				states[num] = 0
				GPIO.output(taps[num], GPIO.HIGH)
				
		elif message.topic == 'checktaps':
				client.publish("sgarden/taps", ','.join(map(str, states)))
				
		elif message.topic == 'schedule_tap':
				payload = str(message.payload.decode("utf-8"))
				data = json.loads(payload)
				scheduled_time = datetime.strptime(data['date'] + ' ' + data['time'], '%Y-%m-%d %H:%M')
				current_time = datetime.now().replace(second=0, microsecond=0)
				tapNumber = data['tapNumber']
				scheduled_tasks.append({'scheduled_time': scheduled_time, 'tapNumber': tapNumber})
				print(f"Scheduled Time: {scheduled_time}")
				print(f"Cuurent tapNumber is {tapNumber}")
				
		elif message.topic == 'schedule_tap_days':
				payload = str(message.payload.decode("utf-8"))
				data = json.loads(payload)
				schedule_days = data['days']
				schedule_time_start = datetime.strptime(data['time_start'], '%H:%M').time()
				schedule_time_end = datetime.strptime(data['time_end'], '%H:%M').time()
				day_of_week = now.weekday()
				time_now = datetime.now().time()
				web_data.append({'schedule_days': schedule_days, 'schedule_time_start': schedule_time_start, 'schedule_time_end': schedule_time_end})
				handle_scheduled_data(data)
	except Exception as e:
			print(f'Invalid command: {e}') 


def activate_tap(tapNumber):
	try:
		num = tapNumber - 1
		if states[num] == 0:
			states[num] = 1
			GPIO.output(taps[num], GPIO.LOW)
		else:
			states[num] = 0
			GPIO.output(taps[num], GPIO.HIGH)
	except Exception as e:
		print(f'Error while turning on/off tap {tap_num}: {e}')
		
def stop_relays():
    try:
        for tap_num in first_three_taps:
            num = tap_num - 1
            states[num] = 0
            GPIO.output(taps[num], GPIO.HIGH)
    except Exception as e:
        print(f'Error while turning off taps: {e}')
		
def send_temp():
    global client, sensor
    while True:
        try:
            temp = sensor.temperature
            hum = sensor.humidity
            payload = f'Temperature:{temp}*C  Humidity: {hum}%'
            client.publish("sgarden/weather", payload)  
            time.sleep(1)

        except RuntimeError as error:
            print(error.args[0])
            time.sleep(2.0)
            continue

        except Exception as error:
            sensor.exit()
            raise error
            time.sleep(2.0)



def dev_check():
	global client
	while True:
		client.publish("sgarden/check", '[ok]')
		time.sleep(1)


def check_scheduled_days():
	while True:
		current_time = datetime.now()
		current_day = now.weekday()
	
		for data in scheduled_day_tasks:
			schedule_days = data['schedule_days']
			edited_schedule_days = str(schedule_days)[1:-1]
			schedule_time_start = data['schedule_time_start']
			schedule_time_end = data['schedule_time_end']

			if current_time == schedule_time_start:
				activate_relays()
			
			elif current_time == schedule_time_end:
				stop_relays()
		
		time.sleep(2)
		
def check_scheduled_tasks():
    while True:
        current_time = datetime.now().replace(second=0, microsecond=0)
        for task in scheduled_tasks:
            scheduled_time = task['scheduled_time']
            tapNumber = task['tapNumber']
            
            if current_time >= scheduled_time:
                activate_tap(tapNumber)
                scheduled_tasks.remove(task)
     
          
def main():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	
	for i in range(8):
		GPIO.setup(taps[i], GPIO.OUT, initial=GPIO.HIGH)
#	wait_for_internet()
	client.connect("broker.hivemq.com", 1883,60) 
	client.subscribe("settaps")
	client.subscribe("checktaps")
	client.subscribe("schedule_tap")
	client.subscribe("schedule_tap_days")
	client.on_message=on_message
	t1 = threading.Thread(target=send_temp)
	t2 = threading.Thread(target=dev_check)
	t4 = threading.Thread(target=check_scheduled_tasks)
	t3 = threading.Thread(target=check_scheduled_days)
	t1.start()
	t2.start()
	t3.start()
	t4.start()
	print('Started...')
	client.loop_forever()



if __name__ == "__main__":
	main()

