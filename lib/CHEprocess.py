﻿from datetime import date, datetime, timedelta
import time
import string

from LinuxCoreUtilities import LinuxCoreUtilities
import logfiles
from utilpath import utilpath
from utils.ssh import _exec_command

from VenueVariables import *

def run_commander(application, command):
    """Runs the Commander tool to execute the specified CHE command.

    Returns the stdout from the executed command.

    Examples:
    | Run Commander  | process      | start ${mte}      |
    | Run Commander  | linehandler  | dumpcache ${mte}  |
    """
    cmd = r'%s -n %s -c "%s"' %(utilpath.COMMANDER,application,command)
    stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr)
    if rc !=0 or stderr !='' or stdout.lower().find('failed') != -1:
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    print '*INFO* cmd=%s, %s'%(cmd,stdout)
    return stdout

def rollover_MTE_start_date(GMTStartTime):   
    """Change the MTE machine date to a few seconds before the next StartOfDay time.
    If current time <  specified time, change to specified time today.
    If current time >= specified time, change to specified time tomorrow.
    Waits for start of day instrument update to complete.
            
    Argument:         
                GMTStartTime     : StartOfDay GMT time with format HH:MM.
  
    return nil
    
    Examples:
               | Rollover MTE Start Date  |  09:00 |
    """  

    secondsBeforeStartTime = timedelta(seconds = 5)
    aDay = timedelta(days = 1 )
    currTimeArray = LinuxCoreUtilities().get_date_and_time() # current time as array of strings
    C = map(int,currTimeArray) # current time as array of INTs
    T = map(int,GMTStartTime.split(':')) #start time as array of INTs
    
    currDateTime = datetime(*C) # current time as dateTime object
    newDateTime = datetime(C[0],C[1],C[2],T[0],T[1]) - secondsBeforeStartTime
        
    if currDateTime >= newDateTime:
        newDateTime += aDay

    LinuxCoreUtilities().set_date_and_time(newDateTime.year, newDateTime.month, newDateTime.day, newDateTime.hour, newDateTime.minute, newDateTime.second)
    currTimeArray = newDateTime.strftime('%Y,%m,%d,%H,%M,%S').split(',')
    logfiles.wait_smf_log_message_after_time('%s.*StartOfDay time occurred' %MTE, currTimeArray)
    logfiles.wait_smf_log_does_not_contain('dropped due to expiration' , waittime=5, timeout=300)
    logfiles.wait_smf_log_message_after_time('%s.*handleStartOfDayInstrumentUpdate.*Ending' %MTE, currTimeArray)

def rollover_MTE_time(GMTSysTime):
    """Change the MTE machine date to a few seconds before the configured time.
               
    Argument:         
                GMTSysTime     : GMT time with format HH:MM.
  
    Return: the set time array like ['2016', '11', '02', '08', '59', '55']
    
    Examples:
        | Rollover MTE time  | 2016-11-02 09:00 |
    """ 
    secondsBeforeStartTime = timedelta(seconds = 5)
    newDateTime = datetime(int(GMTSysTime[0:4]),int(GMTSysTime[5:7]),int(GMTSysTime[8:10]),int(GMTSysTime[11:13]),int(GMTSysTime[14:16])) - secondsBeforeStartTime

    LinuxCoreUtilities().set_date_and_time(newDateTime.year, newDateTime.month, newDateTime.day, newDateTime.hour, newDateTime.minute, newDateTime.second)
    currTimeArray = newDateTime.strftime('%Y,%m,%d,%H,%M,%S').split(',')
    return currTimeArray

def Rollover_Time_Check_SMF_log(AllTimesDict):
    """Change the MTE machine date to a few seconds before the configured time.
               
    Argument:
        AllTimesDict : Dictionary which the time is the key, value is list of the config names like
    {'2016-12-06 12:00:00': [u'StartOfDayTime'], '2016-12-07 03:30:00': [u'EndOfDayTime'], '2016-12-06 05:00:00': [u'RolloverTime', u'CacheRolloverTime', u'JnlRollTime', u'CacheRollover']}
    Normally returned by Get_future_config_times.
    
    Return: no
    
    Examples:
        | Rollover time check smf log | ${allTimesDict} |
    """ 
    sortList = AllTimesDict.keys()
    sortList.sort()
    for timepoint in sortList:
        currTimeArray = rollover_MTE_time(timepoint)
        for eventname in AllTimesDict[timepoint]:
            logfiles.check_logfile_for_event(eventname, currTimeArray)

