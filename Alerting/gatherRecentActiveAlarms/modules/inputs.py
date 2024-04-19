def startTime():
    print('--------------')
    print('Setting Timers...')
    print('--------------')
    # SET TIMER
    seconds_back = 28800

    return seconds_back

def filterParameters():
    print('--------------')
    print('Gathering Filter Parameters...')
    print('--------------')
    param_list = []
    # SET PARAMATERS
    '''
    States:
    0 = noneState
    1 = clear
    2 = alarm
    3 = ackReq
    4 = alarm and ackReq
    5 = All (no filter)
    '''
    state = 1
    '''
    excludeSubpolicies
    0 = False (default) = alarms are included
    1 = True
    '''
    excludeSubpolicies = 0

    '''
    ignores synthetics alerts
    ignorePolicyNamePrefixes: ['V4 Synth']
    0 = False (default)
    1 = True
    '''
    ignorePolicyNamePrefixes = 1

    # CODE BELOW

    if state == 0:
        param_list.append("states=noneState")
    elif state == 1:
        param_list.append("states=clear")
    elif state == 2:
        param_list.append("states=alarm")
    elif state == 3:
        param_list.append("states=ackReq")
    elif state == 4:
        param_list.append("states=alarm&states=ackReq")

    if excludeSubpolicies != 0:
        param_list.append("excludeSubpolicies=True")
    
    if ignorePolicyNamePrefixes != 0:
        param_list.append("ignorePolicyNamePrefixes=V4%20Synth")
    
    params = '&'.join(param_list)

    return params








