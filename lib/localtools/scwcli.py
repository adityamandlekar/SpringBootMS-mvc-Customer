import string
import time

from utils.local import _run_local_command
from VenueVariables import *

def get_master_box_ip(che_ip_list):
    """ To find the master box from pair boxes

        Argument : che_ip_list - IP list of the TD boxes

        Return :   the ip of master box
        
        Examples :
        | ${iplist} | create list | ${CHE_A_IP} | ${CHE_B_IP} |
        | ${master_ip} | get master box ip | ${iplist} |
    """
    for che_ip in che_ip_list:
        cmd ='-state -ip %s -port %s -user %s -pass %s'%(che_ip,SCWCLI_PORT,USERNAME,PASSWORD)
        stdout = _run_local_SCWCLI(cmd)
        if (stdout.find('SCW state MASTER') != -1):
            return che_ip
    raise AssertionError('*ERROR* cannot find a master box')

def get_QOS_value(node, QOSName, che_ip):
    """ get QOS value via watchdog

        Argument : node - A,B,C,D
                   QOSName - the QOS name you want to check, should be "IngressNIC", "EgressNIC", "FMSNIC" etc
                   che_ip - IP of the master TD box
        Return :   QOS value returned from watchdog
        
        Examples :
        | get QOS equal | A | IngressNIC | ${CHE_IP} |
    """
    cmd ='-entity %s -ip %s -port %s -user %s -pass %s'%(MTE, che_ip, SCWCLI_PORT, USERNAME, PASSWORD)
    stdout = _run_local_SCWCLI(cmd)
    for line in stdout.split('\n'):
        if (line.find(QOSName) != -1):
            items = line.split('|')
            if (items[1].strip() != QOSName):
                raise AssertionError('*ERROR* QOSName %s is not correct' %QOSName)

            if (node == 'A'):
                actualQOSValue = items[3].strip()
            elif (node == 'B'):
                actualQOSValue = items[4].strip()
            elif (node == 'C'):
                actualQOSValue = items[5].strip()
            elif (node == 'D'):
                actualQOSValue = items[6].strip()
            else:
                raise AssertionError('*ERROR* node is %s, it must be A, B, C or D' %node)
            return actualQOSValue
    raise AssertionError('*ERROR* Cannot find the specific QOS Name %s' %QOSName)

def get_SyncPulseMissed(master_ip, waittime=5, timeout=30):
    """ get sync pulse missing count through SCWCli

        Argument : master_ip - IP of the master SCW box
                   waittime - specifies the time to wait between checks, in seconds.
                   timeout - specifies the maximum time to wait, in seconds.
                         
        Return : a list with sync pulse missing count for both instance A instance B i.e. [A-instance-missing-count, B-instance-missing-count]
        
        Examples :
        |get SyncPulseMissed |${CHE_A_IP} | 
    """
            
    cmd = '-ip %s -port %s -user %s -pass %s -entity %s'%(master_ip,SCWCLI_PORT,USERNAME,PASSWORD,MTE)
    ret = _run_local_SCWCLI(cmd).splitlines()
    timeout = int(timeout)
    waittime = int(waittime)
    maxtime = time.time() + float(timeout)
    while time.time() <= maxtime:
        ret = _run_local_SCWCLI(cmd).splitlines()
        for line in ret:
            if (line.find('SyncPulseMissed') != -1):
                contents = line.split('|')
                if (len(contents) >= 5):
                    # make sure the fields are not empty,
                    # it may take a few seconds after restart for sync pulse info to be available
                    Acount = contents[3].strip()
                    Bcount = contents[4].strip()
                    if Acount.isdigit() and Bcount.isdigit():
                        return [int(Acount), int(Bcount)]
                else:
                    raise AssertionError('*ERROR* (%s) not match with expected format |SyncPulseMissed   |ID | A sync pulse | B sync pulse | | |'%(line))
        time.sleep(waittime)
    raise AssertionError('*ERROR* No SyncPulseMissed Information found')