def start_smf():
    """Start the Server Management Foundation process.

    This keyword is normally invoked only in the test suite setup via the suite_setup keyword.
    
    Does not return a value.

    Example:
    | Start SMF  |
    """
    cmd = 'service smf status'
    stdout, stderr, rc = _exec_command(cmd)
    if rc != 3: # rc==3 means SMF is not running
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        print '*INFO* %s' %stdout
        return 0
    cmd = 'service smf start'
    stdout, stderr, rc = _exec_command(cmd)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    print '*INFO* %s' %stdout
        
def stop_smf(waittime=30, timeout=600):
    """Stop the Server Management Foundation process.
    Does not return a value.

    Example:
    | Stop SMF  |
    """
    cmd = 'service smf status'
    stdout, stderr, rc = _exec_command(cmd)
    print '*INFO* %s' %stdout
    if rc == 3: # rc==3 means SMF is not running
        return 0
    print '*INFO* Stopping SMF'
    cmd = 'service smf stop'
    stdout, stderr, rc = _exec_command(cmd)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    
    #The smf stop may return before everything is stopped.  Make sure it is fully stopped.
    timeout = int(timeout)
    waittime = int(waittime)
    maxtime = time.time() + float(timeout)
    cmd = 'service smf status'
    while time.time() <= maxtime:
        stdout, stderr, rc = _exec_command(cmd)
        if rc == 3: # rc==3 means SMF is not running
            print '*INFO* %s' %stdout
            return 0
        time.sleep(waittime)
    raise AssertionError('*ERROR* Stop SMF did not complete within %s seconds' %(timeout))

def wait_for_process_to_exist(pattern, waittime=2, timeout=60):
    """Wait until a process matching the specified pattern exists.

    Argument pattern is the pattern to search for in the full process command line.
    Argument 'waittime' specifies the time to wait between checks, in seconds.
    Argument 'timeout' specifies the maximum time to wait, in seconds.
    
    Does not return a value; raises an error if the process does not exist within timeout seconds.

    Examples:
    | Wait for process to exist  | MTE -c MFDS1M  |
    """
    # convert  unicode to int (it is unicode if it came from the Robot test)
    timeout = int(timeout)
    waittime = int(waittime)
    maxtime = time.time() + float(timeout)
    
    while time.time() <= maxtime:
        result = LinuxCoreUtilities().find_processes_by_pattern(pattern)
#             print '*DEBUG* result=%s' %result
        if len(result) > 0:
            return
        time.sleep(waittime)
    raise AssertionError("*ERROR* Process matching pattern '%s' does not exist (timeout %ds)" %(pattern,timeout))

def wait_for_process_to_not_exist(pattern, waittime=2, timeout=60):
    """Wait until no process matching the specified pattern exists.

    Argument pattern is the pattern to search for in the full process command line.
    Argument 'waittime' specifies the time to wait between checks, in seconds.
    Argument 'timeout' specifies the maximum time to wait, in seconds.
    
    Does not return a value; raises an error if the process still exists after timeout seconds.

    Examples:
    | Wait for process to not exist  | MTE -c MFDS1M  |
    """
    # convert  unicode to int (it is unicode if it came from the Robot test)
    timeout = int(timeout)
    waittime = int(waittime)
    maxtime = time.time() + float(timeout)
    
    while time.time() <= maxtime:
        result = LinuxCoreUtilities().find_processes_by_pattern(pattern)
#             print '*DEBUG* result=%s' %result
        if len(result) == 0:
            return
        time.sleep(waittime)
    raise AssertionError("*ERROR* Process matching pattern '%s' still exists (timeout %ds)" %(pattern,timeout))
