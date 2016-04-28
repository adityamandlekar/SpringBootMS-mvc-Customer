from datetime import datetime
import time

from utilpath import utilpath
from utils.ssh import _exec_command

from VenueVariables import *

def convert_EXL_datetime_to_statblock_format(exlDatetime):
    """
    Converts the given EXL datetime string to statblock datetime string. 
    
    Returns the statblock datetime string.
    
    EXL datetime string example: '2015-03-08T02:00:00.00'
    StatBlock datetime string example: '2015-Mar-08 07:00:00'
    
    Examples:
    | ${statBlockDatetime} | convert EXL datetime to statblock format | ${exlDatetime} |
    """
    exlDatetimeParts = exlDatetime.split('.')
    exlDatetimeObject = datetime.strptime(exlDatetimeParts[0], '%Y-%m-%dT%H:%M:%S')
    return exlDatetimeObject.strftime('%Y-%b-%d %H:%M:%S')

def get_count_from_stat_block(instanceName,statBlock,fieldName):
    """Returns count from stat block

    Examples:
    | get count from stat block | HKF02M | InputPortStatsBlock_0 | bytesReceivedCount |
    """          
    
    msgCount = get_stat_block_field(instanceName, statBlock, fieldName)
    
    #Non integer detected > make a zero
    if (msgCount.isdigit() == False):
        msgCount = '0'
    
    return int(msgCount)

def get_outputAddress_and_port_for_mte(field='multicast'):
    """Get ip address (based on type) and port for TD MTE
    
    field      : 'multicast', 'primary', 'secondary'
    Returns    : list = [ip,port] 

    Examples:
    | get ip address and port for MTE |
    | get ip address and port for MTE | primary   |
    | get ip address and port for MTE | secondary |
    """                  
            
    statblockNames = get_stat_blocks_for_category(MTE, 'OutputStats')
                               
    ipAndPort = get_stat_block_field(MTE, statblockNames[-1], field + 'OutputAddress').strip().split(':')
    if (len(ipAndPort) != 2):            
        raise AssertionError('*ERROR* Fail to obatin %sOutputAddress and port, got [%s]'%(field,':'.join(ipAndPort)))
    
    return ipAndPort

def get_stat_block_field(writerName, blockName, fieldName):
    """Returns the specified Stat Block field value.

    Example:
    | ${field}= | get stat block field  | ${mte}  | FMS  |  lastReorgType  |
    """
            
    cmd = "%s -f %s %s %s | grep 'Value:' | sed -n -e '/^Value:/s/^Value:[\t ]*//p' " %(utilpath.STATBLOCKFIELDREADER, writerName, blockName, fieldName)
    stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, stdout=%s stderr=%s' %(cmd,rc,stdout,stderr)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    if stdout != '':
        return stdout.strip()
    else:
        raise AssertionError('*ERROR* No field found for %s, %s, %s' %(writerName, blockName, fieldName))

def get_statBlockList_for_fh_output(instanceName):
    """get all the stat block name for FH output

    Argument
    instanceName : instance of FH
    Returns list of stat block name

    Examples:
    | get statBlockList for fh output | HKF01F |
     """
    
    statBlockList = get_stat_blocks_for_category(instanceName, 'OutputStats')

    return statBlockList    

def get_statBlockList_for_mte_output():
    """get all the stat block name for MTE output

    Argument NIL
    Returns list of stat block name

    Examples:
    | get statBlockList for mte output |
     """
    
    statBlockList = ['OutputStatsBlock']
   
    return statBlockList     

def get_stat_blocks_for_category(writerName, categoryName):
    """Returns a list of Stat Blocks for the specified category.

    Examples:
    | $categories}= | get stat blocks for category  | ${mte}  | FMS       |
    | $categories}= | get stat blocks for category  | ${mte}  | Holidays  |
    """

    cmd = "%s -c %s %s " %(utilpath.STATBLOCKFIELDREADER, writerName, categoryName)
    stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, stdout=%s stderr=%s' %(cmd,rc,stdout,stderr)
    
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    lines = stdout.rstrip().split('\n')
    numLines = len(lines)   
    for idx in range(0,numLines-1):
        if lines[idx].find('All stat blocks for') != -1:
            return lines[idx+1:numLines]

    raise AssertionError('*ERROR* No block found for %s, %s' %(writerName, categoryName))

def statBlock_should_be_equal(writerName, blockName, fieldName, expectedValue, msg='statBlock actual value does not match expected value'):
    """Checks whether the specified Stat Block field has the exected value.

    Example:
    | statBlock should be equal  | ${mte}  | FMS  |  lastReorgType  | 2 |
    """
    cmd = "%s -v %s %s %s %s" %(utilpath.STATBLOCKFIELDREADER, writerName, blockName, fieldName, expectedValue)
    stdout, stderr, rc = _exec_command(cmd)
#         print '*DEBUG* cmd=%s, %s %s' %(cmd,stdout,stderr)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* ' + msg)
    return rc

def wait_for_HealthCheck(writerName, fieldToCheck, waittime=2, timeout=60):
    """Read the HealthCheck Stat Block for the specified writerName and wait for the specified 'fieldToCheck' value to be 1 (true).

    Argument 'waittime' specifies the time to wait between checks, in seconds.
    Argument 'timeout' specifies the maximum time to wait, in seconds.
    
    Does not return a value; raises an error if the field value is not 1 within timeout seconds.

    Examples:
    | Wait for HealthCheck  | ${mte}  | IsLinehandlerStartupComplete  |
    | Wait for HealthCheck  | ${mte}  | FMSStartupReorgHasCompleted   | 5  | 600  |
    """
    return wait_for_StatBlock(writerName, 'HealthCheck', fieldToCheck, '1', waittime, timeout)

def wait_for_StatBlock(writerName, statBlock, fieldToCheck, fieldValue, waittime=2, timeout=60):
    """Reads the Stat Block for the specified writerName and wait for the specified 'fieldToCheck' value to be fieldValue.

    Argument 'waittime' specifies the time to wait between checks, in seconds.
    Argument 'timeout' specifies the maximum time to wait, in seconds.
    
    Does not return a value; raises an error if the field value is not equal to fieldValue within timeout seconds.

    Examples:
    | Wait for StatBlock  | ${mte}  | HealthCheck | IsLinehandlerStartupComplete  | 1 |
    | Wait for StatBlock  | ${mte}  | HealthCheck | FMSStartupReorgHasCompleted   | 1 | 5  | 600  |
    """
    # convert  unicode to int (it is unicode if it came from the Robot test)
    timeout = int(timeout)
    waittime = int(waittime)
    maxtime = time.time() + float(timeout)
    while time.time() <= maxtime:
        time.sleep(waittime)
        val = get_stat_block_field(writerName,statBlock,fieldToCheck)
#             print 'DEBUG time=%f maxtime=%f value=%s' %(time.time(),maxtime,val)
        if val.strip() == fieldValue:
            return 0
    raise AssertionError('*ERROR* %s for %s  %s did not get value %s before timeout %ds' %(writerName,statBlock,fieldToCheck,fieldValue,timeout))

