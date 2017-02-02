import time

from LinuxCoreUtilities import LinuxCoreUtilities
from LinuxFSUtilities import LinuxFSUtilities
from utils.ssh import _exec_command

from VenueVariables import *

SMFLOGDIR = BASE_DIR + '/smf/log/'

def wait_GMI_message_after_time(message, timeRef, isCaseSensitive=False, waittime=2, timeout=60):
    """Wait until the EventLogAdapterGMILog file contains the specified message with a timestamp newer than the specified reference time
    NOTE: This does not yet handle log file rollover at midnight

    Argument :
        message : target message in grep format to find in smf log
        timeRef : UTC time message must be after. It is a list of values as returned by the get_date_and_time Keyword [year, month, day, hour, min, second]
        isCaseSensitive : flag indicates if search message is case sensitive.
        waittime : specifies the time to wait between checks, in seconds.
        timeout : specifies the maximum time to wait, in seconds.
    
    Return : Nil if success or raise error

    Examples:
    | wait GMI message after time | FMS REORG DONE | ${dt} |
    """
    refDate = '%s-%s-%s' %(timeRef[0], timeRef[1], timeRef[2])
    refTime = '%s:%s:%s' %(timeRef[3], timeRef[4], timeRef[5])
    currentFile = '%s/EventLogAdapterGMILog.txt' %(SMFLOGDIR)

    # convert  unicode to int (it is unicode if it came from the Robot test)
    timeout = int(timeout)
    waittime = int(waittime)
    maxtime = time.time() + float(timeout)
    while time.time() <= maxtime:            
        retMessages = LinuxFSUtilities().grep_remote_file(currentFile, message, isCaseSensitive=isCaseSensitive)
        if (len(retMessages) > 0):
            logContents = retMessages[-1].split('|')
            if (len(logContents) >= 2):
                logDateTime = logContents[0].split('T')
                if (len(logDateTime) >= 2):
                    if logDateTime[0].strip() >= refDate and logDateTime[1].strip() >= refTime:
                        return
        time.sleep(waittime)
    raise AssertionError('*ERROR* Fail to get pattern \'%s\' from smfGMI log before timeout %ds' %(message, timeout)) 

def wait_smf_log_does_not_contain(message, isCaseSensitive=False, waittime=2, timeout=60):
    """Wait until the SMF log file does not contain the specified message within the last 'waittime' interval

    Argument :
        message : target message in grep format to find in smf log
        isCaseSensitive : flag indicates if search message is case sensitive.
        waittime : specifies the time to wait between checks, in seconds.
        timeout : specifies the maximum time to wait, in seconds.
    
    Return : Nil if success or raise error

    Example:
    | wait smf log does not contain | Drop message sent for |
    """

    dt = LinuxCoreUtilities().get_date_and_time()
    
    # convert  unicode to int (it is unicode if it came from the Robot test)
    timeout = int(timeout)
    waittime = int(waittime)
    maxtime = time.time() + float(timeout)
    while time.time() <= maxtime:
        time.sleep(waittime)
        refDate = '%s-%s-%s' %(dt[0], dt[1], dt[2])
        refTime = '%s:%s:%s' %(dt[3], dt[4], dt[5])
        currentFile = '%s/smf-log-files.%s%s%s.txt' %(SMFLOGDIR, dt[0], dt[1], dt[2])
        if isCaseSensitive:
            cmd = "grep '%s' %s | tail --lines=1" %(message, currentFile)
        else:
            cmd = "grep -i '%s' %s | tail --lines=1" %(message, currentFile)
        stdout, stderr, rc = _exec_command(cmd)
        retMessage = stdout.split(';')
        if (len(retMessage) < 2):
            return
        else:
            if retMessage[0].strip() <= refDate and retMessage[1].strip() <= refTime:
                return
        dt = LinuxCoreUtilities().get_date_and_time()
    raise AssertionError('*ERROR* SMF log still contains pattern \'%s\' after timeout %ds' %(message, timeout))    

