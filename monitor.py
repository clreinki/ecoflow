# EcoFlow Battery Monitor

import os
import time
import platform
import asyncio
import requests
from datetime import date, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from kasa import SmartPlug
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.environ['EMAIL']
PWD = os.environ['PWD']
# Existing TOKEN may be defined in env
SERIAL = os.environ['SERIAL']
SENDGRID_API_KEY=os.environ['SENDGRID_API_KEY']
PLUG_IP = os.environ['PLUG']

if platform.system() == 'Windows':
	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

#pstate = True
#p = SmartPlug(PLUG_IP)

def get_token():
	try:
		token = 'Bearer ' + os.environ['TOKEN']
	except:
		url = "https://api-a.ecoflow.com/auth/login"

		payload = json.dumps({
		  "appVersion": "4.7.2.28",
		  "countryCode": "US",
		  "email": EMAIL,
		  "os": "android",
		  "osVersion": "30",
		  "password": PWD,
		  "scene": "IOT_APP",
		  "source": "IOT_APP",
		  "userType": "ECOFLOW"
		})
		headers = {
		  'countrycode': 'US',
		  'lang': 'en-us',
		  'platform': 'android',
		  'sysversion': '11',
		  'version': '4.7.2.28',
		  'Content-Type': 'application/json'
		}

		response = requests.request("POST", url, headers=headers, data=payload)
		if not response.status_code == 200:
			print("ERROR - COULD NOT GET TOKEN!")
			send_email("COULD NOT GET NEW AUTH TOKEN!")
			exit()
		else:
			response_json = response.json()
			token = 'Bearer ' + response_json['data']['token']
			print("Retrieved token " + token)
	return token


def get_battery_level():

	url = "https://api-a.ecoflow.com/iot-service/user/device"
	payload = {}
	headers = {
	  'Authorization': authtoken,
	  'countrycode': 'US',
	  'lang': 'en-us'
	}

	response = requests.request("GET", url, headers=headers, data=payload)
	if response.status_code == 401:
		get_token()
		return "unauthorized"
	elif response.status_code == 200:
		api_data = response.json()
		battery = api_data['data']['bound'][SERIAL]['soc']
		print(str(battery) + '% at ' + time.strftime('%a %b %d %H:%M:%S'))
		return battery
	else:
		print("ERROR - ECOFLOW API DID NOT RESPOND APPROPRIATELY WITH CODE " + response.status_code)
		send_email("ERROR - ECOFLOW API DID NOT RESPOND APPROPRIATELY WITH CODE " + response.status_code)
		exit()

def send_email(msg):
	message = Mail(
	    from_email=EMAIL,
	    to_emails=EMAIL,
	    subject='ECOFLOW MONITOR ISSUE',
	    html_content=msg)
	try:
	    sg = SendGridAPIClient(SENDGRID_API_KEY)
	    response = sg.send(message)
	    print(response.status_code)
	    print(response.body)
	    print(response.headers)
	except Exception as e:
	    print(e.message)

async def get_plug(ip):
	p = SmartPlug(ip)
	await p.update()
	if p.is_on:
		return "on"
	else:
		return "off"

async def set_plug(ip, pstate):
	p = SmartPlug(ip)
	await p.update()
	if pstate == "on":
		await p.turn_on()
		print("Turned On AC Power")
	elif pstate == "off":
		await p.turn_off()
		print("Turned Off AC Power")
	else:
		print("An error occurred")
		send_email("An issue with the Kasa Plug occurred!")

authtoken = get_token()
ac_state = asyncio.run(get_plug(PLUG_IP))
print(ac_state)

while True:
	current_level = get_battery_level()
	if current_level == "unauthorized":
		authtoken = get_token()
		current_level = get_battery_level()
	if current_level < 20 and ac_state == "off":
		# Turn AC Power On
		ac_state = "on"
		asyncio.run(set_plug(PLUG_IP, "on"))
	if current_level > 50 and ac_state == "on":
		# Turn AC Power Off
		ac_state = "off"
		asyncio.run(set_plug(PLUG_IP, "off"))
	time.sleep(60)
