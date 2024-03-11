'''
Program Name: GatherRecentAlarms
Product: Kentik
Author: Ethan Angele
Description" This program connects to the Kentik API and pulls the most recent alarms according to a user defined "go back" timer. 
'''

# IMPORTED MODULES
import requests
import json
import datetime
from time import strftime, gmtime
from datetime import timedelta
import modules.auth as auth
import modules.inputs as inputs
import modules.outputs as outputs
import sys

def main():
    print('Main function')
    seconds_back = inputs.startTime()

    print(f"Going back {seconds_back} seconds...")
    
    time_back = datetime.datetime.now(datetime.timezone(-timedelta(hours=0))) - datetime.timedelta(0, seconds_back)
    time_back = time_back.strftime("%Y-%m-%dT%H:%M:%S")

    now = datetime.datetime.now(datetime.timezone(-timedelta(hours=0)))
    now = now.strftime("%Y-%m-%dT%H:%M:%S")

    parameters = inputs.filterParameters()

    if parameters == None:
        url = f"https://api.kentik.com/api/v5/alerting/alarms?limit=1000&startTimeStart={time_back}Z"
    else:
        url = f"https://api.kentik.com/api/v5/alerting/alarms?limit=1000&sortBy=startTimeStart&startTimeStart={time_back}Z&{parameters}"
    
    print('---------------')
    print('connecting to...')
    print(url)
    print('---------------')

    payload = ""
    headers = {
    'X-CH-Auth-Email': auth.username,
    'X-CH-Auth-API-Token': auth.apikey,
    'Content-Type': 'application/json'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code != 200:
        print(f'ERROR - Status Code: {response.status_code}')
        print(f'MESSAGE - {response.text}')
        sys.exit()

    response_dict = response.json()

    outputs.printStructured(response_dict)

if __name__ == "__main__":
    main()