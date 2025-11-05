import pandas as pd
import requests
import json
import time
import os
import random
import math

# --- Configuration ---
# IMPORTANT: Replace with your actual Kentik API credentials
KENTIK_API_EMAIL = os.getenv('KENTIK_EMAIL')
KENTIK_API_TOKEN = os.getenv('KENTIK_TOKEN')
KENTIK_API_BASE_URL = "https://grpc.api.kentik.com" # Kentik API v6 base URL

# Path to your CSV file
CSV_FILE_PATH = "./device_list.csv"

# COLOR LIST
COLOR_LIST = ["#91a3b0", "#b64605", "#374d5d", "#2c4d1d", "#3970a7", "#fae57c"]

CUSTOMER_SNMP_COMMUNITY = ""

# --- Helper Functions ---
def _gather_device_list():
    response = _make_kentik_api_call("GET", "device/v202308beta1/device", None, "query.noCustomColumns=true")
    device_dict = response
    device_list = []
    for item in device_dict["devices"]:
        device_list.append(item['deviceName'])
    return device_dict, device_list

def _gather_all_sites():
    response = _make_kentik_api_call("GET", "site/v202211/sites")
    return response

def _gather_all_labels():
    response = _make_kentik_api_call("GET", "label/v202210/labels")
    label_dict = response
    return label_dict

def _make_kentik_api_call(method, endpoint, data=None, params=None):
    """
    Helper function to make API calls to Kentik.
    Handles authentication, error checking, and rate limiting.
    """
    headers = {
        "X-CH-Auth-Email": KENTIK_API_EMAIL,
        "X-CH-Auth-API-Token": KENTIK_API_TOKEN,
        "Content-Type": "application/json"
    }
    url = f"{KENTIK_API_BASE_URL}/{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"Error: Unsupported HTTP method '{method}'")
            return None

        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f"!!! HTTP error occurred: {http_err} - Response: {response.text} !!!")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"!!! Connection error occurred: {conn_err} !!!")
    except requests.exceptions.Timeout as timeout_err:
        print(f"!!! Timeout error occurred: {timeout_err} !!!")
    except requests.exceptions.RequestException as req_err:
        print(f"!!! An unexpected error occurred: {req_err} !!!")
    return None

def create_device(device_data, existing_devices, devices_list, existing_sites):
    """Creates a new device in Kentik."""
    #print(f"Attempting to create device: '{device_data['device_name']}'")
    site_id = False
    for site in existing_sites['sites']:
        if device_data['site'] == site['title']:
            #print(f"Site {device_data['site']} exists.")
            site_id = site['id']
    if not site_id:
        #print(f"Site {device_data['site']} does not exists.")
        #print(f"Creating site,{device_data['site']}")
        payload = {
            "site": {
                "title": device_data['site'],
                "type": "SITE_TYPE_OTHER"
            }
        }
        site_data = _make_kentik_api_call("POST", "site/v202211/sites", data=payload, params=None)
        if site_data:
            site_id = site_data['site']['id']
        else:
            print(f"!!!ERROR - Could not create the site. {device_data['site']}")
            return None

    device_payload = {
        "device": {
            "deviceName": device_data['device_name'],
            "deviceSubtype": "router", # Default type, adjust if needed (e.g., "host", "switch")
            "sendingIps": device_data['ip_address'],
            "deviceSampleRate": 1,
            "deviceDescription": f"Device created by Kentik automation script: {device_data['device_name']}",
            "deviceBgpType": "none",
            "planId": 70649,
            "minimize_snmp": False,
            "siteId": site_id,
            "deviceSnmpIp": device_data['ip_address'],
            "deviceSnmpCommunity": CUSTOMER_SNMP_COMMUNITY
        }
    }
    # Check if device already exists
    response = None
    if device_data['device_name'].lower() in devices_list or f"{device_data['device_name']}.visa.com".lower() in devices_list:
        #print(f"Device already exists with name: '{device_data['device_name']}'")
        #print(f"Attempting to update device: '{device_data['device_name']}")
        for device in existing_devices['devices']:
            if device['deviceName'].lower() == device_data['device_name'].lower() or device['deviceName'].lower() == f"{device_data['device_name']}.visa.com".lower():
                device_payload['device']['id'] = device['id']
        if 'visa.com' in device_data['device_name'].lower() and device_payload['device'].get('id'):
            response = _make_kentik_api_call("PUT", f"device/v202308beta1/device/{device_payload['device']['id']}", data=device_payload)
        elif device_payload['device'].get('id'):
            device_data['device_name'] = f"{device_data['device_name']}.visa.com"
            response = _make_kentik_api_call("PUT", f"device/v202308beta1/device/{device_payload['device']['id']}", data=device_payload)
        else:
            print(f"!!!ERROR - Device ID Not found - {device_data['device_name']}")
    elif device_data['ip_address'] in devices_list:
        #print(f"Device already exists with name: '{device_data['ip_address']}'")
        #print(f"Attempting to update device: '{device_data['device_name']}'")
        for device in existing_devices['devices']:
            if device['deviceName'].lower() == device_data['ip_address'].lower():
                device_payload['device']['id'] = device['id']
        response = _make_kentik_api_call("PUT", f"device/v202308beta1/device/{device_payload['device']['id']}", data=device_payload)
    else:
        response = _make_kentik_api_call("POST", "device/v202308beta1/device", data=device_payload)
    if response and 'device' in response:
        #print(f"Successfully created device: '{device_data['device_name']}' (ID: {response['device']['id']})")
        return response['device']['id']
    print(f"!!! Error: Failed to create or update device: '{device_data['device_name']}' !!!")
    if device_payload['device'].get('id'):
        return device_payload['device']['id']
    else:
        return None


