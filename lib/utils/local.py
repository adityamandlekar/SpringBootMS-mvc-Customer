import subprocess

def _run_local_command(command, return_stdout, workdir=''):
    if workdir:
        if return_stdout:
            p = subprocess.Popen(command, cwd=workdir , stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        else:
            p = subprocess.Popen(command, cwd=workdir , shell=True)
    else:
        if return_stdout:
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        else:
            p = subprocess.Popen(command, shell=True)
    
    if p.returncode != 0 and p.returncode != None:
        raise AssertionError('*ERROR* %s' %p.returncode)
    
    if return_stdout:
        
        stdoutdata, stderrdata = p.communicate()
        if p.returncode != 0:
            return [1, stdoutdata, stderrdata]
        else:
            return [0, stdoutdata, stderrdata]
           
    return [0]