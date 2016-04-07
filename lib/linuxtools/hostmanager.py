import time
import string

from utilpath import utilpath
from utils.ssh import _exec_command

from VenueVariables import *

MTESTATE = {'0': 'UNDEFINED', '1': 'LIVE', '2': 'STANDBY', '3' : 'LOCKED_LIVE', '4' : 'LOCKED_STANDBY'};

def run_HostManger(*optArgs):
    """run HostManager with specific arguments
    
    optArgs    : argument that used to run HostManager
    Returns    : stdout of after the command has executed 

    Examples:
    | run HostManager  | -readparams /HKF02M/LiveStandby|
    """         
    cmd = '%s ' %utilpath.HOSTMANAGER
    cmd = cmd + ' ' + ' '.join( map(str, optArgs))
    print '*INFO* ' + cmd
    stdout, stderr, rc = _exec_command(cmd)
            
    if rc != 0:
        raise AssertionError('*ERROR* %s' %stderr)    
    
    return stdout

def Get_MTE_state():
    """check MTE state (UNDEFINED,LIVE,STANDBY,LOCKED_LIVE,LOCKED_STANDBY) through HostManger
    
     Argument:
                
    Returns    :  either 'UNDEFINED' or 'LIVE' or 'STANDBY' or 'LOCKED_LIVE' or 'LOCKED_STANDBY'

    Examples:
    | check MTE state | HKF02M
    """           
    
    cmd = '-readparams /%s/LiveStandby'%MTE
    ret = run_HostManger(cmd).splitlines()
    if (len(ret) == 0):
        raise AssertionError('*ERROR* Running HostManger %s return empty response'%cmd)
    
    idx = '-1'
    for line in ret:
        if (line.find('LiveStandby') != -1):
            contents = line.split(' ')
            idx = contents[-1].strip()
    
    if (idx == '-1'):
        raise AssertionError('*ERROR* Keyword LiveStandby was not found in response')
    elif not (MTESTATE.has_key(idx)):
        raise AssertionError('*ERROR* Unknown state %s found in response'%idx)
    
    return MTESTATE[idx]  

def verify_MTE_state(state, waittime=5, timeout=150):
    """Verify MTE instance is in specific state.
    State change is not instantaneous, so loop and check up to timeout seconds.
    
     Argument:
        state    : expected state of MTE (UNDEFINED,LIVE,STANDBY,LOCKED_LIVE,LOCKED_STANDBY)
        waittime : specifies the time to wait between checks, in seconds.
        timeout  : specifies the maximum time to wait, in seconds.
    
    Returns    : 

    Examples:
    | verify MTE state | LIVE |
    """             
    # convert  unicode to int (it is unicode if it came from the Robot test)
    timeout = int(timeout)
    waittime = int(waittime)
    maxtime = time.time() + float(timeout)

    #verify if input 'state' is a valid one
    if not (state in MTESTATE.values()):
        raise AssertionError('*ERROR* Invalid input (%s). Valid value for state is UNDEFINED , LIVE , STANDBY , LOCKED_LIVE , LOCKED_STANDBY '%state)
    
    cmd = '-readparams /%s/LiveStandby'%MTE
    while time.time() <= maxtime:
        ret = run_HostManger(cmd).splitlines()
        if (len(ret) == 0):
            raise AssertionError('*ERROR* Running HostManger %s return empty response'%cmd)
     
        idx = '-1'
        for line in ret:
            if (line.find('LiveStandby') != -1):
                contents = line.split(' ')
                idx = contents[-1].strip()
                 
        if (idx == '-1'):
            raise AssertionError('*ERROR* Keyword LiveStandby was not found in response')
        elif not (MTESTATE.has_key(idx)):
            raise AssertionError('*ERROR* Unknown state %s found in response'%idx)
        elif (MTESTATE[idx] == state):
            return
        time.sleep(waittime)
    raise AssertionError('*ERROR* %s is not at state %s (current state : %s, timeout : %ds)'%(MTE,state,MTESTATE[idx],timeout))            
    