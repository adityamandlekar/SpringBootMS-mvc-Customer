'''
Created on May 12, 2014

@author: xiaoqin.li
'''

import re
import os
import time

from utils.version import get_version

from utils.ssh import _count_lines, _delete_file, _exec_command, _ls, _run_command, _search_file
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
    
    def create_remote_file_content(self, destination, content):
        G_SSHInstance.write_bare('cat > %s <<END_OF_DATA\n' %destination)
        if type(content) == list:
            for i in content:
                G_SSHInstance.write_bare('%s\n' %i)
        elif str(type(content)).find('dict') != -1:
            for key,value in content.items():
                G_SSHInstance.write_bare('%s=%s\n' %(key,value))
        else:
            G_SSHInstance.write_bare('%s\n' %content)
        G_SSHInstance.write_bare('END_OF_DATA\n')
    
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
   
    def wait_for_search_file(self, topdir, filename, waittime=2, timeout=60):
        """Wait until the remote filename to exist somewhere under the specified directory.

        Arguement topdir is the top directory to do the search from.
        Argument filename may contain UNIX filename wildcard values.
        Argument 'waittime' specifies the time to wait between checks, in seconds.
        Argument 'timeout' specifies the maximum time to wait, in seconds.
        
        Does not return a value; raises an error if the file does not exist within timeout seconds.

        Examples:
        | Wait for searchfile  | VENUE_DIR | filepathname  |
        | Wait for searchfile  | VENUE_DIR | filepathname  | 2  | 30  |
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
    
