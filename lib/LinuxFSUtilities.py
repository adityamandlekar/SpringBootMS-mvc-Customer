'''
Created on May 12, 2014

@author: xiaoqin.li
'''

import re
import os
import time

from utils.version import get_version

from utils.ssh import _delete_file,_search_file, _count_lines,_run_command,_exec_command
from utils.ssh import G_SSHInstance

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
    
    def tail_remote_file(self, path, lines=0):
        """
        Tail a remote file.\n
        
        path is the full path of the file.\n
        lines is the number of lines from the bottom of the file to start the output.\n
        
        This is generally used in conjunction with remote_tail_should_contain or remote_tail_should_contain_regexp
        
        Return null.
        
        Examples:
        | tail remote file | /tmp/1.txt  |
        | tail remote file | /tmp/1.txt  | 20 |
        """
        cmd = 'tail --lines=%d --follow=name --retry %s' %(lines,path)
        G_SSHInstance.write(cmd)

    def remote_tail_should_contain(self, text, maxwait='60 seconds'):
        """
        Read the results from a previous call to tail_remote_file and verify that it contains the specified string.
        
        text is a plain text string.
        maxwait is the maximum time to wait/process the search (default is 60 seconds)
        
        See also remote_tail_should_contain_regexp to search for a regular expression
        
        Returns null.  Fails if string not found within maxwait time
        
        Example:
        | remote file should contain | some text  |
        | remote file should contain | some text  | maxwait=2 minutes |
        """
        defaultTimeout = G_SSHInstance.get_connection(timeout=True)
        G_SSHInstance.set_client_configuration(timeout=maxwait)
        G_SSHInstance.read_until(text)
        G_SSHInstance.set_client_configuration(timeout=defaultTimeout)
    
    def remote_tail_should_contain_regexp(self, pattern, maxwait='60 seconds'):
        """
        Read the results from a previous call to tail_remote_file and verify that it contains the specified pattern.
        
        Pattern is in Python regular expression syntax, http://docs.python.org/2/library/re.html|re module
        Pattern matching is case-sensitive regardless the local or remote operating system
        
        maxwait is the maximum time to wait/process the search (default is 60 seconds)
        
        See also remote_tail_should_contain to search for a simple string
        
        Returns null.  Fails if pattern not found within maxwait time
        
        Example:
        | remote file should contain regexp | Processing.*start.*${MTE} |
        | remote file should contain regexp | Processing.*start.*${MTE} | maxwait=2 minutes |
        """
        defaultTimeout = G_SSHInstance.get_connection(timeout=True)
        G_SSHInstance.set_client_configuration(timeout=maxwait)
        G_SSHInstance.read_until_regexp(pattern)
        G_SSHInstance.set_client_configuration(timeout=defaultTimeout)
    