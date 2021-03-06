﻿'''
Created on May 12, 2014

@author: xiaoqin.li
'''

#!/usr/bin/env python
import math
import re
import os
import sys

from datetime import datetime, date

from utils.version import get_version
from utils.rc import _rc

from utils.ssh import _get_process_pid_pattern_dict, _check_process, _exec_command, _get_datetime, _get_datetime_string, _set_datetime, _return_pslist, _kill_process
from utils.ssh import G_SSHInstance
       
class LinuxCoreUtilities():    
    """A test library providing keywords for common basic operations.

    `LinuxCoreUtilities` is GATS's standard library.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()
    
    def open_connection(self, host, alias=None, port=22, timeout=None,
                        newline=None, prompt=None, term_type=None, width=None,
                        height=None, path_separator=None, encoding=None):
        return G_SSHInstance.open_connection(host, alias, port, timeout,
                        newline, prompt, term_type, width,
                        height, path_separator, encoding)
        
    def get_current_connection_index(self):   
        return G_SSHInstance.get_connection(index = True)
        
    def close_connection(self):
        G_SSHInstance.close_connection()
        
    def login(self, username, password, delay='0.5 seconds'):
        return G_SSHInstance.login(username,password,delay)
    
    def switch_connection(self, index_or_alias):
        return G_SSHInstance.switch_connection(index_or_alias)
    
    def close_all_connections(self):
        G_SSHInstance.close_all_connections()
        
    def execute_command(self, command, return_stdout=True, return_stderr=False,
                        return_rc=False):
        return G_SSHInstance.execute_command(command, return_stdout, return_stderr,
                        return_rc)
        
    def start_command(self, command):
        G_SSHInstance.start_command(command)
        
    def read_command_output(self, return_stdout=True, return_stderr=False,
                            return_rc=False):
        return G_SSHInstance.read_command_output(return_stdout, return_stderr,
                            return_rc)

    def block_dataflow_by_port_protocol(self,inOrOut,protocol,port):
        """using iptables command to block specific port and protocol data
        
         Argument:
            inOrOut  : either 'INPUT' or 'OUTPUT'
            protocol : UDP, TCP
            port     : port number
        
        Returns    : 

        Examples:
        | block dataflow by port protocol | INPUT | UDP | 9002
        """  
                
        cmd = "/sbin/iptables -A %s -p %s --destination-port %s -j DROP"%(inOrOut,protocol,port)
        
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        
        cmd = "/sbin/service iptables save"
        
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        
    def check_processes(self, *process):
        """
        Check processes existence. Return Foundlist and NotFoundlist.
        
        Process is the process name, which can be provided one or more items.\n
        
        
        Return [Foundlist, NotFoundlist].

        Examples:
        | ${foundlist} | ${notfoundlist} | check processes | svchost | tts |
        | ${foundlist} | ${notfoundlist} | check processes | svchost | 
        ==>\n
        * check two processes 
        * check one process
        """
        return _check_process(list(process))
    
    def enable_disable_interface(self, interfaceName, status):
        """ Enable or disable the interface

            Argument : interfaceName - should be eth1 ... eth5
                       status - should be enable or disable

            Return :   None
            
            Examples :
            | enable disable interface| eth1 | enable |
        """
        if (status.lower() == 'enable'):
           cmd = 'ifup '
        elif (status.lower() == 'disable'):
            cmd = 'ifdown '
        else:
            raise AssertionError('*ERROR* the status is %s, it should be enable or disable' %status)
        cmd = cmd + interfaceName
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0:
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    
    def find_processes_by_pattern(self, pattern):
        """
        Find processes that match the given pattern.  Return the matching 'ps' lines.

        Examples:
        | ${result}= | find processes by pattern | MTE -c MFDS1M |
        """
        cmd = "ps -ef | grep '%s' | grep -v grep" %pattern   
        stdout, stderr, rc = _exec_command(cmd)
        return stdout.rstrip()
   
    def get_date_and_time(self):
        """
        Get the date and time value.
        
        The return value is list as [year, month, day, hour, min, second, dayofweek]. Each value is a string.
        dayofweek is 0~6. 0 is Sunday, 1~6 is Mon to Sat.

        Examples:
        | ${res} | get date and time |
        """
        return _get_datetime()

    def get_date_and_time_string(self):
        """
        Get the date and time value in string format.
        
        The return datetime string in format of 'YYYY-MM-DD hh:mm:ss', e.g. 2016-09-23 03:47:50.
        It is the supported Date format in robot framework.

        Examples:
        | ${datetime}= | get date and time string |
        """
        return _get_datetime_string()

    def get_day_of_week_as_string(self):
        """
        Get the current day of week from remote machine.
        
        The return value is a 3-char uppercase string [SUN, MON, TUE, WED, THU, FRI, SAT].

        Examples:
        | ${dow}= | get day of week as string |
        """
        dateString = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
        dateInfo = _get_datetime()
        return dateString[int(dateInfo[6])]
    
    def get_day_of_week_from_date(self, year, month, day):
        """
        Get the day of week from given date.
        
        The return value is a 3-char uppercase string [SUN, MON, TUE, WED, THU, FRI, SAT].

        Examples:
        | ${dow}= | get day of week from date | 2015 | 10 | 31 |
        """
        return date(int(year), int(month), int(day)).strftime('%a').upper()
    
    def get_hostname(self):
        """
        Get the hostname of remote machine.

        Examples:
        | ${hostname} | get hostname |
        """
        cmd = 'hostname'
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))       
        return stdout.strip()

    def get_interface_name_by_alias(self,alias):
        """Get network ard interface name by given alias

        Argument alias specifies the alias name that we could find in /etc/hosts
        
        Returns string interfance name or prompt error

        Examples:
        | get interface by alias | DDNA |
        """        
        
        aliasIp = self._get_alias_ip(alias)
        interfaceName = self.get_interface_name_by_ip(aliasIp)
        
        return interfaceName
    
    def get_interface_name_by_ip(self,ip):
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
          
        cmd = 'ip addr' + '| grep "inet ' + ip + '/"' + '| awk \'BEGIN {FS=" "}{print $7}\''
        stdout, stderr, rc = _exec_command(cmd)  
          
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))  
              
        if len(stdout) > 0:
            return stdout.strip()
        
        raise AssertionError('*ERROR* Fail to get the interface name for %s' %ip) 
      

    def get_memory_usage(self):
        """
        Find the memory usage(%) from system
        
        """

        cmd = "egrep \'MemTotal\' /proc/meminfo | sed \'s/[^0-9]*//g\'"
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))       
        total = float(stdout)

        cmd = "egrep \'MemFree\' /proc/meminfo | sed \'s/[^0-9]*//g\'"
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        free = float(stdout)

        usage = math.ceil(((total - free)/total)*100)

        return usage

    
    def Get_process_and_pid_matching_pattern(self, *process_pattern): 
        """
        From process patterns return dictionary contains pid and process_pattern
        Examples:
        | MTE -c ${MTE} | FMSClient  | SCWatchdog |
        
        """
        return _get_process_pid_pattern_dict(list(process_pattern))
    
    def get_time_before_midnight_in_seconds(self):
        """
        Get the time in seconds of remote TD machine before midnight
        E.g. Current local system time of remote TD machine = 23:58:55, it will return the seconds of (00:00:00 - 23:58:55) = 65.
        
        Examples:
        | ${sec} | get time before midnight in seconds |
        """
        #dateInfo return value is list as [year, month, day, hour, min, second, dayofweek]. Each value is a string.
        dateInfo = _get_datetime()
        hour = int(dateInfo[3])
        min = int(dateInfo[4])
        sec = int(dateInfo[5])
        
        currTimeInSec = hour*60*60 + min*60 + sec
        totalSec = 24*60*60
        return totalSec - currTimeInSec
    
    def get_time_in_microseconds(self):
        """
        Get the local system time of remote TD machine in microsecond from midnight

        Examples:
        | ${microsec} | get time in microseconds |
        """
        #dateInfo return value is list as [year, month, day, hour, min, second, dayofweek]. Each value is a string.
        dateInfo = _get_datetime()

        hour = int(dateInfo[3])
        min = int(dateInfo[4])
        sec = int(dateInfo[5])
        return (hour*60*60 + min*60 + sec)*1000000

    def kill_processes(self, *Proc):
        """
        kill process.
        
        Proc is one or more process name.\n
        
        return [rc, not found list]. rc is 0 or 12. 12 mean some processes not found to kill.
        
        Examples:
        | ${res} | kill processes | dataview |
        | ${res} | kill processes | dataview | rdtplybk |
        """
        stdout = _return_pslist()
        pat=re.compile(r'\w+')
        psDict = {}
        PIDlist = []
        not_found_list = []
        # build mapping of process name to the list of associated process ids.
        # the pslist process name is currently limited to display first 15 chars, so we will compare only 15 chars
        for ps in stdout.splitlines():
            psInfo = ps.split()
            if len(psInfo) < 2:
                continue
            # get just the process name, remove everything after first non-alphanumeric
            psProcessName = re.match(pat,psInfo[1]).group()
            if psProcessName != None:
                psCompareProcessName = psProcessName.lower()[:15]
                if psCompareProcessName in psDict:
                    psDict[psCompareProcessName].append(psInfo[0])
                else:
                    psDict[psCompareProcessName] = [psInfo[0]]
        for process in list(Proc):
            compareProcessName = process.lower()[:15]
            if compareProcessName in psDict:
                PIDlist.extend(psDict[compareProcessName])
            else:
                not_found_list.append(process)
        if len(PIDlist):
            _kill_process(PIDlist)
        if len(not_found_list):
            return [12,not_found_list]
        else:
            return [0, []]

    def set_date_and_time(self, year, month,day,hour,min,sec):
        """
        Set the date and time value on Linux.
        
        All parameters can be string or integer. 
        
        The return value is 6 or 0. 6 mean set fail, 0 mean pass.
        
        *NOTE* This is used for Linux system, and if you only set date, please notice the time will be automatically set to 00:00:00.

        Examples:
        | ${res} | set date and time | 2014 | 5 | 6 | 12 | 23 | 59 |
        | ${res} | set date and time | ${2014} | ${5} | ${6} | ${12} | ${23} | ${59} |
        | ${res} | set date and time | ${EMPTY} | ${EMPTY} | ${EMPTY} | 12 | 23 | 59 |
        """
        print '*INFO* Setting date/time to: %04d-%02d-%02d %02d:%02d:%02d' %(int(year),int(month),int(day),int(hour),int(min),int(sec))
        return _set_datetime(year, month,day,hour,min,sec, 'linux')
    
    
    def set_date_and_time_Unix(self, year, month,day,hour,min,sec):
        """
        Set the date and time value on Unix.
        
        All parameters can be string or integer. 
        
        The return value is 6 or 0. 6 mean set fail, 0 mean pass.
        
        Examples:
        | ${res} | set date and time unix | 2014 | 5 | 6 | 12 | 23 | 59 |
        | ${res} | set date and time unix | ${2014} | ${5} | ${6} | ${12} | ${23} | ${59} |
        | ${res} | set date and time unix | ${EMPTY} | ${EMPTY} | ${EMPTY} | 12 | 23 | 59 |
        """
        print '*INFO* Setting date/time to: %04d-%02d-%02d %02d:%02d:%02d' %(int(year),int(month),int(day),int(hour),int(min),int(sec))
        return _set_datetime(year, month,day,hour,min,sec, 'unix')
        
    def show_processes(self):
        return _return_pslist()                   
        
    def unblock_dataflow(self):
        """using iptables command to unblock all ports
        
        Argument   :        
        Returns    : 

        Examples:
        | unblock dataflow | 
        """  
                
        cmd = "iptables -F"
        
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))       
        
        cmd = "/sbin/service iptables save"
        
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
        
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