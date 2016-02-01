﻿'''
Created on May 12, 2015

@author: xiaoqin.li
'''

from __future__ import with_statement

from utils.version import get_version
from utils.rc import _rc

from utils.ssh import G_SSHInstance, _exec_command,_ls,_search_file,_delete_file,_start_command,_check_process

from datetime import date, datetime, timedelta
import time
import string
import re
import os.path

import xml.etree.ElementTree as ET

from LinuxFSUtilities import LinuxFSUtilities
from LinuxCoreUtilities import LinuxCoreUtilities

class LinuxToolUtilities():
    """A test library providing keywords for run all kinds of tool, for example wirehshark, das, dataview, FMSCMD etc.

    `LinuxToolUtilities` is GATS's standard library.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()
    
    COMMANDER = ''
    HOSTMANAGER = ''
    STATBLOCKFIELDREADER = ''
    SMFLOGDIR = ''
    MANGLINGRULE = {'SOU': '3', 'BETA': '2', 'RRG': '1', 'UNMANGLED' : '0'};
    
    def setUtilPath(self, path):
        """Setting the Utilities paths by given base directory for searching
        
        Examples:
        | setUtilPath | '/ThomsonReuters' |   
         """
        self.COMMANDER = _search_file(path,'Commander',True)[0]
        self.STATBLOCKFIELDREADER = _search_file(path,'StatBlockFieldReader',True)[0]
        self.HOSTMANAGER = _search_file(path,'HostManager',True)[0]
        self.SMFLOGDIR = path + '/smf/log/'
        self.BASE_DIR = path

    def run_commander(self, application, command):
        """Runs the Commander tool to execute the specified CHE command.

        Returns the stdout from the executed command.

        Examples:
        | Run Commander  | process      | start ${mte}      |
        | Run Commander  | linehandler  | dumpcache ${mte}  |
        """
        cmd = r'%s -n %s -c "%s"' %(self.COMMANDER,application,command)
        stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr)
        if rc !=0 or stderr !='' or stdout.lower().find('failed') != -1:
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        print '*INFO* cmd=%s, %s'%(cmd,stdout)
        return stdout   
       
    def get_stat_block_field(self, writerName, blockName, fieldName):
        """Returns the specified Stat Block field value.

        Example:
        | ${field}= | get stat block field  | ${mte}  | FMS  |  lastReorgType  |
        """
                
        cmd = "%s -f %s %s %s | grep 'Value:' | sed -n -e '/^Value:/s/^Value:[\t ]*//p' " %(self.STATBLOCKFIELDREADER, writerName, blockName, fieldName)
        stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, stdout=%s stderr=%s' %(cmd,rc,stdout,stderr)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        if stdout != '':
            return stdout.strip()
        else:
            raise AssertionError('*ERROR* No field found for %s, %s, %s' %(writerName, blockName, fieldName))

    def get_stat_blocks_for_category(self, writerName, categoryName):
        """Returns a list of Stat Blocks for the specified category.

        Examples:
        | $categories}= | get stat blocks for category  | ${mte}  | FMS       |
        | $categories}= | get stat blocks for category  | ${mte}  | Holidays  |
        """

        cmd = "%s -c %s %s " %(self.STATBLOCKFIELDREADER, writerName, categoryName)
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

    def statBlock_should_be_equal(self, writerName, blockName, fieldName, expectedValue, msg='statBlock actual value does not match expected value'):
        """Checks whether the specified Stat Block field has the exected value.

        Example:
        | statBlock should be equal  | ${mte}  | FMS  |  lastReorgType  | 2 |
        """
        cmd = "%s -v %s %s %s %s" %(self.STATBLOCKFIELDREADER, writerName, blockName, fieldName, expectedValue)
        stdout, stderr, rc = _exec_command(cmd)
#         print '*DEBUG* cmd=%s, %s %s' %(cmd,stdout,stderr)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* ' + msg)
        return rc

    def wait_for_StatBlock(self, MTEName, statBlock, fieldToCheck, fieldValue, waittime=2, timeout=60):
        """Reads the Stat Block for the specified MTE and wait for the specified 'fieldToCheck' value to be fieldValue.

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
            val = self.get_stat_block_field(MTEName,statBlock,fieldToCheck)