def update_labels_device(device_data, device_id, existing_devices, existing_labels):
    """Creates a new device in Kentik."""
    #print(f"Attempting to add labels to the device: '{device_data['device_name']}'")
    label_ids = []
    labels = [device_data['role'], device_data['lane'], device_data['function'], device_data['type']]
    for label in labels:
        label_exists = False
        for existing_label in existing_labels['labels']:
            if existing_label["name"].lower() == label.lower():
                label_ids.append(existing_label['id'])
                label_exists = True
        if not label_exists:
            #print(f"Need to create label: {label}")
            label_payload = {
                "label": {
                    "name": label,
                    "description": label,
                    "color": random.choice(COLOR_LIST)
                }
            }
            response = _make_kentik_api_call("POST", "label/v202210/labels", data=label_payload)
            label_return = response
            label_ids.append(label_return['label']['id'])
            existing_labels['labels'].append(label_return['label'])
    labels_list = []
    for label in label_ids:
        label_dict = {"id": int(label)}
        labels_list.append(label_dict)
    
    payload = {
        "id": device_id,
        "labels": labels_list
    }
    response = _make_kentik_api_call("PUT", f"device/v202308beta1/device/{device_id}/labels", data=payload)

    return None



def main():
    """Main function to orchestrate the site and device creation."""
    print("Starting Kentik automation script...")

    # 1: Gather the current list of devices.

    existing_devices, devices_list = _gather_device_list()

    # 2. Read CSV file
    try:
        df = pd.read_csv(CSV_FILE_PATH)
        print(f"Successfully loaded CSV file: '{CSV_FILE_PATH}' with {len(df)} entries.")
    except FileNotFoundError:
        print(f"Error: CSV file not found at '{CSV_FILE_PATH}'. Please check the path.")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # 3 Ensure required columns exist
    required_headers = ['device_name', 'ip_address', 'site', "role", "lane", "function", "type"]
    if not all(header in df.columns for header in required_headers):
        print(f"Error: CSV file must contain all required headers: {', '.join(required_headers)}")
        return

    # 4 Get existing sites once to minimize API calls
    existing_sites = _gather_all_sites()

    # 5 Next process and add the labels
    existing_labels = _gather_all_labels()

    # 6 Process each row in the CSV
    for index, row in df.iterrows():
        device_name = row['device_name']
        ip_address = row['ip_address']
        site = row['site']
        if type(device_name) is float or type(ip_address) is float or type(site) is float:
            print(f"!!!ERROR - {device_name} does not have a necessary field")
            continue
        #print(f"\n--- Processing Device: {device_name} (IP: {ip_address}) ---")
        device_id = create_device(row, existing_devices, devices_list, existing_sites)
        if device_id:
            #print(f"\n--- Adding labels to Device: {device_name} (IP: {ip_address}) ---")
            update_labels_device(row, device_id, existing_devices, existing_labels)
        time.sleep(2)

    print("\nKentik automation script finished.")

if __name__ == "__main__":
    main()
