#!/usr/bin/python3

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time
import requests
import threading
from datetime import datetime
import schedulew
import board
import adafruit_dht
import random

taps_board = [ 29, 31, 33, 36, 35, 38, 40, 37 ]
taps = [5, 6, 13, 16, 19, 20, 21, 26]
states = [ 0, 0, 0, 0, 0, 0, 0, 0 ]
sensor = adafruit_dht.DHT11(board.D4)
client = mqtt.Client()
schedule_taps = []

#def is_internet_connected():
	#try:
	#	response = requests.get("http://www.uktc-edu.eu", timeout=5)
	#	return response.status_code == 200
	#except requests.ConnectionError:
	#	return False

#def wait_for_internet():
	#while not is_internet_connected():
	#	time.sleep(1)

def schedule_tap(tap_num, date_str, time_str):
    scheduled_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    schedule.every().day.at(scheduled_time.strftime("%H:%M")).do(turn_on_tap, tap_num)
    
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
        
def cancel_scheduled_tap(tap_num):
    try:
        schedule.clear(f"turn_on_tap({tap_num})")
        print(f"Scheduled tap {tap_num} canceled.")
    except Exception as e:
        print(f'Error while canceling scheduled tap {tap_num}: {e}')

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
		elif message.topic == 'scheduletap':
            tap_num, date_str, time_str = message.payload.decode("utf-8").split(",")
            tap_num = int(tap_num)
            schedule_tap(tap_num, date_str, time_str)
            
    except Exception as e:
        print(f'Invalid command: {e}')

def send_temp():
	global client, sensor
	while True:
		try:
			temp = sensor.temperature
			hum = sensor.humidity
			client.publish("sgarden/weather", f'Temperature:{temp}*C  Humidity: {hum}%')
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


def main():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	
	for i in range(8):
		GPIO.setup(taps[i], GPIO.OUT, initial=GPIO.HIGH)
#	wait_for_internet()
	client.connect("broker.hivemq.com", 1883,60) 
	client.subscribe("settaps")
	client.subscribe("checktaps")
	client.subscribe("scheduletap")
	client.on_message=on_message
	t1 = threading.Thread(target=send_temp)
	t2 = threading.Thread(target=dev_check)
	t1.start()
	t2.start()
	print('Started...')
	client.loop_forever()



if __name__ == "__main__":
	main()