#             print 'DEBUG time=%f maxtime=%f value=%s' %(time.time(),maxtime,val)
            if val.strip() == fieldValue:
                return 0
        raise AssertionError('*ERROR* %s for %s  %s did not get value %s before timeout %ds' %(MTEName,statBlock,fieldToCheck,fieldValue,timeout))
    
    def wait_for_HealthCheck(self, MTEName, fieldToCheck, waittime=2, timeout=60):
        """Reads the Stat Block for the specified MTE and wait for the specified 'fieldToCheck' value to be 1 (true).

        Argument 'waittime' specifies the time to wait between checks, in seconds.
        Argument 'timeout' specifies the maximum time to wait, in seconds.
        
        Does not return a value; raises an error if the field value is not 1 within timeout seconds.

        Examples:
        | Wait for HealthCheck  | ${mte}  | IsLinehandlerStartupComplete  |
        | Wait for HealthCheck  | ${mte}  | FMSStartupReorgHasCompleted   | 5  | 600  |
        """
        return self.wait_for_StatBlock(MTEName, 'HealthCheck', fieldToCheck, '1', waittime, timeout)

    def wait_for_process_to_exist(self, pattern, waittime=2, timeout=60):
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

    def wait_for_process_to_not_exist(self, pattern, waittime=2, timeout=60):
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

    def wait_for_search_file(self, topdir, filename, waittime=2, timeout=60):
        """Wait until the remote filename to exist somewhere under the specified directory.

        Arguement venuedir is the top directory to do the search from.
        Argument filename may contain UNIX filename wildcard values.
        Argument 'waittime' specifies the time to wait between checks, in seconds.
        Argument 'timeout' specifies the maximum time to wait, in seconds.
        
        Does not return a value; raises an error if the file does not exist within timeout seconds.

        Examples:
        | Wait for searchfile  | venuedir | filepathname  |
        | Wait for searchfile  | venuedir | filepathname  | 2  | 30  |
        """
        # convert  unicode to int (it is unicode if it came from the Robot test)
        timeout = int(timeout)
        waittime = int(waittime)
        maxtime = time.time() + float(timeout)

        while time.time() <= maxtime:
            foundfiles = _search_file(topdir,filename,True)
            if len(foundfiles) >= 1:
                return foundfiles
            time.sleep(waittime)
        raise AssertionError('*ERROR* File %s does not exist (timeout %ds)' %(filename,timeout))

    def wait_for_file_write(self, filename, waittime=2, timeout=60):
        """Wait until the remote file exists and the size does not change.

        Argument filename may contain UNIX filename wildcard values.
        Argument 'waittime' specifies the time to wait between checks, in seconds.
        Argument 'timeout' specifies the maximum time to wait, in seconds.
        
        Does not return a value; raises an error if the file does not exist or writing complete within timeout seconds.

        Examples:
        | Wait for file write  | filepathname  |
        | Wait for file write  | filepathname  | 1  | 10  |
        """
        # convert  unicode to int (it is unicode if it came from the Robot test)
        timeout = int(timeout)
        waittime = int(waittime)
        maxtime = time.time() + float(timeout)

        fileStartSize = -1
        while time.time() <= maxtime:
            fileInfo = _ls(filename,'--full-time')
            if len(fileInfo) == 0:
                continue
            splitInfo = fileInfo.split(' ')
            fileCurrSize = splitInfo[4]
            if fileCurrSize == fileStartSize:
                return
            fileStartSize = fileCurrSize
            time.sleep(waittime)
        if fileStartSize == -1:
            raise AssertionError('*ERROR* File %s does not exist' %filename)
        else:
            raise AssertionError('*ERROR* File %s writing did not complete before timeout %ds' %(filename,timeout))
   
    def wait_for_file_update(self, filename, waittime=2, timeout=60):
        """Wait until the remote file timestamp changes and then wait until the size does not change.

        Argument filename may contain UNIX filename wildcard values.
        Argument 'waittime' specifies the time to wait between checks, in seconds.
        Argument 'timeout' specifies the maximum time to wait, in seconds.
        
        Does not return a value; raises an error if the file does not change within timeout seconds.

        Examples:
        | Wait for file update  | filepathname  |
        | Wait for file update  | filepathname  | 5  | 90  |
        """
        # convert  unicode to int (it is unicode if it came from the Robot test)
        timeout = int(timeout)
        waittime = int(waittime)
        maxtime = time.time() + float(timeout)
        
        fileInfo = _ls(filename,'--full-time')
        if len(fileInfo) == 0:
            raise AssertionError('*ERROR* File %s does not exist' %filename)
        splitInfo = fileInfo.split(' ')
        fileStartTime = ' '.join(splitInfo[5:7])
        
        while time.time() <= maxtime:
            fileInfo = _ls(filename,'--full-time')
            splitInfo = fileInfo.split(' ')
            fileCurrTime = ' '.join(splitInfo[5:7])
#             print 'DEBUG fileStartTime=%s fileCurrTime=%s' %(fileStartTime,fileCurrTime)
            if fileCurrTime > fileStartTime:
                # file has changed, now wait for writing to complete
                fileStartSize = splitInfo[4]
                while time.time() <= maxtime:
                    fileInfo = _ls(filename,'--full-time')
                    splitInfo = fileInfo.split(' ')
                    fileCurrSize = splitInfo[4]
#                     print 'DEBUG fileStartSize=%s fileCurrSize=%s' %(fileStartSize,fileCurrSize)
                    if fileCurrSize == fileStartSize:
                        return
                    fileStartSize = fileCurrSize
                    time.sleep(waittime)
                raise AssertionError('*ERROR* File %s writing did not complete before timeout %ds' %(filename,timeout))
            time.sleep(waittime)
        raise AssertionError('*ERROR* File %s did not change before timeout %ds' %(filename,timeout))

    def wait_smf_log_message_after_time(self,message,timeRef, waittime=2, timeout=60):
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
        currentFile = '%s/smf-log-files.%s%s%s.txt' %(self.SMFLOGDIR, dt[0], dt[1], dt[2])
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
 
    def wait_smf_log_does_not_contain(self, message, waittime=2, timeout=60):
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
            currentFile = '%s/smf-log-files.%s%s%s.txt' %(self.SMFLOGDIR, dt[0], dt[1], dt[2])
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
    
    def dump_cache(self, MTEName, venuedir, waittime=2, timeout=60):
        """Dump the MTE cache to a file (on the MTE machine).

        Argument venuedir specifies the base directory on the CHE machine where the Venue data/programs are located.
        
        Returns the full path name to the dumped file.

        Examples:
        | Dump Cache  | TTView3  | /ThompsonReuters/Venues  |
        | Dump Cache  | ${mte}   | ${VENUE_DIR}             |
        """
        stdout = self.run_commander('linehandler', 'lhcommand %s dumpcache' %MTEName)
        if stdout.lower().find('successfully processed command:') == -1:
            raise AssertionError('*ERROR* dumpcache %s failed, %s' %(MTEName,stdout))
        
        # get path to the cache file
        today = LinuxCoreUtilities().get_date_and_time()
        filename = '%s_%s%s%s.csv' %(MTEName, today[0], today[1], today[2])
        foundfiles = self.wait_for_search_file(venuedir,filename,waittime,timeout)
        if len(foundfiles) > 1:
            raise AssertionError('*ERROR* Found more than one cache file: %s' %foundfiles)
        print '*INFO* cache file is %s' %foundfiles[0]
        self.wait_for_file_write(foundfiles[0],waittime,timeout)
        return foundfiles[0]

        # if GATS provides Venue name, then use this code instead of _search_file
        # This requires venuedir to include the venue name
