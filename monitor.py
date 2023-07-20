# EcoFlow Battery Monitor

import os
import time
import requests
from datetime import date, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.environ['EMAIL']
PWD = os.environ['PWD']
# Existing TOKEN may be defined in env
SERIAL = os.environ['SERIAL']
SENDGRID_API_KEY=os.environ['SENDGRID_API_KEY']

power_status = "off"

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


authtoken = get_token()
while True:
	current_level = get_battery_level()
	if current_level == "unauthorized":
		authtoken = get_token()
		current_level = get_battery_level()
	if current_level < 20:
		# Turn AC Power On
		print("uh oh low battery")
	if current_level > 50:
		# Turn AC Power Off
		print("no more ac for you")
	time.sleep(60)
