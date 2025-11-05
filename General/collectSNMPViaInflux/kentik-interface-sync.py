import json
import os
import time
import requests
# ==============================================================================
# Configuration
# ==============================================================================
# It is highly recommended to use environment variables for sensitive data.
KENTIK_API_EMAIL = os.environ.get("KENTIK_API_EMAIL")
KENTIK_API_TOKEN = os.environ.get("KENTIK_API_TOKEN")

# The URL for your Kentik API endpoint.
KENTIK_API_BASE_URL = "https://grpc.api.kentik.com"
KENTIK_API_CREATE_URL = f"{KENTIK_API_BASE_URL}/interface/v202108alpha1/interfaces"

# The path to the JSON file created by Telegraf.
TELEGRAF_INTERFACE_DATA = "/var/log/telegraf/interface_metrics.json"
TELEGRAF_IP_ADDRESS_DATA = "/var/log/telegraf/ip_address_metrics.json"

# ==============================================================================
# Helper Functions
# ==============================================================================

def get_headers():
    """
    Constructs the HTTP headers for authenticating with the Kentik API.
    """
    if not KENTIK_API_EMAIL or not KENTIK_API_TOKEN:
        raise ValueError("Environment variables for Kentik API are not set.")

    return {
        "Content-Type": "application/json",
        "X-CH-Auth-Email": KENTIK_API_EMAIL,
        "X-CH-Auth-API-Token": KENTIK_API_TOKEN
    }

def get_device_interfaces(device_id):
    """
    Gathers a list of interfaces for a particular device.
    An error is logged if a device does not exist. 
    """
    print(f"Gathering the interfaces for device: {device_id}")
    url = f"{KENTIK_API_CREATE_URL}?filters.deviceIds={int(device_id)}"
    print(url)
    response = send_request('GET', url, None)
    interface_dict = response.json()
    dict_item = {}
    for item in interface_dict['interfaces']:
        dict_item.update({item['interfaceDescription']: item['id']})
    return dict_item

def build_consolidated_list():
    """
    Takes the two telegraf files and performs a single pass on them to consolidate
    the data into one dictionary for all devices and interfaces.
    """
    print("Reading in the two telegraf data files and merging them into one list...")
    consolidated_list = []
    consolidated_dict = {}

    with open(TELEGRAF_INTERFACE_DATA, "r") as file:
        lines = file.readlines()
        # Filter out blank lines and join with a comma
        valid_lines = [line.strip() for line in lines if line.strip()]
        fixed_json_string = "[" + ",".join(valid_lines) + "]"

        # Load the fixed string as a single JSON array
        interface_data = json.loads(fixed_json_string)

    with open(TELEGRAF_IP_ADDRESS_DATA, "r") as file:
        lines = file.readlines()
        # Filter out blank lines and join with a comma
        valid_lines = [line.strip() for line in lines if line.strip()]
        fixed_json_string = "[" + ",".join(valid_lines) + "]"

        # Load the fixed string as a single JSON array
        ip_address_data = json.loads(fixed_json_string)
    
    
    # Add the interface indexes to the dictionary items. 
    for item in interface_data:
        consolidated_dict = {}
        device_name = item.get('tags', {}).get('device_name', 'unknown')
        device_id = item.get('tags', {}).get('device_id', 'unknown')
        if device_name not in consolidated_dict.get('device_name', {}):
            consolidated_dict[device_name] = {}
            consolidated_dict[device_name]['device_id'] = device_id
            consolidated_dict[device_name]['interfaces'] = {}
            for item in interface_data:
                if item.get('tags', {}).get('device_name', 'unknown') == device_name:
                    ifindex = item.get('tags', {}).get('ifindex', 'unknown')
                    description = item.get('tags', {}).get('description', 'empty')
                    consolidated_dict[device_name]['interfaces'][ifindex] = {}
                    consolidated_dict[device_name]['interfaces'][ifindex]['deviceId'] = item['tags']['device_id']
                    consolidated_dict[device_name]['interfaces'][ifindex]['snmpId'] = item['tags']['ifindex']
                    consolidated_dict[device_name]['interfaces'][ifindex]['snmpSpeed'] = int(item['tags']['speed'])
                    consolidated_dict[device_name]['interfaces'][ifindex]['snmpType'] = int(item['tags']['type'])
                    consolidated_dict[device_name]['interfaces'][ifindex]['snmpAlias'] = description
                    consolidated_dict[device_name]['interfaces'][ifindex]['interfaceDescription'] = item['tags']['ifDescr']
            for item in ip_address_data:
                if item.get('tags', {}).get('device_name', 'unknown') == device_name:
                    consolidated_dict[device_name]['interfaces'][ifindex]['interfaceIp'] = item['tags']['ip']
                    consolidated_dict[device_name]['interfaces'][ifindex]['interfaceIpNetmask'] = item['tags']['netmask']
        consolidated_list.append(consolidated_dict)
    #print(consolidated_list)
    print("List merge complete...")

    return consolidated_list

def send_request(method, url, data):
    """
    Sends an HTTP request with exponential backoff for retries.
    """
    headers = get_headers()
    max_retries = 5
    delay = 1  # seconds

    for i in range(max_retries):
        try:
            response = requests.request(method, url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            print(f"[{method}] Request to {url} successful.")
            return response
        except requests.exceptions.HTTPError as e:
            print(f"[{method}] HTTP Error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code in [401, 403]:
                print("Authentication failed. Exiting.")
                return None
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2
    
    print("Max retries exceeded. Request failed.")
    return response.text

# ==============================================================================
# Main Execution
# ==============================================================================

if __name__ == "__main__":
    if not os.path.exists(TELEGRAF_INTERFACE_DATA):
        print(f"Error: Telegraf output file not found at {TELEGRAF_INTERFACE_DATA}")
        exit(1)

    if not os.path.exists(TELEGRAF_IP_ADDRESS_DATA):
        print(f"Error: Telegraf output file not found at {TELEGRAF_IP_ADDRESS_DATA}")
        exit(1)
    
    # Build a merge list of the telegraf data.
    telegraf_interface_data = build_consolidated_list()
    #print(telegraf_interface_data)
    for device in telegraf_interface_data:
        for device_name in device:
            print(f"Creating interfaces for device: {device_name}")
            kentik_interface_list = get_device_interfaces(device[device_name]['device_id'])
            print(kentik_interface_list)
            for interface in device[device_name]['interfaces']:
                interface_payload = {}
                interface_payload['interface'] = device[device_name]['interfaces'][interface]
                print(interface_payload)
                if device[device_name]['interfaces'][interface]['interfaceDescription'] in kentik_interface_list:
                    print(f"Interface {device[device_name]['interfaces'][interface]['interfaceDescription']} exist, updating...")
                    interface_payload['interface']['id'] = kentik_interface_list[device[device_name]['interfaces'][interface]['interfaceDescription']]
                    send_request('PUT', f"{KENTIK_API_CREATE_URL}/{int(interface_payload['interface']['id'])}", interface_payload)
                else:
                    print(f"Interface {device[device_name]['interfaces'][interface]['interfaceDescription']} does not exist, creating...")
                    send_request('POST', KENTIK_API_CREATE_URL, interface_payload)

    print("Script finished.")