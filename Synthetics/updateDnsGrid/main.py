
import modules.auth as auth
import requests
import yaml
from pprint import pprint
import json
import sys

def gather_parameters():
    print("Gathering user parameters...")


def collect_current_test(test_name):
    print(f"Connecting to the Kentik API, looking for {test_name}...")
    url = "https://grpc.api.kentik.com/synthetics/v202309/tests"
    payload = {}
    headers = {
        'X-CH-Auth-Email': auth.username,
        'X-CH-Auth-API-Token': auth.apikey
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    test_data = response.json()


    for test in test_data['tests']:
        if test['name'] == test_name:
            return test['id']

    raise ValueError(f"Test Name, {test_name}, Not Found")

def gather_current_test_config(test_id):
    url = f"https://grpc.api.kentik.com/synthetics/v202309/tests/{test_id}"
    payload = {}
    headers = {
        'X-CH-Auth-Email': auth.username,
        'X-CH-Auth-API-Token': auth.apikey
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    test_data = response.json()

    del test_data['test']["createdBy"]
    del test_data['test']["cdate"]
    del test_data['test']["edate"]

    return test_data

def update_dns_grid(test_id,ip_list,test_data):
    test_data["test"]["settings"]["dnsGrid"]["servers"] = ip_list
    url = f"https://grpc.api.kentik.com/synthetics/v202309/tests/{test_id}"
    headers = {
        'X-CH-Auth-Email': auth.username,
        'X-CH-Auth-API-Token': auth.apikey
    }

    payload = json.dumps(test_data)

    response = requests.request("PUT", url, headers=headers, data=payload)

    print(response.status_code)

 
def main():
    print("Main Function")
    if len(sys.argv) == 2:
        file_name = sys.argv[1]
    else:
        sys.exit("ERROR: No Configuration File Included...")
    with open(file_name, 'r') as file: 
        config = yaml.safe_load(file)
        ip_list = config['ip_list']
        test_name = config['test_name']
    test_id = collect_current_test(test_name)
    test_data = gather_current_test_config(test_id)
    update_dns_grid(test_id,ip_list,test_data)


if __name__ == "__main__":
    main()