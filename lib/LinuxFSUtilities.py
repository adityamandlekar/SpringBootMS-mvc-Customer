'''
Created on May 12, 2014

@author: xiaoqin.li
'''

import re
import os
import time

from GATSNG.version import get_version

from GATSNG.utils.ssh import _delete_file,_search_file, _count_lines,_run_command,_exec_command
from GATSNG.utils.ssh import G_SSHInstance

class LinuxFSUtilities():
    """A test library providing keywords for file and directory related operations.

    `LinuxFSUtilities` is GATS's standard library.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()
    
    def get_remote_file(self, source, destination='.'):
        return G_SSHInstance.get_file(source, destination)
    
    def put_remote_file(self, source, destination='.', mode='0744', newline=''):
        return G_SSHInstance.put_file(source, destination, mode, newline)
    
    def remote_file_should_exist(self, path):
        G_SSHInstance.file_should_exist(path)
        
    def remote_file_should_not_exist(self, path):
        G_SSHInstance.file_should_not_exist(path)
        
    def delete_remote_files(self,*paths):
        """delete one or more files on IP, all files should be provided with fullpath.\n

        Return [0, delete success info, ''] or [1, '', delete error info]

        Examples:
        | ${res} | delete files | /tmp/tmp.exl | /tmp/1.txt |
        | ${res} | delete files | /tmp/tmp.exl | 
        """
        return _delete_file(list(paths), '', False)
    
    def delete_remote_files_matching_pattern(self, path, name, recurse= False):
        """delete all pattern matching files under desired path on IP.\n
        
        path is the directory.\n
        name support wildcard *, for example GATS*.exl.\n
        recurse default to False, if True, mean recursively find all matching files under all subdirectories.\n
        
        Return [0, delete success info, ''] or [1, '', delete error info]

        Examples:
        | ${res} | delete files matching pattern | /tmp | test* | 
        | ${res} | delete files matching pattern | /tmp | test* | ${True} |
        """
        return _delete_file(name, path, recurse)
    
    def search_remote_files(self, path, name, recurse=False):
        """
        Search files which we expect.\n
        
        path is the path where the files are located.\n
        name can be pattern. * matches everything.\n
        recurse default is False, mean only search the current folder.\n
        
        Return the matched files list under the path. Each file is fullpath.
        
        Examples:
        | ${res} | search files | /tmp | smf* |  
        | ${res} | search files | /tmp | smf* | ${true} |
        """
        return _search_file(path, name, recurse)
    
    def count_remote_lines(self, file):
        """
        count the line number of the file.\n
        
        file should be absolute path.\n
        
        Return the number.
        
        Examples:
        | ${res} | count lines | /tmp/1.txt  | 
        """
        return _count_lines(file)
        
    def grep_remote_file(self, filePath, searchKeyWord, isPattern=True, isCaseSensitive=True, Fromline=0, timeout=0, retry_interval=0):
        """
        this keyword is used to grep keywords in a file, then return matching lines.\n

        filePath is the full path of the file.\n
        searchKeyWord is the keyword filter.\n
        isPattern is the flag indicate if searchKeyword is a normal search string or regular expression pattern.\n
        isCaseSensitive is the flag indicate if searchKeyword is case sensitive.\n
        timeout default to 0, mean not timeout wait.\n
        retry_interval is default to 20, mean every 20s will check the log once.\n
        Fromline default to 0, which mean from which line to search the content.\n
        
        The return value is a list for all the matched lines content.\n
        Empty list would be returned if no matched lines found.\n

        Examples:
        | @list | grep remote file | /result.txt | AB\\.C | ${true} | ${true} |
        | @list | grep remote file | /result.txt | timelimit \\\\d+ | ${true} | ${true} |
        | @list | grep remote file | /result.txt | AB.C | ${false} | ${false} | 60 | 
        """
        returnMatchLines = []
        current = time.time()
        timout_value = float(timeout)
        maxtime = current + timout_value
        while (current <= maxtime):
            if isPattern == False:
                if isCaseSensitive:
                    cmd = r'grep -n -F "%s" "%s"' % (searchKeyWord, filePath)
                else:
                    cmd = r'grep -n -i -F "%s" "%s"' % (searchKeyWord, filePath)  
            else:
                if not isCaseSensitive:
                    cmd = r'grep -n -i -P "%s" "%s"' % (searchKeyWord, filePath)  
                else:
                    cmd = r'grep -n -P "%s" "%s"' % (searchKeyWord, filePath)
            #stdout = _run_command(cmd)
            retInfo = _exec_command(cmd)
            stdout = retInfo[0]
            if len(stdout) < 1:
                if timout_value == 0:
                    break
                current = time.time()
                time.sleep(float(retry_interval))
            else:
                break
        for line in stdout.split('\n'):
            if line and int(line.split(':',1)[0]) >= int(Fromline):
                returnMatchLines.append(line.split(':',1)[1])
        return returnMatchLines
    
    
    
    


