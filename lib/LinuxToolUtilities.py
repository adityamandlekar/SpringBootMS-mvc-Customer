'''
Created on May 12, 2015

@author: xiaoqin.li
'''

from __future__ import with_statement

from GATSNG.version import get_version
from GATSNG.utils.rc import _rc

from GATSNG.utils.ssh import G_SSHInstance, _exec_command,_ls,_search_file,_start_command,_check_process

from datetime import date
import time
import string
import os.path

import xml.etree.ElementTree as ET

from LinuxFSUtilities import LinuxFSUtilities
from LinuxCoreUtilities import LinuxCoreUtilities

SMFLOGDIR = '/ThomsonReuters/smf/log/'

class LinuxToolUtilities():
    """A test library providing keywords for run all kinds of tool, for example wirehshark, das, dataview, FMSCMD etc.

    `LinuxToolUtilities` is GATS's standard library.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()
    
    COMMANDER = ''
    STATBLOCKFIELDREADER = ''
    
    def setUtilPath(self, path):
        """Setting the Utilities paths by given base directory for searching
        
        Examples:
        | setUtilPath | '/ThomsonReuters' |   
         """
        self.COMMANDER = _search_file(path,'Commander',True)[0]
        self.STATBLOCKFIELDREADER = _search_file(path,'StatBlockFieldReader',True)[0]

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
            print '*DEBUG* result=%s' %result
            if len(result) > 0:
                return
            time.sleep(waittime)
        raise AssertionError("*ERROR* Process '%s' does not exist (timeout %ds)" %(filename,timeout))

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
            print '*DEBUG* result=%s' %result
            if len(result) == 0:
                return
            time.sleep(waittime)
        raise AssertionError("*ERROR* Process '%s' still exists (timeout %ds)" %(filename,timeout))

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

    def get_smf_log_message(self, message):
        """Reads the smf log file and wait for specific message to show up.

        Argument :
            message : target message going to find in smf log
            waittime : specifies the time to wait between checks, in seconds.
            timeout : specifies the maximum time to wait, in seconds.
        
        Return : list of messages found 

        Examples:
        | wait for smf log message  | FMS REORG DONE |
        """
        cmd = 'date +"%Y%m%d"'
        stdout, stderr, rc = _exec_command(cmd)
        
        targetfile = 'smf log files.' + stdout.strip() + '.txt'
        filenamefullpath = SMFLOGDIR + "/" + targetfile
        LinuxFSUtilities().remote_file_should_exist(filenamefullpath)
                
        #Check message
        foundlines = LinuxFSUtilities().grep_remote_file(filenamefullpath, message)

        return foundlines

    def wait_smf_log_message_after_time(self,message,timeRef, waittime=2, timeout=60):
        """Reads the smf log file and wait for specific message to show up
           Check the message time is after given time (same message could appear many times in the smf.log)

        Argument :
            message : target message going to find in smf log
            time : ref time (HH:MM:SS) to check against the message log time
            waittime : specifies the time to wait between checks, in seconds.
            timeout : specifies the maximum time to wait, in seconds.
        
        Return : Nil if success or raise error

        Examples:
        | wait for smf log message after time | FMS REORG DONE | 06:15:00
        """
        refTime = time.strptime(timeRef,"%H:%M:%S")

        # convert  unicode to int (it is unicode if it came from the Robot test)
        timeout = int(timeout)
        waittime = int(waittime)
        maxtime = time.time() + float(timeout)
        while time.time() <= maxtime:            
            retMessages = self.get_smf_log_message(message)
            if (len(retMessages) > 0):
                logContents = retMessages[-1].split(';')
                if (len(logContents) >= 2):
                    logTime =  time.strptime(logContents[1].strip(),"%H:%M:%S")
                    if (logTime >= refTime):
                        return
            time.sleep(waittime)
        raise AssertionError('*ERROR* Fail to get pattern %s from smf log before timeout %ds' %(message, timeout)) 
             
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
        today = date.today().strftime("%Y%m%d")
        filename = '%s_%s.csv' %(MTEName,today)
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
    
    def get_multicast_address_and_port_for_mte(self,mte):
        """Get multicast address and port for TD MTE

        Argument shortname specifies shortname for MTE
        
        Returns list = [ip,port] or prompt error

        Examples:
        | get multicast address and port by shortname | MFDS1M |
         """         
                
        statblockNames = self.get_stat_blocks_for_category(mte, 'OutputStats')
                                   
        ipAndPort = self.get_stat_block_field(mte, statblockNames[-1], 'multicastOutputAddress').strip().split(':')
        if (len(ipAndPort) != 2):            
            raise AssertionError('*ERROR* Fail to obatin multicast address and port (return %s)'%'|'.join(ipAndPort)) 
        
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
                        if (fid.isdigit() and constit.isdigit() and len(contextID) > 0):
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
        elif len(foundfiles) > 1:
            raise AssertionError('*ERROR* Found more than one file: %s' %cfgfile)     
                
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

    def set_PE_mangling_value(self,enabled,cfgfile):
        """enable or disalbe PE mangling by chaning the content of manglingConfiguration.xml
        enabled : True=enable , False=disable
        cfgfile : full path of mangling config file xml
        Returns : Nil

        Examples:
        | set PE mangling value | True | /ThomsonReuters/Venues/MFDS/MTE/manglingConfiguration.xml |
        """         
        #Find configuration file
        LinuxFSUtilities().remote_file_should_exist(cfgfile)

        #Check if <PE> tag exist
        searchKeyWord = "<PE enabled="
        foundlines = LinuxFSUtilities().grep_remote_file(cfgfile, searchKeyWord)
        if (len(foundlines) == 0):
            raise AssertionError('*ERROR* <PE> tag is missing in %s' %cfgfile)
                
        if (enabled):
            cmd = "sed -i 's/PE enabled=\"false\"/PE enabled=\"true\"/' " + cfgfile
        else:
            cmd = "sed -i 's/PE enabled=\"true\"/PE enabled=\"false\"/' " + cfgfile
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
            dummyDatetime = LinuxCoreUtilities().add_seconds_to_date(tdBoxDatetime[0], tdBoxDatetime[1], tdBoxDatetime[2], '01', '00', '00', dayCount*oneDayInSecond)
            targetFile = 'PERSIST_%s_%s%02d%02dT010000.DAT' %(MTEName,dummyDatetime[0],int(dummyDatetime[1]),int(dummyDatetime[2]))
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
