import requests
import json
import os
import time
import sys

# --- Configuration ---
# IMPORTANT: Replace with your actual Kentik API credentials
KENTIK_API_EMAIL = os.getenv('KENTIK_EMAIL')
KENTIK_API_TOKEN = os.getenv('KENTIK_TOKEN')
REGION = "US" # Set the region if you use EU
KENTIK_API_BASE_URL = "https://grpc.api.kentik.com" # Kentik API v6 base URL
API_VERSION = "v202308beta1"
KENTIK_HEADERS = {
        "X-CH-Auth-Email": KENTIK_API_EMAIL,
        "X-CH-Auth-API-Token": KENTIK_API_TOKEN,
        "Content-Type": "application/json"
    }
NETBOX_BASE_URL = os.getenv('NETBOX_URL')
NETBOX_TOKEN = os.getenv('NETBOX_TOKEN')
NETBOX_HEADERS = {
        "Authorization": f"Token {NETBOX_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

def gather_kentik_labels():
    """Gather the current list of labels"""
    print("Gathering a list of Kentik Labels")
    url = f"{KENTIK_API_BASE_URL}/label/v202210/labels"
    payload = {}
    headers = KENTIK_HEADERS
    label_data = {}
    try:
        response = requests.request(
            "GET", url, headers=headers, data=payload, timeout=30
        )
        if response.status_code == 200:
            label_data = response.json()
        else:
            print(f"ERROR, received a {response.status_code} status code")
            sys.exit(1)
    except ConnectionError as exc:
        print(f"ERROR: Connection Error gather labels with message: {exc}")
    label_dict = {}
    for label in label_data["labels"]:
        label_dict[label["name"]] = label["id"]
    return label_dict

def gather_netbox_tenants():
    '''Gather a list of netbox tenatns'''
    print("Gathering a list of Netbox Tenants")
    # Define the API endpoint for tenants
    api_endpoint = f"{NETBOX_BASE_URL}/api/tenancy/tenants/"

    # Set up the headers for the API request, including the authorization token
    headers = NETBOX_HEADERS

    try:
        # Make the GET request to the NetBox API
        print(f"Attempting to connect to {api_endpoint}...")
        response = requests.get(api_endpoint, headers=headers, timeout=10)

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Parse the JSON response and return the 'results' key which contains the list of tenants
        data = response.json()
        print("Successfully retrieved tenant data.")
        return data.get("results", [])

    except requests.exceptions.RequestException as e:
        # Catch any request-related errors (e.g., network issues, invalid URL)
        print(f"An error occurred: {e}")
        return None
    except json.JSONDecodeError:
        # Catch errors if the response is not valid JSON
        print("Error: Failed to decode JSON response.")
        return None

def get_devices_by_tenant(tenant):
    '''Gather device from netbox by tenant'''
    print(f"Gathering a list of devices for tenant {tenant['name']}")
    # Define the API endpoint for devices with a filter for tenant ID
    api_endpoint = f"{NETBOX_BASE_URL}/api/dcim/devices/?tenant_id={tenant['id']}"

    # Set up the headers for the API request, including the authorization token
    headers = NETBOX_HEADERS
    
    try:
        # Make the GET request to the NetBox API
        print(f"Attempting to connect to {api_endpoint}...")
        response = requests.get(api_endpoint, headers=headers, timeout=10)

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Parse the JSON response and return the 'results' key
        data = response.json()
        print(f"Successfully retrieved device data for tenant ID {tenant['name']}.")
        return data.get("results", [])

    except requests.exceptions.RequestException as e:
        # Catch any request-related errors (e.g., network issues, invalid URL)
        print(f"An error occurred: {e}")
        return None
    except json.JSONDecodeError:
        # Catch errors if the response is not valid JSON
        print("Error: Failed to decode JSON response.")
        return None

def compare_label(kentik_label_list, label):
    """Check to see if the label already exists"""
    print(f"Checking that {label['name']} exists")
    if label['name'] in kentik_label_list:
        print(f"Label {label['name']} exists")
        function_return = kentik_label_list[label['name']]
    else:
        print(f"Creating label, {label['name']}")
        function_return = create_label(label['name'])
    return function_return

def create_label(label):
    """Creates a label"""
    url = f"{KENTIK_API_BASE_URL}/label/v202210/labels"
    payload = json.dumps({
        "label": {
            "name": label,
            "description": f"Tenant from netbox for team {label}",
            "color": "#033a63"
            }
        })
    headers = KENTIK_HEADERS
    function_return = ''
    try:
        response = requests.request(
            "POST", url, headers=headers, data=payload, timeout=30
        )
        label_data = response.json()
        if response.status_code == 200:
            function_return = label_data["label"]["id"]
        else:
            print(response.text)
    except ConnectionError as exc:
       print(f"ERROR: Connection error when creating the label - {exc}")
    return function_return

def check_device(device_name):
    """Function to check if the device exists in kentik"""
    print(f"Checking if Device, {device_name} exists...")
    if REGION == "EU":
        url = f"https://api.kentik.eu/api/v5/device/{device_name}"
    else:
        url = f"https://api.kentik.com/api/v5/device/{device_name}"
    headers = KENTIK_HEADERS
    payload = {}
    response = http_request_func("GET", url, headers, payload)
    if response:
        device_info = response.json()
    else:
        device_info = False
        print(f"Device, {device_name}, does not exist")
    return device_info

def update_device_labels(device_data, label):
    """Function to add or update device labels"""
    print("Updating Device Labels...")
    device_id = device_data['device']['id']
    device_labels = device_data['device']['labels']
    url = f"{KENTIK_API_BASE_URL}/device/{API_VERSION}/device/{device_id}/labels"
    headers = KENTIK_HEADERS
    labels_list = []
    device_data = ''
    for label in device_labels:
        label_dict = {"id": int(label)}
        labels_list.append(label_dict)
    labels_list.append(label)
    payload = json.dumps({"id": device_id, "labels": labels_list})
    response = http_request_func("PUT", url, headers, payload)
    device_data = response.json()
    return device_data["device"]["id"]

def http_request_func(method, url, headers, payload, retries=0):
    """Function for handling HTTP Requests"""
    if retries < 3:
        try:
            response = requests.request(
                method, url, headers=headers, data=payload, timeout=30
            )
            if response.status_code == 200:
                print("%s HTTP Request Successfull for url: %s", method, url)
            elif response.status_code == 429:
                if 'x-ratelimit-reset' in response.headers:
                    time.sleep(int(response.headers['x-ratelimit-reset']))
                else:
                    time.sleep(60)
                retries += 1
                http_request_func(method, url, headers, payload, retries)
            elif response.status_code == 404:
                return False
            else:
                print(response.text)
            if 'x-ratelimit-remaining' in response.headers:
                if int(response.headers['x-ratelimit-remaining']) < 10:
                    time.sleep(10)  # Helps to slow down the rate of execution for throttling.
        except ConnectionError as exc:
            print(f"ERROR: Connection error when attaching the label - {exc}")
    else:
        print("ERROR - RETRIED 3 TIMES")
    return response

def main():
    '''MAIN FUNCTION PROGRAM STARTS HERE'''
    print("Starting the label sync program for Kentik and Netbox")
    kentik_label_list = gather_kentik_labels()
    print(kentik_label_list)
    netbox_tenant_list = gather_netbox_tenants()
    for label in netbox_tenant_list:
        label_id = compare_label(kentik_label_list, label)
        device_list = get_devices_by_tenant(label)
        for device in device_list:
            device_data = check_device(device['name'])
            if device_data:
                update_device_labels(device_data, label_id)
                print(f"Label, {label['name']}, associated to device, {device['name']}.")

if __name__ == "__main__":
    main()
