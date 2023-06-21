# MODULE FOR CREATING PRINT STRUCTURES FOR THE API DATA, TO ADD DIFFERENT PRINTING STRUCTURES, ADD ADDITIONAL FUNCTIONS.
def printStructured(response_dict):
    print(f"PAGETOKEN: {response_dict['pageToken']}")
    print('--------------')
    print('TOTALS')
    print(response_dict['totals'])
    print('--------------')
    print('POLICY DETAILS')
    for item in response_dict['policyIDToDetails']:
        print(response_dict['policyIDToDetails'][item])
        print('---')
    print('--------------')
    print('THRESHOLD DETAILS')
    for item in response_dict['thresholdIDToDetails']:
        print(response_dict['thresholdIDToDetails'][item])
        print('---')
    print('--------------')
    print('ALARMS')
    for alarm in response_dict['alarms']:
        print(alarm)
        print('---')
    print(f"COUNT: {response_dict['count']} Alarms")
    print('--------------')