#         filename = '%s/MTE/%s_%s.csv' %(venuedir,MTEName,today)
#         G_SSHInstance.file_should_exist(filename)
#         return filename
    
    def get_ric_fields_from_cache(self, MTEName, venuedir, numrows, domain, contextID):
        """Get the first n rows' ric fields data for the specified domain or/and contextID from MTE cache.
        Ignore RICs that contain 'TEST' and non-publishable RICs.
        Returns an array of dictionary containing all fields for the match.  Returns empty dictionary if match are not found
 
        Arguments:
            MTEname:   MTE name
            venuedir:  venue directory name
            rows:      number of rows to return
            domain:    RIC must belong to this domain if domain is not NONE
            contextID: RIC must belong to this contextID if contextID is not NONE
                       If domain and contextID are NONE, first PUBLISHABLE=TRUE will be checked
                    
        Returns an array of dictionaries containing fields for each RICs.
        E.g. [ {RIC : ric1, SIC sic1, DOMAIN MarketPrice, CONTEXT_ID : 1052 ...}, {RIC : ric2, SIC sic2, DOMAIN MarketPrice, CONTEXT_ID : 1052 ...} ]
 
        Example:
        | get_ric_fields_from_cache  | ${MTE} | ${VENUE_DIR} | 1 | MARKET_PRICE |
        | get_ric_fields_from_cache  | ${MTE} | ${VENUE_DIR} | 1 | ${EMPTY} | 1052 |
        | get_ric_fields_from_cache  | ${MTE} | ${VENUE_DIR} | 2 | MARKET_PRICE | 1052 |
        | get_ric_fields_from_cache  | ${MTE} | ${VENUE_DIR} | 2 |
        """
        if numrows != 'all':
            numrows = int(numrows)
            
        if domain:
            newDomain = self._convert_domain_to_cache_format(domain)
            
        cacheFile = self.dump_cache(MTEName, venuedir)
        # create hash of header values
        cmd = "head -1 %s | tr ',' '\n'" %cacheFile
        stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, stdout=%s stderr=%s' %(cmd,rc,stdout,stderr)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        
        headerList = stdout.strip().split()
        index = 1;
        headerDict = {}
        for fieldName in headerList:
            headerDict[fieldName] = index
            index += 1
        if not headerDict.has_key('DOMAIN') or not headerDict.has_key('PUBLISHABLE') or not headerDict.has_key('CONTEXT_ID'):
            raise AssertionError('*ERROR* Did not find required column names in cache file (DOMAIN, PUBLISHABLE, CONTEXT_ID') 
        
        # get all fields for selected RICs
        domainCol = headerDict['DOMAIN']
        publishableCol = headerDict['PUBLISHABLE']
        contextIDCol = headerDict['CONTEXT_ID']
        
        if contextID and domain:
            if numrows == 'all':
                cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && $%d == \"TRUE\" && $%d == \"%s\" {print}'" %(cacheFile, domainCol, newDomain, publishableCol, contextIDCol, contextID)
            else:
                cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && $%d == \"TRUE\" && $%d == \"%s\" {print}' | head -%d" %(cacheFile, domainCol, newDomain, publishableCol, contextIDCol,contextID, numrows)
                
        elif  domain: 
            if numrows == 'all':
                cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && $%d == \"TRUE\" {print}'" %(cacheFile, domainCol, newDomain, publishableCol)
            else:
                cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && $%d == \"TRUE\" {print}' | head -%d" %(cacheFile, domainCol, newDomain, publishableCol, numrows)
                
        elif  contextID:
            if numrows == 'all':
                cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && $%d == \"TRUE\" {print}'" %(cacheFile, contextIDCol, contextID, publishableCol)
            else:
                cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && $%d == \"TRUE\" {print}' | head -%d" %(cacheFile, contextIDCol, contextID, publishableCol, numrows)
                
        else:
            if numrows == 'all':
                cmd = "grep -v TEST %s | awk -F',' '$%d == \"TRUE\" {print}'" %(cacheFile, publishableCol)
            else:
                cmd = "grep -v TEST %s | awk -F',' '$%d == \"TRUE\" {print}' | head -%d" %(cacheFile, publishableCol, numrows)
                
        stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, stdout=%s stderr=%s' %(cmd,rc,stdout,stderr)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        rows = stdout.splitlines()
        if numrows != 'all' and len(rows) != numrows:
            raise AssertionError('*ERROR* Requested %d rows, Found %d rows' %(numrows,len(rows)))
        
        # get the requested fields
        result = []
        for row in rows:
            values = row.split(',')
            
            if len(values) != len(headerList):
                raise AssertionError('*ERROR* Number of values (%d) does not match number of headers (%d)' %(len(values), len(headerList)))
            
            fieldDict = {}
            for i in range(0, len(values)):
                if headerList[i] == 'DOMAIN':
                    newdomain = self._convert_cachedomain_to_normal_format(values[i]) 
                    fieldDict[headerList[i]] = newdomain
                else:    
                    fieldDict[headerList[i]] = values[i]
               
            result.append(fieldDict)
                  
        _delete_file(cacheFile,'',False)
        return result 
    
    def get_all_fields_for_ric_from_cache(self, MTEName, venuedir, ric):
        """Get the field values from the MTE cache for the specifed RIC.
 
        Arguments:
            MTEname:  MTE name
            venuedir: venue directory name
            ric:   RIC name
         
        Returns a dictionary containing all fields for the RIC.  Returns empty dictionary if RIC not found.
 
        Example:
        | get random RICs from cache  | ${MTE} | ${VENUE_DIR} | TESTRIC |
        """
        cacheFile = self.dump_cache(MTEName, venuedir)
         
        # create hash of header values
        cmd = "head -1 %s | tr ',' '\n'" %cacheFile
        stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, stdout=%s stderr=%s' %(cmd,rc,stdout,stderr)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        ricCol = 0
        header = stdout.strip().split()
        for i in range(0, len(header)):
            if header[i] == 'RIC':
                ricCol = i+1 # for awk, col numbers start at 1, so add 1 to index
                break
        if not ricCol:
            raise AssertionError('*ERROR* Did not find required column name in cache file (RIC)')
         
        # get all fields for the RIC
        cmd = "awk -F',' '$%d == \"%s\" {print}' %s" %(ricCol, ric, cacheFile)
        stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, stdout=%s stderr=%s' %(cmd,rc,stdout,stderr)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        rows = stdout.strip().split('\n')
        if len(rows) > 1:
            raise AssertionError('*ERROR* Multiple rows found for RIC %s rows.  %s' %(ric,rows))
        
        # put fields into dictionary
        values = rows[0].split(',')
        if len(values) <= 1:
            return {}
        if len(values) != len(header):
            raise AssertionError('*ERROR* Number of values (%d) does not match number of headers (%d)' %(len(values), len(header)))
        valuesToReturn = {}
        for i in range(0, len(values)):
                valuesToReturn[header[i]] = values[i]
         
        _delete_file(cacheFile,'',False)
        return valuesToReturn
    
    def _convert_domain_to_cache_format(self,domain):
        newDomain = domain.replace('_','')
        if newDomain.lower() == 'marketprice':
            newDomain = 'MarketPrice'
        elif newDomain.lower() == 'marketbyprice':
            newDomain = 'MarketByPrice'
        elif newDomain.lower() == 'marketbyorder':
            newDomain = 'MarketByOrder'
        else:
            raise AssertionError('*ERROR* Unsupported domain %d' %domain)
        return newDomain
    
    def _convert_cachedomain_to_normal_format(self,domain):
        if domain.lower() == 'marketprice':
            newDomain = 'MARKET_PRICE'
        elif domain.lower() == 'marketbyprice':
            newDomain = 'MARKET_BY_PRICE'
        elif domain.lower() == 'marketbyorder':
            newDomain = 'MARKET_BY_ORDER'
        else:
            raise AssertionError('*ERROR* Unsupported domain %d' %domain)
        return newDomain
    
    def start_smf(self):
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
            if stdout.find('SMF is running')!= -1:
                print '*INFO* %s' %stdout
                return 0
        cmd = 'service smf start'
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        if stdout.find('SMF service is already started')!= -1 or stdout.find(r'SMF is started.')!= -1:
            print '*INFO* %s' %stdout
        else:
            raise AssertionError('*ERROR* cmd=%s, %s' %(cmd,stdout)) 
            
    def stop_smf(self):
        """Stop the Server Management Foundation process.
        Does not return a value.

        Example:
        | Stop SMF  |
        """
        cmd = 'service smf status'
        stdout, stderr, rc = _exec_command(cmd)
        if rc == 3: # rc==3 means SMF is not running
                print '*INFO* %s' %stdout
                return 0
        cmd = 'service smf stop'
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        if stdout.find('SMF is stopped successfully')!= -1:
            print '*INFO* %s' %stdout
        else:
            raise AssertionError('*ERROR* cmd=%s, %s' %(cmd,stdout))            
 
    def _get_alias_ip(self,alias):
        """Get ip address by given alias name

        Argument alias specifies the alias name that we could find in /etc/hosts
        
        Returns string 'null' if not found or ip address that matched with alias

        Examples:
        | get alias ip | 'DDNA' |
        """          
        cmd = 'getent hosts ' + alias
        stdout, stderr, rc = _exec_command(cmd)
        
        if rc==2:
            print '*INFO* no alias found for given ip'  
            return 'null'
        
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))     
        
        if len(stdout) > 0:
            listOfContent = stdout.split()
            return listOfContent[0]
        
        return 'null'
  
    def _get_all_interfaces_names(self):
        """Get the name for all avaliable interface from box
    
        Argument NIL
            
        Returns empty list or list of interface name
    
        Examples:
        | get all interfaces names |
        """            
            
        listOfInterfaceName = []
                
        cmd = 'ip link show | awk \'/eth[0-9]/ {print $0}\''
        stdout, stderr, rc = _exec_command(cmd)
    
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))               
                
        listOfContent = stdout.split('\n')
        for content in listOfContent:
            subcontent = content.split(':')
            if (len(subcontent) > 2):
                listOfInterfaceName.append(subcontent[1].lstrip())
                
        return listOfInterfaceName  
    
    def _get_interface_name_by_ip(self,ip):
        """Get network card interface name by given ip

        Argument ip specifies the ip address that used to find interface name
        
        Returns string interface name or prompt error

        Examples:
        | get interface name by ip | '192.168.56.10' |
        """
        
        #Checking if it is valid ip address
        ipComponents = ip.split('.')
        if (len(ipComponents) == 4):
            for component in ipComponents:
                if not(component.isdigit()):
                    raise AssertionError('*ERROR* Invalid IP address %s' %ip)     
                           
        listOfInterfacesNames = self._get_all_interfaces_names()
        for interfaceName in listOfInterfacesNames:
            cmd = 'ifconfig ' + interfaceName + ' | grep \"inet addr\" | awk \'BEGIN {FS=":"}{print $2}\''
            stdout, stderr, rc = _exec_command(cmd)
                
            if rc !=0 or stderr !='':
                raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))     
                        
            if len(stdout) > 0: 
                listofContent = stdout.split()
                if (listofContent[0] == ip):
                    return interfaceName
                   
        raise AssertionError('*ERROR* Fail to get the interface name for %s' %ip)      

    def get_interface_name_by_alias(self,alias):
        """Get network ard interface name by given alias

        Argument alias specifies the alias name that we could find in /etc/hosts
        
        Returns string interfance name or prompt error

        Examples:
        | get interface by alias | DDNA |
        """        
        
        aliasIp = self._get_alias_ip(alias)
        interfaceName = self._get_interface_name_by_ip(aliasIp)
        
        return interfaceName
    
    def get_outputAddress_and_port_for_mte(self,mte,field='multicast'):
        """Get ip address (based on type) and port for TD MTE
        
        mte        : instance name of MTE
        field      : 'multicast', 'primary', 'secondary'
        Returns    : list = [ip,port] 

        Examples:
        | get ip address and port for different field of specific MTE | MFDS1M |
        """                  
                
        statblockNames = self.get_stat_blocks_for_category(mte, 'OutputStats')
                                   
        ipAndPort = self.get_stat_block_field(mte, statblockNames[-1], field + 'OutputAddress').strip().split(':')
        if (len(ipAndPort) != 2):            
            raise AssertionError('*ERROR* Fail to obatin %sOutputAddress and port, got [%s]'%(field,':'.join(ipAndPort)))
        
        return ipAndPort
    
    def _get_message_sent_from_stat_block(self,instanceName,statBlock):
        """Get byte receive data from stat block
        Argument : instanceName , name of MTE or FH instance
                   statBlock, name of block in StatBlock
        Returns : integer of byte received

        Examples:
        | get message sent from stat block| MFDS1F | output1 |  
        """          
        
        msgCount = self.get_stat_block_field(instanceName, statBlock, 'numberMessagesSent')
        
        #Non integer detected > make a zero
        if (msgCount.isdigit() == False):
            msgCount = '0'
        
        return int(msgCount)
    
    def _get_statBlockList_for_fh_output(self):
        """get all the stat block name for FH output

        Argument NIL
        Returns list of stat block name

        Examples:
        | get statBlockList for fh output |
         """
        
        statBlockList = ['output1']
                 
        return statBlockList    
    
    def _get_statBlockList_for_mte_input(self):
        """get all the stat block name for FH output

        Argument NIL
        Returns list of stat block name

        Examples:
        | get statBlockList for fh output |
         """
        
        statBlockList = ['InputPortStatsBlock_0']
                 
        return statBlockList    
    
    def _get_bytes_received_from_stat_block(self,instanceName,statBlock):
        """Get byte receive data from stat block
        Argument : instanceName , name of MTE or FH instance
                   statBlock, name of block in StatBlock
        Returns : integer of byte received

        Examples:
        | get message sent from stat block| MFDS1F | InputPortStatsBlock_0 |  
        """          
        
        msgCount = self.get_stat_block_field(instanceName, statBlock, 'bytesReceivedCount')
        
        #Non integer detected > make a zero
        if (msgCount.isdigit() == False):
            msgCount = '0'
        
        return int(msgCount)    
    
    def wait_for_capture_to_complete(self,instanceName,waittime=5,timeout=30):
        """wait for capture finish by checking the stat block information

        Argument 
        instanceName : either instance of MTE of FH e.g. MFDS1M or MFDS1F
        statBlockList : [list] of stat block name that want to monitor during capture
        waittime : how long we wait for each cycle during checking (second)
        timeout : how long we monitor before we timeout (second)
    
        Returns NIL.

        Examples:
        | wait for capture to complete | HKF1A | 2 | 300 |
         """
        
        statBlockList = self._get_statBlockList_for_mte_input()
        
        #initialize the msgCount for each stat block found in statBlock list 
        msgCountPrev = {}
        msgCountDiff = {}
        for statBlock in statBlockList:
            msgCountPrev[statBlock] =  self._get_bytes_received_from_stat_block(instanceName,statBlock)
            msgCountDiff[statBlock] = 0
    
        # convert  unicode to int (it is unicode if it came from the Robot test)
        timeout = int(timeout)
        waittime = int(waittime)
        maxtime = time.time() + float(timeout) 
        
        while time.time() <= maxtime:
                        
            time.sleep(waittime)  
            
            #Check if msg count difference
            for statBlock in statBlockList:
                msgCountCurr = self._get_bytes_received_from_stat_block(instanceName,statBlock)
                msgCountDiff[statBlock] = msgCountCurr - msgCountPrev[statBlock]
                
                if (msgCountDiff[statBlock] < 0):
                    raise AssertionError('*ERROR* stat block %s - Current bytes received %d < previous bytes received %d' %(statBlock,msgCountCurr,msgCountPrev[statBlock]))
            
                msgCountPrev[statBlock] = msgCountCurr
                
            #Check time to stop catpure
            isStop = True
            for statBlock in statBlockList:
                if (msgCountDiff[statBlock] != 0):
                    isStop = False
            
            if (isStop):
                return                    
        
        #Timeout                    
        raise AssertionError('*ERROR* Timeout %ds : Playback has not ended yet for some channel (suggest to adjust timeout)' %(timeout))
                     
    def start_capture_packets(self,outputfile,interface,ip,port,protocol='UDP'):
        """start capture packets by using tcpdump

        Argument 
        outputfile : outputfilename fullpath
        interface : the nic interface name e.g. eth1
        ip : 'source' ip for data capture
        port : port for data capture
        protocol : protocol for data capture
    
        Returns NIL.

        Examples:
        | start capture packets | mte.output.pcap | eth0 | 232.2.1.0 | 7777 |
         """

        #Pre Checking
        checkList = _check_process(['tcpdump'])
        if (len(checkList[0]) > 0):
            print '*INFO* tcpdump process already started at the TD box. Kill the exising tcpdump process'
            self.stop_capture_packets() 
         
        #Create output folder
        cmd = 'mkdir -p' + os.path.dirname(outputfile)
        stdout, stderr, rc = _exec_command(cmd)
        
        #Remove existing pcap
        cmd = 'rm -rf ' + outputfile
        stdout, stderr, rc = _exec_command(cmd)
      
        cmd = ''
        if (len(ip) > 0 and len(port) > 0):
            cmd = 'tcpdump -i ' + interface + ' -s0 \'(host ' + ip +  ' and port ' + port  + ')\' -w ' + outputfile
        else:     
            cmd = 'tcpdump -i' + interface + '-s0 ' + protocol +  '-w ' + outputfile
        
        print '*INFO* ' + cmd    
        _start_command(cmd)
        
        #Post Checking
        time.sleep(5) #wait a while before checking or sometimes it would return false alarm
        checkList = _check_process(['tcpdump'])
        if (len(checkList[1]) > 0):
            raise AssertionError('*ERROR* Fail to start cmd=%s ' %cmd)
                    
    def stop_capture_packets(self):
        """stop capture packets by using tcpdump
        Argument NIL
        
        Returns NIL.

        Examples:
        | stop capture packets |
         """
                        
        cmd = 'pkill tcpdump'
        stdout, stderr, rc = _exec_command(cmd)            
        
        if rc==1:
            print '*INFO* tcpdump process NOT found on target box'
        elif rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        else:   
            print '*INFO* tcpdump process stop successfully'

    def get_contextID_from_FidFilter(self, venue_dir):
        fidfilter = self.get_contextId_fids_constit_from_fidfiltertxt(venue_dir)
        return fidfilter.keys()
    
    def get_contextId_fids_constit_from_fidfiltertxt(self,venuedir):
        """Get context ID, FIDs and Constituent from FIDFilter.txt
        Argument : NIL
        Returns : Dictionary of FIDFilter [contextID][constituent][fid]='1'

        Examples:
        | get contextId fids constit from fidfiltertxt
         """    
                        
        constitWithFIDs = {} #dictionary with key=contituent number and content=array of FIDs
        contextIdsMap = {} #dictionary with key=contextID and content=map of constit with FIDs
        
        cmd = 'cat `find ' + venuedir + ' -name FIDFilter.txt`'
        stdout, stderr, rc = _exec_command(cmd)
        
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))  
        
        lines = stdout.split('\n')
        
        contextID = ""
        for line in lines:
            if (len(line.strip()) > 0 and line.strip()[0] != '!'):
                content = line.split(':')
                if (len(content) == 2):
                    if (content[0].find('LIST NUMBER') != -1):
                        
                        #Before roll to next context ID, save the FID List to previous found context ID
                        if (len(constitWithFIDs) > 0):
                            contextIdsMap[contextID] = dict(constitWithFIDs)
                        
                        #Get the new context ID
                        contextID = content[1].strip()
                        
                        #Prepare a new FID list Map for context ID
                        contextIdsMap[contextID] = {}
                        
                        #clear constitWithFIDs Map
                        constitWithFIDs.clear()
                        
                else:
                    content = line.split()
                    if (len(content) == 2):
                        fid = content[0]
                        constit = content[1]
                        if re.match(r'-?\d+$',fid) and re.match(r'-?\d+$',constit):
                            if (constitWithFIDs.has_key(constit) == False):
                                constitWithFIDs[constit] = {}
                            constitWithFIDs[constit][fid]='1'
                        else:
                            if (len(contextID) > 0):
                                raise AssertionError('*ERROR* %s has non-integer value found'%line)
                            else:
                                raise AssertionError('*ERROR* empty context ID found in FIDFilter.txt')
           
        if (len(constitWithFIDs) > 0):
            contextIdsMap[contextID] = dict(constitWithFIDs)
        
        #post checking
        if (len(contextIdsMap) == 0):
            raise AssertionError('*ERROR* Fail to retrieve FIDFilter.txt information') 

        return contextIdsMap
    
    def get_fids_from_fidfiltertxt_by_contextId(self,contextId,venuedir):
        """Get FIDs list from FIDFilter Dictionary given context ID
        Argument : required context ID
        Returns : Dictionary of FID List with key=constituent number

        Examples:
        | get fids from fidfiltertxt by contextId | 1234 |     
        """
                
        contextIdsMap = self.get_contextId_fids_constit_from_fidfiltertxt(venuedir)
        
        if (contextIdsMap.has_key(contextId) == True):
            return  contextIdsMap[contextId]
        
        return dict({})
    
    def get_fids_from_fidfiltertxt_by_contextId_and_constit(self,contextId,constit,venuedir):
        """Get FIDs list from FIDFilter Dictionary given context ID
        Argument : required context ID and constituent number
        Returns : List of FIDs

        Examples:
        | get fids from fidfiltertxt by contextId | 1234 |     
        """        

        contextIdsMap = self.get_contextId_fids_constit_from_fidfiltertxt(venuedir)
        
        if (contextIdsMap.has_key(contextId) == True):
            if (contextIdsMap[contextId].has_key(constit) == True):
                return  contextIdsMap[contextId][constit]
        
        return dict({})

    def backup_cfg_file(self,searchdir,cfgfile,suffix='.backup'):
        """backup config file by create a new copy with filename append with suffix
        Argument : 
        searchdir  : directary where we search for the configuration file
        cfgfile    : configuration filename
        suffix     : suffix used to create the backup filename 
            
        Returns : a list with 1st item = full path config filename and 2nd itme = full path backup filename

        Examples:
        | backup cfg file | /ThomsonReuters/Venues | manglingConfiguration.xml |  
        """         
        
        #Find configuration file
        foundfiles = _search_file(searchdir,cfgfile,True)        
        if len(foundfiles) < 1:
            raise AssertionError('*ERROR* %s not found' %cfgfile)
        """elif len(foundfiles) > 1:
            raise AssertionError('*ERROR* Found more than one file: %s' %cfgfile)   """  
                
        #backup config file
        backupfile = foundfiles[0] + suffix
        cmd = "cp -a %s %s"%(foundfiles[0], backupfile)
        stdout, stderr, rc = _exec_command(cmd)
        
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        
        return [foundfiles[0], backupfile]
        
    def restore_cfg_file(self,cfgfile,backupfile):
        """restore config file by rename backupfile to cfgfile
        Argument : 
        cfgfile    : full path of configuration file
        backupfile : full path of backup file
            
        Returns : Nil

        Examples:
        | restore cfg file | /reuters/Venues/HKF/MTE/manglingConfiguration.xml | /reuters/Venues/HKF/MTE/manglingConfiguration.xml.backup |  
        """       
        
        LinuxFSUtilities().remote_file_should_exist(cfgfile)
        LinuxFSUtilities().remote_file_should_exist(backupfile)
        
        #restore config file
        cmd = "mv -f %s %s"%(backupfile,cfgfile)
        stdout, stderr, rc = _exec_command(cmd)
        
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))                
 
    def set_value_in_MTE_cfg(self, mtecfgfile, tagName, value):
        """change tag value in ${MTE}.xml
        
            params : searchdir - path where search for mte config file
                     mtecfgfile - filename of mte config file
                     tagName - target tagName
                     value - required value
                    
            return : N/A
            
            Examples :
              | set value in_MTE cfg | jsda01.xml | NumberOfDailyBackupsToKeep | 12:00
        """         
        #Find configuration file
        LinuxFSUtilities().remote_file_should_exist(mtecfgfile)

        #Check if <PE> tag exist
        searchKeyWord = "</%s>"%tagName
        foundlines = LinuxFSUtilities().grep_remote_file(mtecfgfile, searchKeyWord)
        if (len(foundlines) == 0):
            raise AssertionError('*ERROR* <%s> tag is missing in %s' %(tagName, mtecfgfile))

        for line in foundlines:
            cmd = "sed -i 's/%s/<%s>%s<\/%s>/' "%(line.replace('/','\/'),tagName,value,tagName)
            cmd = cmd + mtecfgfile
            stdout, stderr, rc = _exec_command(cmd)
        
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))    
    
    def generate_persistence_backup(self, venuedir, MTEName, keepDays):
        """ based on the no. of keeping days generate dummy persistence backup files 
            
            params : venuedir - path where search for persist files
                     MTEName - instance name of MTE
                     keepDays = value found in MTE config tag <NumberOfDailyBackupsToKeep>

            return : N/A
            
            Examples :
                | generate persistence backup | /ThomsonReuters/Venues | JSDA01M | 3
        """
                
        #Persistence backup filename format : PERSIST_${MTE}_YYYYMMDDTHHMMSS.DAT
        dummyRefFile = 'PERSIST_' + MTEName + '.DAT'
        listOfPersistBackupFiles = LinuxFSUtilities().search_remote_files(venuedir, dummyRefFile, True)
        if (len(listOfPersistBackupFiles) == 0):
            raise AssertionError('*ERROR* Persistence file is missing' )
        
        backupfileDir = os.path.dirname(listOfPersistBackupFiles[0])
        tdBoxDatetime = LinuxCoreUtilities().get_date_and_time()
        oneDayInSecond = 60*60*24*-1
        for dayCount in range(0, int(keepDays)+2):
            dummyDatetime = datetime(int(tdBoxDatetime[0]), int(tdBoxDatetime[1]), int(tdBoxDatetime[2]), int('01'), int('00'), int('00')) + timedelta(seconds=int(dayCount*oneDayInSecond))
            targetFile = 'PERSIST_%s_%s%02d%02dT010000.DAT' %(MTEName,dummyDatetime.year,dummyDatetime.month,dummyDatetime.day)
            cmd = "cp -a %s %s"%(listOfPersistBackupFiles[0], backupfileDir + '/' + targetFile)
            stdout, stderr, rc = _exec_command(cmd)
        
            if rc !=0 or stderr !='':
                raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        
    def verify_persistence_cleanup(self, venuedir, MTEName, keepDays):
        """ verify if cleanup action has carried out properly after EndOfDay time
            
            params : venuedir - path where search for persist files
                     MTEName - instance name of MTE
                     keepDays = value found in MTE config tag <NumberOfDailyBackupsToKeep>

            return : N/A
            
            Examples :
             | verify persistence cleanup | /ThomsonReuters/Venues | JSDA01M | 3
        """
            
        #Get a list of persist backup file
        targetFile = 'PERSIST_' + MTEName + '_*.DAT'
        listOfPersistBackupFiles = LinuxFSUtilities().search_remote_files(venuedir, targetFile, True)
        
        # 1. Test Case will use generate_persistence_backup_files() to generate dummy persist backup files
        # 2. Total no. of backup file generated is 1(current day) + keeyDays + 1(Suppose to be cleanup/deleted)
        originalNoOfBackupFile = 1 + int(keepDays) + 1
        if not ((originalNoOfBackupFile - len(listOfPersistBackupFiles)) == 1):
            raise AssertionError('*ERROR* Expected no. of backup file remain after cleanup (%d), but (%d) has found' %(originalNoOfBackupFile-1,len(listOfPersistBackupFiles)))
        
    def run_dataview(self, dataviewPath, dataType, multicastIP, interfaceIP, multicastPort, LineID, RIC, domain, *optArgs):
        """ Argument :
                dataviewPath : DataView full path
                dataType : Could be TRWF2 or RWF
                multicastIP : multicast IP DataView listen to
                multicastPort : muticast port DataView used to get data
                interfaceIP : interface IP (DDNA or DDNB)
                LineID : lineID published by line handler
                RIC : published RIC by MTE
                Domain : published data domain
                optargs : a variable list of optional arguments for refresh request and DataView run time.
            Return: stdout.
            examples:
                DataView -TRWF2 -IM 232.2.19.229 -IH 10.91.57.71  -PM 7777 -L 4608 -R 1YWZ5_r -D MARKET_BY_PRICE  -O output_test.txt -REF -IMSG 232.2.9.0 -PMSG 9000 -S 0  -EXITDELAY 5
                DataView -TRWF2 -IM 232.2.19.229 -IH 10.91.57.71  -PM 7777 -L 4096 -R .[SPSCB1L2_I -D SERVICE_PROVIDER_STATUS -EXITDELAY 5
        """
                            
        # use pathfail to detect failure of a command within a pipeline
        # remove non-printable chars; dataview COMP_NAME output contains binary characters that can cause utf-8 decode problems
        cmd = 'set -o pathfail; %s -%s -IM %s -IH %s -PM %s -L %s -R \'%s\' -D %s ' % (dataviewPath, dataType, multicastIP, interfaceIP, multicastPort, LineID, RIC, domain)
        cmd = cmd + ' ' + ' '.join( map(str, optArgs))
        cmd = cmd + ' | tr -dc \'[:print:],[:space:]\''
        print '*INFO* ' + cmd
        stdout, stderr, rc = _exec_command(cmd)
                
        if rc != 0:
            raise AssertionError('*ERROR* %s' %stderr)    
        
        return stdout 

    def run_HostManger(self, *optArgs):
        """run HostManager with specific arguments
        
        optArgs    : argument that used to run HostManager
        Returns    : stdout of after the command has executed 

        Examples:
        | run HostManager  | -readparams /HKF02M/LiveStandby|
        """         
        cmd = '%s ' %self.HOSTMANAGER
        cmd = cmd + ' ' + ' '.join( map(str, optArgs))
        print '*INFO* ' + cmd
        stdout, stderr, rc = _exec_command(cmd)
                
        if rc != 0:
            raise AssertionError('*ERROR* %s' %stderr)    
        
        return stdout
    
    def verify_MTE_state(self,mteName,state):
        """verify MTE instance is in specific state
        
         Argument:
            mteName  : name of MTE instance
            state    : expected state of MTE (UNDEFINED,LIVE,STANDBY,LOCKED_LIVE,LOCKED_STANDBY)
        
        Returns    : 

        Examples:
        | verify MTE state | HKF02M | LIVE
        """             
     
        stateDict = {'0': 'UNDEFINED', '1': 'LIVE', '2': 'STANDBY', '3' : 'LOCKED_LIVE', '4' : 'LOCKED_STANDBY'};
        
        #verify if input 'state' is a valid one
        if not (state in stateDict.values()):
            raise AssertionError('*ERROR* Invalid input (%s). Valid value for state is UNDEFINED , LIVE , STANDBY , LOCKED_LIVE , LOCKED_STANDBY '%state)
        
        cmd = '-readparams /%s/LiveStandby'%mteName
        ret = self.run_HostManger(cmd).splitlines()
        if (len(ret) == 0):
            raise AssertionError('*ERROR* Running HostManger %s return empty response'%cmd)
     
        idx = '-1'
        for line in ret:
            if (line.find('LiveStandby') != -1):
                contents = line.split(' ')
                idx = contents[-1].strip()
                 
        if (idx == '-1'):
            raise AssertionError('*ERROR* Keyword LiveStandby was not found in response')
        elif not (stateDict.has_key(idx)):
            raise AssertionError('*ERROR* Unknown state %s found in response'%idx)
        elif (stateDict[idx] != state):
                raise AssertionError('*ERROR* %s is not at %s (current state : %s)'%(mteName,state,stateDict[idx]))            
        
    def get_FID_Name_by_FIDId(self,FidId):
        """get FID Name from TRWF2.DAT based on fidID
        
        fidID is the FID ID number. For example 22
        return the corresponding FID Name

        Examples:
        |get FID Name by FIDId | 22 |     
        """
        
        filelist = LinuxFSUtilities().search_remote_files(self.BASE_DIR, 'TRWF2.DAT',True)
        if (len(filelist) == 0):
            raise AssertionError('no file is found, can not located the field ID')
        
        
        #sed -e '/^!/d' %s | sed 's/\"[^\"]*\"/ /'    the command is to remove the comments which begins with symbol ! 
        #and remove the string beginning with " and ending with ", for example in file /reuters/Config/TRWF2.DAT, the 2nd column
        #tr -s ' '  it is to remove repeat symbol ' '(space)
        #cut -d ' ' f1,2  Use symbol ' '(space) as delimiter to split the line and delete the filed f1 and f2
        cmd = "sed -e '/^!/d' %s | sed 's/\"[^\"]*\"/ /' | grep \" %s \" | tr -s ' ' | cut -d ' ' -f1,2 | grep \" %s$\""%(filelist[0],FidId,FidId)
    
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))  
        
        elements = stdout.split()
        
        if (len(elements) == 2 ):
            return elements[0]
        else:
            raise AssertionError('*ERROR* The FID can not be found')
    
    def get_FID_ID_by_FIDName(self,fieldName):
        """get FID ID from TRWF2.DAT based on fidName
        
        fieldName is the FID Name. For example BID, ASK
        return the corresponding FID ID

        Examples:
        |get FID ID by FIDName | ASK |     
        """
        
        filelist = LinuxFSUtilities().search_remote_files(self.BASE_DIR, 'TRWF2.DAT',True)
        if (len(filelist) == 0):
            raise AssertionError('no file is found, can not located the field ID')
        
        #sed 's/\"[^\"]*\"/ /' %s remove the string which begins with symbol " and end with symbol ", 
        #for example in file /reuters/Config/TRWF2.DAT, remove the 2nd column
        #tr -s ' ' remove repeat symbol ' '(space)
        cmd = "sed 's/\"[^\"]*\"/ /' %s | grep \"^%s \" | tr -s ' '" %(filelist[0],fieldName)
        
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))  
        
        elements = stdout.split()
        
        if (len(elements) > 2 ):
            return elements[1]
        else:
            raise AssertionError('*ERROR* The FID can not be found')        

    def rollover_MTE_Machine_Date(self, startOfDay, endOfDay, durationDays=1):   
        """to rollover MTE machine date with the duration days
                
        Argument:         
                    startOfDay   : dateTime object with MTE start of day.
                    endOfDay     : dateTime object with MTE end of day.
                    durationDays : the number of days we want to rollover
                    
         
        return nil
        
        Examples:
                    Rollover MTE Machine Date  |  ${StartOfDayGMT} |   ${EndOfDayGMT}  |  ${days}
        """  
                
        """
        Here is the logic for adjusting start time, end time, and box time.
        Desired state before entering loop is that it is within a session, i.e. startTime < currentTime < EndTime 
        
        currDateTime > startOfDay > endOfDay - set box time to start time
        startOfDay > currDateTime > endOfDay - do nothing
        startOfDay > endOfDay > currDateTime - add a day to start and end; set box to to start time
        currDateTime > endOfDay > startOfDay - subtract a day from start
        endOfDay > currDateTime > startOfDay - add a day to end; set box time to start time
        endOfDay > startOfDay > currDateTime - add a day to end
        """

        aSec = timedelta(seconds = 1)
        aDay = timedelta(days = 1 )
        currTimeArray = LinuxCoreUtilities().get_date_and_time() # current time as array
        currDateTime = datetime(*map(int,currTimeArray)) # current time as dateTime object
            
        if startOfDay < endOfDay:
            if currDateTime > endOfDay:
                # today's session already ended (startTime > endTime > currentTime)
                startOfDay = startOfDay + aDay
                endOfDay = endOfDay + aDay
        else:
            if currDateTime < endOfDay:
                # session started yesterday, session not ended (currentTime > endTime > startTime)
                startOfDay = startOfDay - aDay
            else:
                # next session will end tomorrow (endTime > currentTime > startTime  or endTime > startTime > currentTime)
                endOfDay = endOfDay + aDay
 
        if startOfDay > endOfDay:
            AssertionError('Could not set startOfDay and endOfDay correctly.')

        # set start and end so they are just before the actual start and end times
        startOfDay = startOfDay - aSec
        endOfDay = endOfDay - aSec

        leftDays = int (durationDays) 
         
        while leftDays > 0 :
            # first time thru loop, we may already be past startOfDay, if not, change box time to start the next session.
            # currDateTime < startOfDay will always be true for succesive iterations thru the loop
            if currDateTime < startOfDay:
                LinuxCoreUtilities().set_date_and_time(startOfDay.year, startOfDay.month, startOfDay.day, startOfDay.hour, startOfDay.minute, startOfDay.second)
                currTimeArray = startOfDay.strftime('%Y,%m,%d,%H,%M,%S').split(',')
                currDateTime = datetime(*map(int,currTimeArray))
                self.wait_smf_log_message_after_time('DailyEventScheduleTask Ends',currTimeArray,15,480)
            startOfDay = startOfDay + aDay
            
            LinuxCoreUtilities().set_date_and_time(endOfDay.year, endOfDay.month, endOfDay.day, endOfDay.hour, endOfDay.minute, endOfDay.second)
            currTimeArray = endOfDay.strftime('%Y,%m,%d,%H,%M,%S').split(',')
            currDateTime = datetime(*map(int,currTimeArray))
            self.wait_smf_log_message_after_time('DailyEventScheduleTask Ends',currTimeArray,15,480)
            endOfDay = endOfDay + aDay
            
            leftDays = leftDays - 1
             