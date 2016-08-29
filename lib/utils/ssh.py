'''
Created on May 12, 2014

@author: xiaoqin.li
'''
import re

#from robot.libraries.BuiltIn import BuiltIn
#BuiltInInstance= BuiltIn()

from rc import _rc


from SSHLibrary.library import SSHLibrary

G_SSHInstance = SSHLibrary()

#===============================================================================
# def _get_current_connection():
#     try:
#         sshinstance= BuiltInInstance.get_library_instance('SSHLibrary')
#     except AttributeError:
#         raise AssertionError("*ERROR* please import SSHLibrary and call open_connection first")
#     return sshinstance.current
#===============================================================================

def _get_current_connection():
    return G_SSHInstance.current
    
def _run_command(cmd):
    stdout, stderr, rc = _get_current_connection().execute_command(cmd)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* %s' %stderr)  
    return stdout
    
def _exec_command(cmd):
    stdout, stderr, rc = _get_current_connection().execute_command(cmd)
    return [stdout, stderr, rc]

def _delete_file(name, path, recurse):
    if path == '':
        if isinstance(name, list):
            namestr=''
            for n in name:
                namestr = namestr + "'%s' " %n
            cmd = "rm -f %s" %namestr
        else:
            cmd = "rm -f '%s'" %name
    else:
        if recurse == True:
            cmd ="find %s -type f -name '%s' -exec rm -f {} \;" %(path,name)
        else:
            cmd = "rm -f '%s'/%s" %(path,name)
    
    stdout, stderr, return_code = _get_current_connection().execute_command(cmd)
    if return_code != 0:
        return_code = 1
    return [return_code, stdout, stderr]

def _search_file(path, name, recurse):
    if recurse == True:
        cmd = "find '%s' -type f -name '%s'" %(path,name)
    else:
        cmd = "cd '%s' && find . ! -name . -prune -type f -name '%s'" %(path,name)
    stdout, stderr, rc = _get_current_connection().execute_command(cmd)
    if rc !=0 or stderr !='':
        raise AssertionError("*ERROR* %s, %s" %(rc, stderr))
    filelist =[]
    for filename in stdout.split('\n'):
        if filename.startswith('./'):
            filelist.append(path + filename[1:])
        elif filename != '':
            filelist.append(filename)
    return filelist

def _ls(filename, options):
    cmd = 'ls %s %s' %(filename,options)
    stdout, stderr, rc = _get_current_connection().execute_command(cmd)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* %s' %stderr)  
    return stdout
    
def _count_lines(filename):
    cmd = 'wc -l "%s"' %filename
    stdout, stderr, rc = _get_current_connection().execute_command(cmd)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* %s' %stderr)  
    else:
        pat = re.compile('\d+')
        return int(re.findall(pat,stdout)[0])

def _return_ps_cmd_list():
    cmd = 'ps -eo pid,cmd'
    stdout, stderr, rc = _get_current_connection().execute_command(cmd)
    #stdout, stderr, rc = G_SSHInstance.current.execute_command(cmd)
    if rc != 0:
        raise AssertionError('*ERROR* %s' %stderr)
    return stdout

def _get_process_pid_pattern_dict(process_pattern_list):
    stdout = _return_ps_cmd_list()
    pid_cmd_list = stdout.split('\n')
    dict = {}
    for process_item in pid_cmd_list:
        for pattern_item in process_pattern_list:
            if re.search(pattern_item.lower(), process_item.lower()):
                dict[process_item.split()[0]] = pattern_item
                break
    return dict  


def _return_pslist():
    cmd = 'ps -eo pid,comm='
    stdout, stderr, rc = _get_current_connection().execute_command(cmd)
    #stdout, stderr, rc = G_SSHInstance.current.execute_command(cmd)
    if rc != 0:
        raise AssertionError('*ERROR* %s' %stderr)
    return stdout

def _check_process(processlist):
    stdout = _return_pslist()
    FoundList = []
    NotFoundList = []
    for item in processlist:
        if stdout.lower().find(' ' + item.lower() + '\n') != -1 or stdout.lower().find('/' + item.lower() + '\n') != -1:
            FoundList.append(item)
        else:
            NotFoundList.append(item)
       
    return [FoundList, NotFoundList]   

def _kill_process(pidlist):
    cmd = 'kill -9 %s' % ' '.join(pidlist)
    stdout, stderr, rc = _get_current_connection().execute_command(cmd)
    if rc != 0:
        raise AssertionError('*ERROR* %s' %stderr)

def _get_datetime():
    cmd = 'date +%Y-%m-%d-%H-%M-%S-%w'
    stdout, stderr, rc = _get_current_connection().execute_command(cmd)
    if rc !=0 or stderr !='':
        raise AssertionError("*ERROR* %s, %s" %(rc, stderr))
    return stdout.strip().split('-')

def _set_datetime(year,month,day, hour, min, sec, system='linux'):
    if system == 'linux':
        if year !='' and hour !='':
            cmd = 'date +%Y%m%d%T -s "' + '%04d%02d%02d %02d:%02d:%02d' %(int(year), int(month),int(day),int(hour),int(min),int(sec)) + '"'
        elif year != '':
            #useless
            cmd = 'date +%Y%m%d -s "' + '%04d%02d%02d' %(int(year), int(month),int(day)) + '"'
        elif hour !='':
            cmd = 'date +%T -s "' + '%02d:%02d:%02d' %(int(hour),int(min),int(sec)) + '"'
        else:
            return 6
    if system == 'unix':
        if year !='' and hour !='':
            cmd = 'date ' + '%02d%02d%02d%02d%04d.%02d' %(int(month),int(day),int(hour),int(min), int(year), int(sec))
        elif hour !='':
            cmd = 'date ' + '%02d%02d.%02d' %(int(hour),int(min),int(sec))
        else:
            return 6
    stdout, stderr, rc = _get_current_connection().execute_command(cmd)
    if rc !=0 or stderr !='':
        return 6
    else:
        return 0
    
def _start_command(cmd):
    return _get_current_connection().start_command(cmd)
    
