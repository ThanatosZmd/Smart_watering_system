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
first_three_taps = [5,6,13]
states = [ 0, 0, 0, 0, 0, 0, 0, 0 ]
scheduled_tasks = []
scheduled_days = []
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

    
def turn_on_tap(tap_num):
    try:
        num = tap_num - 1
        if states[num] == 0:
            states[num] = 1
            GPIO.output(taps[num], GPIO.LOW)
        else:
            states[num] = 0
            GPIO.output(taps[num], GPIO.HIGH)
    except Exception as e:
        print(f'Error while turning on/off tap {tap_num}: {e}')

		

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
				
		if message.topic == 'schedule_tap_days':
				payload = str(message.payload.decode("utf-8"))
				data = json.loads(payload)
				schedule_days = data['days'][::]
				schedule_time = datetime.strptime(data['time'], '%H:%M').time()
				current_day = datetime.now().strftime('%a')
				current_time = datetime.now().time()
				scheduled_days.append({'schedule_days': schedule_days, 'schedule_time': schedule_time})
				print(current_day)
				print(schedule_time)
				print(schedule_days)
				
	
				

				
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

def activate_first_three_taps():
	for tap in first_three_taps:
		GPIO.output(tap, GPIO.LOW)
	
	

def send_temp():
    global client, sensor
    while True:
        try:
            temp = sensor.temperature
            hum = sensor.humidity
            payload = f'Temperature:{temp}*C  Humidity: {hum}%'
            client.publish("sgarden/weather", payload)  # Make sure this line is indented correctly
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
		current_day = datetime.now().strftime('%a')
		current_time = datetime.now().time()
		if current_day in scheduled_days and current_time == schedule_time:
			activate_first_three_taps()

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
	t3 = threading.Thread(target=check_scheduled_tasks)
	t4 = threading.Thread(target=check_scheduled_days)
	t4.start()
	t3.start()
	t1.start()
	t2.start()
	print('Started...')
	client.loop_forever()



if __name__ == "__main__":
	main()