def switch_MTE_LIVE_STANDBY_status(node,status,che_ip):
    """ To switch specific MTE instance to LIVE, STANDBY, LOCK_LIVE or LOCK_STANDY. Or unlock the MTE instance.

        Argument : node - A,B,C,D
                   status - LIVE:Switch to Live, STANDBY:Switch to Standby, 
                            LOCK_LIVE to lock live, LOCK_STANDY to lock standby, UNLOCK to unlock the MTE
                   che_ip - IP of the TD box
                         
        Return :
        
        Examples :
        |switch MTE LIVE STANDBY status | A | ${CHE_A_IP} | 
    """
   
    if (status == 'LIVE'):
        cmd = "-promote "
    elif (status == 'STANDBY'):
        cmd = "-demote "
    elif (status == 'LOCK_LIVE'):
        cmd = "-lock_live "
    elif (status == 'LOCK_STANDBY'):
        cmd = "-lock_stby "
    elif (status == 'UNLOCK'):
        cmd = "-unlock "
    else:
        raise AssertionError('*ERROR* Unknown status %s' %status)
        
    cmd = cmd + '%s %s -ip %s -port %s -user %s -pass %s'%(MTE,node,che_ip,SCWCLI_PORT,USERNAME,PASSWORD)
    _run_local_SCWCLI(cmd)

def verify_QOS_equal_to_specific_value(node, QOSName, QOSValue, che_ip):
    """ verify QOS is equal to the specific value

        Argument : node - A,B,C,D
                   QOSName - the QOS name you want to check, should be "IngressNIC", "EgressNIC", "FMSNIC" etc
                   QOSValue - the specific QOS value, 100 or 50 or 0
                   che_ip - IP of the TD box
        Return :   None
        
        Examples :
        | verify QOS equal to specific value | A | IngressNIC | 100 | ${CHE_IP} |
    """
    actualQOSValue = get_QOS_value(node, QOSName, che_ip)
    if (int(actualQOSValue) != int(QOSValue)):
        raise AssertionError('*ERROR* QOS %s on %s is %s, is not equal to %s' %(QOSName,node,actualQOSValue,QOSValue))

def verify_sync_pulse_missed_Qos(syncPulseBefore,syncPulseAfter):
    """ To verify if sync pulse missing count has increased after port has been blocked

        Argument : SyncPulseMissed - list of sync pulse missing count before port blocked
                   syncPulseAfter - list of sync pulse missing count after port blocked
                         
        Return :
        
        Examples :
        |verify sync pulse missed Qos |[0,0]|[0,100]| 
    """
            
    if (syncPulseAfter[0] > 0):
        if ((syncPulseAfter[0] - syncPulseBefore[0]) <= 0):
            raise AssertionError('*ERROR* Sync Pulse Missed Count has not increased after port blocked (before : %d, after : %d)' %(syncPulseBefore[0], syncPulseAfter[0]))
    else:
        if ((syncPulseAfter[1] - syncPulseBefore[1]) <= 0):
            raise AssertionError('*ERROR* Sync Pulse Missed Count has not increased after port blocked (before : %d, after : %d)' %(syncPulseBefore[1], syncPulseAfter[1]))

def wait_for_QOS(node, QOSName, QOSValue, che_ip, waittime=10, timeout=100):
    """ wait the QOS until it is changed to the specific value, break the wait after timeout.

        Argument : node - A,B,C,D
                   QOSName - the QOS name you want to check, should be "IngressNIC", "EgressNIC", "FMSNIC" etc
                   QOSValue - the specific QOS value, 100 or 50 or 0
                   che_ip - IP of the master TD box
                   waittime - specifies the time to wait between checks, in seconds.
                   timeout - specifies the maximum time to wait, in seconds.
        Return :   None
        
        Examples :
        | wait for QOS | A | IngressNIC | 100 | ${CHE_IP} |
    """
    timeout = int(timeout)
    waittime = int(waittime)
    maxtime = time.time() + float(timeout)
    while time.time() <= maxtime:
        time.sleep(waittime)
        actualQOSValue = get_QOS_value(node, QOSName, che_ip)
        if (int(actualQOSValue) == int(QOSValue)):
            return
    raise AssertionError('*ERROR* QOS %s on %s is %s did not change to %s before timeout %ds' %(QOSName,node,actualQOSValue,QOSValue,timeout))

def _run_local_SCWCLI(cmd):
    """ Run SCWCli at Slave

        Argument : cmd - input parameters for SCWCLi.exe
                   
        Return :
        
        Examples :
        |${ret}| run local SCWCLI | -demote HKF02M A -ip 10.32.15.187 -port 27000 -user root -pass xxxxxx |
    """
    
    cmd = 'SCWCLi.exe %s'%cmd
    print cmd

    rc,stdout,stderr  = _run_local_command(cmd, True, LOCAL_SCWCLI_BIN)
    if rc != 0:
        raise AssertionError('*ERROR* in running SCWLLi.exe %s' %stderr)  
    
    return stdout
