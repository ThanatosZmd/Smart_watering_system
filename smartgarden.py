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
scheduled_tasks = []
schedules = []
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
				
		elif message.topic == 'schedules':
				payload = str(message.payload.decode("utf-8"))
				message_data = json.loads(payload)
				schedules.append(message_data)
				current_day = datetime.now().strftime('%A')
				current_time = datetime.now()
				print(current_time)
				print(current_day)
				print(schedules)
				
				
				
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
		
		for index, message_data in enumerate(schedules):
			days = message_data['days'].split(',')
			start_time = datetime.strptime(message_data['time_start'], '%H:%M').time()
			end_time = datetime.strptime(message_data['time_end'], '%H:%M').time()
			current_day = datetime.now().strftime('%A')
			for day in days:
				cleaned_days = day.strip()
				print(cleaned_days)
				print(end_time)

				if current_day in cleaned_days:
					current_time = datetime.now().time().replace(second=0, microsecond=0)
					print(current_time)

					if start_time <= current_time < end_time:
						GPIO.output(6, GPIO.LOW)
						GPIO.output(5, GPIO.LOW)
						GPIO.output(13, GPIO.LOW)
					if current_time >= end_time:
						GPIO.output(5, GPIO.HIGH)
						GPIO.output(6, GPIO.HIGH)
						GPIO.output(13, GPIO.HIGH)

			time.sleep(2)  # Sleep for one minute before checking again
		
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
	client.subscribe("schedules")
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

