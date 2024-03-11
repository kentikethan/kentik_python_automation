'''
Program Name: ElastisearchIndexToKentik
Product: Kentik
Author: Ethan Angele
Description: This program connects to an ElastiSearch index for IP inventory data and adds those attributes to Kentik as Custom Dimensions.
Requirements:  Edit the program structure document to define what will be the value (name of the populator), the two dimension IDs (src and dst)
             and the IP field to match. Create either a unique copy of this program for each custom dimension or edit the program to handle multiple input files.
'''

# IMPORTED MODULES
import requests
import json
import modules.auth as auth
import modules.elastisearchToJson as elastisearchJson
import modules.inputs as inputs
import modules.outputs as outputs
from jinja2 import Template, Environment, FileSystemLoader

def main():
    print('Main function')
    json_file = open("./elastisearch.json")
    json_vars = json.load(json_file)
    template_loader = FileSystemLoader(searchpath="./")
    template_env = Environment(loader=template_loader)
    src_template = template_env.get_template("./templates/kentik_cd_src_template.j2")
    request_body = src_template.render(elastisearch=json_vars)
    return request_body

def kentik_api(request_body):
    print("Connecting to the Kentik API ...")
    kentik_inputs = inputs.srcCustomDimensionName()
    src_cd_name = kentik_inputs[0]
    kentik_url = f"https://api.kentik.com/api/v5/batch/customdimensions/{src_cd_name}/populators"
    payload = request_body
    headers = {
    'X-CH-Auth-Email': auth.username,
    'X-CH-Auth-API-Token': auth.apikey,
    'Content-Type': 'application/json'
    }
    #print(payload)
    response = requests.request("POST", kentik_url, headers=headers, data=payload)
    print(response.text)
    

if __name__ == "__main__":
    request_body = main()
    kentik_api(request_body)


    