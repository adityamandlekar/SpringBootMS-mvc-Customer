import string
import re

from utilpath import utilpath
from utils.ssh import _exec_command,_start_command,_check_process

def convert_dataView_response_to_dictionary(dataview_response):
    """ capture the FID Name and FID value from DateView output which return from run_dataview

        Argument : dataview_response - stdout return from run_dataview
                   
        Return : dictionary with key=FID NAME and value=FID value
        
        Examples :
        |convert dataView response to dictionary |  response |
    """        
    
    fidsAndValuesDict = {}
    lines = dataview_response.split('\n')
    for line in lines:
        if (line.find('->') != -1):
            fidAndValue = line.split(',')                
            if (len(fidAndValue) >= 2):
                fidIdAndfidName = fidAndValue[0].split()
                if (len(fidIdAndfidName) == 3):
                    fidsAndValuesDict[fidIdAndfidName[2].strip()] = ' '.join(fidAndValue[1:]).strip()
                else:
                    raise AssertionError('*ERROR* Unexpected FID/value format found in dataview response (%s), expected format (FIDNUM -> FIDNAME, FIDVALUE)' %line) 
            else:
                raise AssertionError('*ERROR* Unexpected FID/value format found in dataview response (%s), expected format (FIDNUM -> FIDNAME, FIDVALUE)' %line)
    
    return fidsAndValuesDict

def convert_dataView_response_to_multiRIC_dictionary(dataview_response,ignoreBlank=True):
    """ capture the FID Name and FID value for each RIC from DateView output which return from run_dataview

        Argument : dataview_response - stdout return from run_dataview
                    ignoreBlank - should entries with blank values be ignored?
                   
        Return : dictionary with key=RIC value = {sub-dictionary with key=FID NAME and value=FID value}
        
        Examples :
        |convert dataView response to multiRIC dictionary |  response |
    """        
    
    currRic = ''
    retDict = {}
    fidsAndValuesDict = {}
    lines = dataview_response.split('\n')
    for line in lines:
        if (line.startswith('Msg Key:')):
            NewRic = line.split(':')[1].strip()
            # Save FID values for current RIC before starting new RIC
            if (currRic):
                if retDict.has_key(currRic):
                    retDict[currRic].update(fidsAndValuesDict)
                else:
                    retDict[currRic] = fidsAndValuesDict
            currRic = NewRic
            fidsAndValuesDict = {}
        elif (line.find('->') != -1):
            fidAndValue = line.split(',')                
            if (len(fidAndValue) >= 2):
                fidIdAndfidName = fidAndValue[0].split()
                if (len(fidIdAndfidName) == 3):
                    fidsAndValuesDict[fidIdAndfidName[2].strip()] = ' '.join(fidAndValue[1:]).strip()
                else:
                    raise AssertionError('*ERROR* Unexpected FID/value format found in dataview response (%s), expected format (FIDNUM -> FIDNAME, FIDVALUE)' %line) 
            else:
                raise AssertionError('*ERROR* Unexpected FID/value format found in dataview response (%s), expected format (FIDNUM -> FIDNAME, FIDVALUE)' %line)
    # Save FID values for last RIC
    if (currRic):
        if retDict.has_key(currRic):
            retDict[currRic].update(fidsAndValuesDict)
        else:
            retDict[currRic] = fidsAndValuesDict
    return retDict

def run_dataview(dataType, multicastIP, interfaceIP, multicastPort, LineID, RIC, domain, *optArgs):
    """ Run Dataview command with specified arguments and return stdout result.
        Argument :
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
                        
    # use pipefail to detect failure of a command within a pipeline
    # remove non-printable chars; dataview COMP_NAME output contains binary characters that can cause utf-8 decode problems
    cmd = 'set -o pipefail; %s -%s -IM %s -IH %s -PM %s -L %s -R \'%s\' -D %s ' % (utilpath.DATAVIEW, dataType, multicastIP, interfaceIP, multicastPort, LineID, RIC, domain)
    cmd = cmd + ' ' + ' '.join( map(str, optArgs))
    cmd = cmd + ' | tr -dc \'[:print:],[:blank:],\\n\''
    print '*INFO* ' + cmd
    stdout, stderr, rc = _exec_command(cmd)
            
    if rc != 0:
        raise AssertionError('*ERROR* %s' %stderr)    
    
    return stdout 

def run_dataview_noblanks(dataType, multicastIP, interfaceIP, multicastPort, LineID, RIC, domain, *optArgs):
    """ Run Dataview command with specified arguments, remove all FIDs with blank value and return stdout result.
        Argument :
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
                        
    # use pipefail to detect failure of a command within a pipeline
    # remove non-printable chars; dataview COMP_NAME output contains binary characters that can cause utf-8 decode problems
    cmd = 'set -o pipefail; %s -%s -IM %s -IH %s -PM %s -L %s -R \'%s\' -D %s ' % (utilpath.DATAVIEW, dataType, multicastIP, interfaceIP, multicastPort, LineID, RIC, domain)
    cmd = cmd + ' ' + ' '.join( map(str, optArgs))
    cmd = cmd + ' | tr -dc \'[:print:],[:blank:],\\n\''
    print '*INFO* ' + cmd
    stdout, stderr, rc = _exec_command(cmd)
    
    #We only do grep if the return stdout is non-empty
    #This is because DataView by default using stderr to show some statistic information i.e. len(stderr) always > 0
    if rc != 0:
        raise AssertionError('*ERROR* %s' %stderr)

    noBlanks = re.sub('.*<blank>\n','',stdout)
   
    return noBlanks