def wait_smf_log_message_after_time(message, timeRef, isCaseSensitive=False, waittime=2, timeout=60):
    """Wait until the SMF log file contains the specified message with a timestamp newer than the specified reference time
    NOTE: This does not yet handle log file rollover at midnight

    Argument :
        message : target message in grep format to find in smf log
        timeRef : UTC time message must be after. It is a list of values as returned by the get_date_and_time Keyword [year, month, day, hour, min, second]
        isCaseSensitive : flag indicates if search message is case sensitive.
        waittime : specifies the time to wait between checks, in seconds.
        timeout : specifies the maximum time to wait, in seconds.
    
    Return : the timestamp of the message found if success, or raise error

    Examples:
    | ${dt}= | get date and time |
    | ${logMsgTimestamp}= | wait smf log message after time | FMS REORG DONE | ${dt} |
    """

    retLogTimestamp = None
    refDate = '%s-%s-%s' %(timeRef[0], timeRef[1], timeRef[2])
    refTime = '%s:%s:%s' %(timeRef[3], timeRef[4], timeRef[5])
#         print 'DEBUG refDate %s, refTime %s' %(refDate,refTime)
    dt = LinuxCoreUtilities().get_date_and_time()
    currentFile = '%s/smf-log-files.%s%s%s.txt' %(SMFLOGDIR, dt[0], dt[1], dt[2])
#         print 'DEBUG checking SMF log file %s' %currentFile

    # convert  unicode to int (it is unicode if it came from the Robot test)
    timeout = int(timeout)
    waittime = int(waittime)
    maxtime = time.time() + float(timeout)
    while time.time() <= maxtime:
        retMessages = LinuxFSUtilities().grep_remote_file(currentFile, message, isCaseSensitive=isCaseSensitive)
#             print 'DEBUG retMessages: %s' %retMessages
        if (len(retMessages) > 0):
            logContents = retMessages[-1].split(';')
            if (len(logContents) >= 2):
                if logContents[0].strip() >= refDate and logContents[1].strip() >= refTime:
                    retLogTimestamp = logContents[0].strip() + ' ' + logContents[1].strip()
                    return retLogTimestamp
        time.sleep(waittime)
    raise AssertionError('*ERROR* Fail to get pattern \'%s\' from smf log before timeout %ds' %(message, timeout))

def wait_for_persist_load_to_start(timeout=60):
    """Wait for the MTE/FTE to begin loading from the PERSIST file.
    Argument:
    timeout : the maximum time to wait, in seconds
    
    1. This is not a generic function to search for a message from the log file.
    2. Using read_until() or read_until_regexp() is problematic if there is a lot of output
    3. To restrict the amount of output the routine grep's for only lines containing 'Persistence'
    """
    dt = LinuxCoreUtilities().get_date_and_time()
    currentFile = '%s/smf-log-files.%s%s%s.txt' %(SMFLOGDIR, dt[0], dt[1], dt[2])
    orig_timeout = G_SSHInstance.get_connection().timeout
    G_SSHInstance.set_client_configuration(timeout='%s seconds' %timeout)
    G_SSHInstance.write('tail --lines=0 -f %s | grep Persistence' %currentFile)
    G_SSHInstance.read_until_regexp('Persistence: Loading.*complete')
    G_SSHInstance.set_client_configuration(timeout=orig_timeout)
    LinuxCoreUtilities().kill_processes('tail')

def check_logfile_for_event(eventName,currTimeArray):
    """check one event log at specified datetime

    Argument :
        eventName : please see toCheckLogDict for all events
        currTimeArray : UTC time message must be after. It is a list of values as returned by the get_date_and_time Keyword [year, month, day, hour, min, second]

    Return : no

    Examples:
    | check logfile for event | ${eventName} | ${tdBoxDateTime} |
    """
    toCheckLogDict = {'StartOfDayTime':['%s.*StartOfDay time occurred'%MTE, '%s.*handleStartOfDayInstrumentUpdate.*Ending' %MTE], \
        'EndOfDayTime':['%s.*EndOfDay time occurred'%MTE], \
        'CacheRolloverTime': ['%s.*CacheRollover time occurred'%MTE], \
        'RolloverTime': ['%s.*RolloverReset time occurred'%MTE], \
        'StartOfConnect':['%s.*StartOfConnect time occurred'%MTE], \
        'EndOfConnect':['%s.*EndOfConnect time occurred'%MTE], \
        'StartOfHighActivity':['%s.*StartOfHighActivity time occurred'%MTE], \
        'EndOfHighActivity':['%s.*EndOfHighActivity time occurred'%MTE]}
    if toCheckLogDict.has_key(eventName):
        logsToCheck = toCheckLogDict[eventName]
        for log in logsToCheck:
            #print '*INFO* check log: %s'%log
            wait_smf_log_message_after_time(log, currTimeArray)