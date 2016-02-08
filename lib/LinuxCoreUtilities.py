'''
Created on May 12, 2014

@author: xiaoqin.li
'''

#!/usr/bin/env python
import re
import os
import sys

from datetime import datetime, date

from utils.version import get_version
from utils.rc import _rc

from utils.ssh import _check_process, _exec_command, _get_datetime, _set_datetime, _return_pslist, _kill_process
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
    
    def convert_EXL_datetime_to_statblock_format(self,exlDatetime):
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
        pat=re.compile(r'\d+')
        PIDlist = []
        not_found_list = []
        for process in list(Proc):
            findflag =0
            for ps in stdout.split('\n'):
                if ps !='' and (ps.split()[-1] == process or ps.split()[-1].endswith('/' + process)):
                    PIDlist.append(re.findall(pat,ps)[0])
                    findflag =1
            if findflag == 0:
                not_found_list.append(process)
        if PIDlist != []:
            _kill_process(PIDlist)
        if len(not_found_list) != 0:
            return [12,not_found_list]
        else:
            return [0, []]
        
    def show_processes(self):
        return _return_pslist()
    
