import time

from LinuxCoreUtilities import LinuxCoreUtilities
from LinuxFSUtilities import LinuxFSUtilities
from utils.ssh import _exec_command

from VenueVariables import *

SMFLOGDIR = BASE_DIR + '/smf/log/'

def wait_GMI_message_after_time(message,timeRef, waittime=2, timeout=60):
    """Wait until the EventLogAdapterGMILog file contains the specified message with a timestamp newer than the specified reference time
    NOTE: This does not yet handle log file rollover at midnight

    Argument :
        message : target message in grep format to find in smf log
        timeRef : UTC time message must be after. It is a list of values as returned by the get_date_and_time Keyword [year, month, day, hour, min, second]
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
        retMessages = LinuxFSUtilities().grep_remote_file(currentFile, message)
        if (len(retMessages) > 0):
            logContents = retMessages[-1].split('|')
            if (len(logContents) >= 2):
                logDateTime = logContents[0].split('T')
                if (len(logDateTime) >= 2):
                    if logDateTime[0].strip() >= refDate and logDateTime[1].strip() >= refTime:
                        return
        time.sleep(waittime)
    raise AssertionError('*ERROR* Fail to get pattern \'%s\' from smfGMI log before timeout %ds' %(message, timeout)) 

def wait_smf_log_does_not_contain(message, waittime=2, timeout=60):
    """Wait until the SMF log file does not contain the specified message within the last 'waittime' interval

    Argument :
        message : target message in grep format to find in smf log
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
        cmd = "grep '%s' %s | tail --lines=1" %(message, currentFile)
        stdout, stderr, rc = _exec_command(cmd)
        retMessage = stdout.split(';')
        if (len(retMessage) < 2):
            return
        else:
            if retMessage[0].strip() <= refDate and retMessage[1].strip() <= refTime:
                return
        dt = LinuxCoreUtilities().get_date_and_time()
    raise AssertionError('*ERROR* SMF log still contains pattern \'%s\' after timeout %ds' %(message, timeout))    

def wait_smf_log_message_after_time(message,timeRef, waittime=2, timeout=60):
    """Wait until the SMF log file contains the specified message with a timestamp newer than the specified reference time
    NOTE: This does not yet handle log file rollover at midnight

    Argument :
        message : target message in grep format to find in smf log
        timeRef : UTC time message must be after. It is a list of values as returned by the get_date_and_time Keyword [year, month, day, hour, min, second]
        waittime : specifies the time to wait between checks, in seconds.
        timeout : specifies the maximum time to wait, in seconds.
    
    Return : Nil if success or raise error

    Examples:
    | ${dt}= | get date and time |
    | wait smf log message after time | FMS REORG DONE | ${dt} |
    """
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
        retMessages = LinuxFSUtilities().grep_remote_file(currentFile, message)
#             print 'DEBUG retMessages: %s' %retMessages
        if (len(retMessages) > 0):
            logContents = retMessages[-1].split(';')
            if (len(logContents) >= 2):
                if logContents[0].strip() >= refDate and logContents[1].strip() >= refTime:
                    return
        time.sleep(waittime)
    raise AssertionError('*ERROR* Fail to get pattern \'%s\' from smf log before timeout %ds' %(message, timeout))