def start_dataview(dataType, multicastIP, interfaceIP, multicastPort, LineID, RIC, domain, outputfile, *optArgs):
    """ Start Dataview command to run in the background and return.  Dataview output will be written to the specified file.  The caller should use 'Stop Dataview' keyword to terminate the Dataview process.
        Argument :
            dataType : Could be TRWF2 or RWF
            multicastIP : multicast IP DataView listen to
            multicastPort : muticast port DataView used to get data
            interfaceIP : interface IP (DDNA or DDNB)
            LineID : lineID published by line handler
            RIC : published RIC by MTE, can be ??? for all rics capture
            Domain : published data domain
            outputfile: the file on the MTE machine which dataview output write to
            optargs : a variable list of optional arguments for refresh request and DataView run time.
        Return: pid of DataView.
        examples:
            ${pid}=    Start Dataview    TRWF2    @{multicastIPandPort}[0]    @{interfaceIPandPort}[0]    @{multicastIPandPort}[1]    ${lineID}
            ...    ${ric}    ${domain}    ${outputFile}    @{optargs}
            DataView -TRWF2 -IM 232.2.19.229 -IH 10.91.57.71 -PM 7777 -L 4608 -R ??? -D MARKET_BY_PRICE  -O output_test.txt -REF -IMSG 232.2.9.0 -PMSG 9000 -S 0 
            DataView -TRWF2 -IM 232.2.19.229 -IH 10.91.57.71 -PM 7777 -L 4096 -R .[SPSCB1L2_I -D SERVICE_PROVIDER_STATUS -O DV_output.txt
            ftp://ftp-coll.stldevnet.reuters.com/release/CI-CD/CATF/Installers/OL%20DataView%20Release%20Notes.txt
    """
    
    # cleanup all existing DataView process
    cmd = 'pkill DataView'
    _exec_command(cmd)

    # use pipefail to detect failure of a command within a pipeline
    # remove non-printable chars; dataview COMP_NAME output contains binary characters that can cause utf-8 decode problems
    cmd = 'set -o pipefail; %s -%s -IM %s -IH %s -PM %s -L %s -R \'%s\' -D %s -O %s' % (utilpath.DATAVIEW, dataType, multicastIP, interfaceIP, multicastPort, LineID, RIC, domain, outputfile)
    cmd = cmd + ' ' + ' '.join( map(str, optArgs))
    print '*INFO* start Dataview:' + cmd
    _start_command(cmd)
    
    cmd = "ps -ef | grep -i 'dataview' | grep -v grep |grep -v pipefail |grep %s"%RIC
    stdout, stderr, rc = _exec_command(cmd)
    pattern = re.compile(r'\w\s+(\d+)')
    pid =''
    if re.findall(pattern, stdout)!=[]:
        pid=re.findall(pattern, stdout)[0]
        return pid
    else:
        raise AssertionError('*ERROR* Cannot find any DataView process' )

def stop_dataview(pidDataView):
    """ Stop Dataview command.
        Argument :
            pidDataView: pid of the DataView which want to stop
        Return: None
    """
    stdout, stderr, rc = _exec_command('kill -SIGINT %s'%pidDataView)
    if rc != 0:
        raise AssertionError('*ERROR* %s' %stderr)
    wait_for_process_to_not_exist(' %s '%pidDataView)

def verify_mangling_from_dataview_response(dataview_response,expected_pe,expected_ricname):
    """ Based on the DataView response to check if the expected Ric could be retrieved from MTE and having expected PE value

        Argument : dataview_response - stdout return from run_dataview
                   expected_pe - a list of expected PE values
                   expected_ricname - expected RIC name
                   
        Return : N/A
        
        Examples :
        |verify mangling from dataview response |  response | [4128, 4245, 4247] | ![HSIU5
    """   
                    
    fidsAndValues = convert_dataView_response_to_dictionary(dataview_response)
    if (len(fidsAndValues) > 0):
        if (fidsAndValues.has_key('PROD_PERM')):
            isPass = False
            for pe in expected_pe: 
                if (fidsAndValues['PROD_PERM'] == pe):
                    isPass = True
                    break
            if not (isPass):
                raise AssertionError('*ERROR* Ric (%s) has PE (%s) not equal to expected value (%s) ' %(expected_ricname, fidsAndValues['PROD_PERM'], expected_pe))
        else:
            raise AssertionError('*ERROR* Missing FID (PROD_PERM) from dataview response ')
    else:
        raise AssertionError('*ERROR* Cannt retrieve Ric (%s) from MTE' %expected_ricname)

def verify_mangling_for_UP_SOURCE_RIC_FID_from_dataview_response(dataview_response,expected_manglingPrefix):

    lines = dataview_response.split('\n')
    for line in lines:
        if (line.find("UP_SOURCE_RIC") != -1):
            splitContents = line.split(" ")
            if (len(splitContents[-1]) >= len(expected_manglingPrefix)):
                if (expected_manglingPrefix != (splitContents[-1])[0:len(expected_manglingPrefix)]):
                    raise AssertionError('*ERROR* UP_SOURCE_RIC (%s) mangling does not matched with expected value (%s)'%(splitContents[-1],expected_manglingPrefix))
                else:
                    return
            else:
                raise AssertionError('*ERROR* UP_SOURCE_RIC (%s) string length is smaller than mangling prefix (%s)'%(splitContents[-1],expected_manglingPrefix))

    raise AssertionError('*ERROR* UP_SOURCE_RIC is not found in dataview response')