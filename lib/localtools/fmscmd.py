import re

from utils.local import _run_local_command
from utils.rc import _rc

from VenueVariables import *

def run_FmsCmd (headendIP, TaskType, *optargs):
    """ 
    Argument :
        headendIP : headend IP
        TaskType : possible value [Process, Extract, Search, Insert, Recon, Close, Rebuild, Drop, UnDrop, DBRebuild, Compare, ClsRun]
        optargs : a variable list of optional arguments based on TaskType.
        See detailed FmsCmd parameter list at https://thehub.thomsonreuters.com/docs/DOC-172815
    Return: [RC, fmscmd log, fmscmd cmd]. RC can be 0 or 5 or 13.
    examples:

    | ${res}= | run fmscmd | ${IP} | Process | --Services MFDS | --InputFile c:/tmp/nasmf_a.exl | --AllowRICChange true|
    | ${res}= | run fmscmd | ${IP} | Process | --HandlerName VAE_1 | --Services NYSE | --InputFile c:/StatsRIC.exl |
    | ${res}= | run fmscmd | ${IP} | Rebuild | --RIC CB.N | --Domain MARKET_PRICE |
    | ${res}= | run fmscmd | ${IP} | Rebuild | --RIC CB.N | --Domain MARKET_PRICE | --HandlerName VAE_1 | --Services NYSE | --RebuildConstituents 62 |
    | ${res}= | run fmscmd | ${IP} | Rebuild | --HandlerName VAE_1 | --Services NYSE | --InputFile c:/StatsRIC.exl  |
    | ${res}= | run fmscmd | ${IP} | Close   | --RIC CB.N | --Domain MARKET_PRICE |
    | ${res}= | run fmscmd | ${IP} | Close   | --HandlerName VAE_1 | --Services NYSE | --InputFile c:/StatsRIC.exl |
    | ${res}= | run fmscmd | ${IP} | Close   | --HandlerName VAE_1 | --Services NYSE | --InputFile c:/StatsRIC.exl | --ClosingRunRule 1000 | 
    | ${res}= | run fmscmd | ${IP} | Close   | --RIC CB.N | --Domain MARKET_PRICE | --HandlerName VAE_1 | --Services NYSE | --ClosingRunRule 1000 |
    | ${res}= | run fmscmd | ${IP} | Extract | --RIC CB.N | --Domain MARKET_PRICE | --InputFile C:/test.icf |
    | ${res}= | run fmscmd | ${IP} | Extract | --InputFile C:/test.lric | --OutputFile C:/test.icf |  
    | ${res}= | run fmscmd | ${IP} | Insert  | --HandlerName VAE_1 | --Services NYSE | --InputFile C:/test.icf |
    | ${res}= | run fmscmd | ${IP} | Insert  | --InputFile C:/test.icf |
    | ${res}= | run fmscmd | ${IP} | Drop    |  --RIC CB.N | --Domain MARKET_PRICE |
    | ${res}= | run fmscmd | ${IP} | Drop    | --RIC CB.N | --Domain MARKET_PRICE | --HandlerName VAE_1 | --Services NYSE | --ExecutionEndPoint HandlerAndDownstream | --handlerDropType Default |
    | ${res}= | run fmscmd | ${IP} | Drop    | --HandlerName VAE_1 | --Services NYSE | --InputFile c:/StatsRIC.exl | --ExecutionEndPoint HandlerAndDownstream | --handlerDropType Default |
    | ${res=} | run fmscmd | ${IP} | UnDrop  | --RIC CB.N | --Domain MARKET_PRICE |
    | ${res}= | run fmscmd | ${IP} | UnDrop  | --RIC CB.N | --Domain MARKET_PRICE | --HandlerName VAE_1 | --Services NYSE | --ExecutionEndPoint HandlerAndDownstream | --handlerDropType Default |
    | ${res}= | run fmscmd | ${IP} | UnDrop  | --HandlerName VAE_1 | --Services NYSE | --InputFile c:/StatsRIC.exl | --ExecutionEndPoint HandlerAndDownstream | --handlerDropType Default |
    | ${res}= | run fmscmd | ${IP} | Recon   | --HandlerName VAE_1 | --Services NYSE |
    | ${res}= | run fmscmd | ${IP} | dbrebuild | --HandlerName VAE_1 | --Services NYSE |
    """ 
        
    cmd = 'FmsCmd.exe --HeadendIP %s --HeadendPort %s --TaskType %s ' % (headendIP, FMSCMD_PORT, TaskType)
    cmd = cmd + ' ' + ' '.join(map(str, optargs))
    rc,stdout,stderr = _run_local_command(cmd, True, LOCAL_FMS_BIN)
    
    if rc != 0:
        raise AssertionError('*ERROR* %s' %stderr)    
    res = _check_fmscmd_log(stdout)
    return [res, stdout, cmd]

def _check_fmscmd_log(stdout):
    pattern = re.compile(r'- Information - Job final result: HanderName: .+, Issued: (\d+), Success: (\d+), Error: \d+, Failed: \d+')
    searchresult = pattern.findall(stdout)
    if len(searchresult) == 0:
        _rc(13)           
        return 13
    successNum=0
    issueNum = 0
    for tempstr in searchresult:
        successNum = int(tempstr[1])
        issueNum = int(tempstr[0])
        if successNum < issueNum:         
            _rc(5)           
            return 5
    return 0

def _gen_FmsCmd_str(headend,port, TaskType, RIC, Domain, HandlerName, Services, InputFile , OutputFile, ClosingRunRule, RebuildConstituent, SIC, ExecutionEndPoint, handlerDropType, RebuildFrom, RebuildSpeed, ResetSequenceNumber, Throttle, SRCFile, InputFile2):
    cmd_based = 'FmsCmd.exe --TaskType %s ' % TaskType
    
    if TaskType.lower() in ['rebuild', 'close', 'extract', 'drop', 'undrop']:
        if RIC != '' and Domain != '':
            cmd_str = cmd_based + ' --RIC %s --Domain %s ' % (RIC, Domain)
        elif InputFile != '':
            cmd_str = cmd_based + ' --InputFile "%s" ' % InputFile
        else:
            raise AssertionError('*ERROR* please provide ric and domain or inputfile for %s' % TaskType)
        # rebuild
        if RebuildConstituent != '' and TaskType.lower() == 'rebuild':
            cmd_str = cmd_str + ' --RebuildConstituents "%s"' % RebuildConstituent
        # close
        if ClosingRunRule != '' and TaskType.lower() == 'close':
            cmd_str = cmd_str + ' --ClosingRunRule %s' % ClosingRunRule
        # extract
        if  TaskType.lower() == 'extract':
            if OutputFile == '':
                raise AssertionError('*ERROR* please provide outputfile for %s' % TaskType)
            else:
                cmd_str = cmd_str + ' --OutputFile "%s"' % OutputFile
        # DROP and UnDROP
        if  TaskType.lower() in ['drop', 'undrop']:
            if ExecutionEndPoint != '':
                cmd_str = cmd_str + ' --ExecutionEndPoint %s' % ExecutionEndPoint
            if handlerDropType != '':
                cmd_str = cmd_str + ' --HandlerDropType %s' % handlerDropType
                
        # all
        if HandlerName != '':
            cmd_str = cmd_str + ' --HandlerName %s' % HandlerName
        if Services != '':
            cmd_str = cmd_str + ' --Services %s' % Services
        
    elif TaskType.lower() in ['process', 'insert']:
        if InputFile != '':
            cmd_str = cmd_based + ' --InputFile "%s" ' % InputFile
        else:
            raise AssertionError('*ERROR* please provide inputfile for %s' % TaskType)
        if HandlerName != '':
            cmd_str = cmd_str + ' --HandlerName %s' % HandlerName
        if Services != '':
            cmd_str = cmd_str + ' --Services %s' % Services
        if SRCFile != '' and TaskType.lower() == 'process':
            cmd_str = cmd_str + ' --SRCFile  %s' % SRCFile
    
    elif TaskType.lower() in ['recon', 'dbrebuild']:
        if Services != '':
            cmd_str = cmd_based + ' --Services %s' % Services
        else:
            raise AssertionError('*ERROR* please provide services for %s' % TaskType)
        if HandlerName != '':
            cmd_str = cmd_str + ' --HandlerName %s' % HandlerName
        if TaskType.lower() == 'dbrebuild':
            if RebuildConstituent != '':
                cmd_str = cmd_str + ' --RebuildConstituents "%s"' % RebuildConstituent
            if RebuildFrom != '':
                cmd_str = cmd_str + ' --RebuildFrom "%s" ' % RebuildFrom
            if RebuildSpeed != '':
                cmd_str = cmd_str + ' --RebuildSpeed %s' % RebuildSpeed
            if ResetSequenceNumber != '':
                cmd_str = cmd_str + ' --ResetSequenceNumber '
            if Throttle != '':
                cmd_str = cmd_str + ' --Throttle %s' % Throttle
                
    elif TaskType.lower() in ['search']:
        if RIC != '':
            cmd_str = cmd_based + ' --RIC %s' % RIC
        elif SIC !='':
            cmd_str = cmd_based + ' --SIC %s' % SIC
        else:
            raise AssertionError('*ERROR* please provide RIC or SIC for %s' % TaskType)
        if Domain != '':
            cmd_str = cmd_str + ' --Domain %s' % Domain
        if Services != '':
            cmd_str = cmd_str + ' --Services %s' % Services
        
    elif TaskType.lower() in ['compare']:
        if InputFile != '':
            cmd_str = cmd_based + ' --InputFile "%s" ' % InputFile
        else:
            raise AssertionError('*ERROR* please provide inputfile for %s' % TaskType)
        if InputFile2 != '':
            cmd_str = cmd_str + ' --InputFile2 "%s"' % InputFile2
        if OutputFile == '':
            raise AssertionError('*ERROR* please provide outputfile for %s' % TaskType)
        else:
            cmd_str = cmd_str + ' --OutputFile "%s"' % OutputFile
        
    else:
        raise AssertionError('*ERROR* taskType not correct') 
    
    if headend !='':
        cmd_str = cmd_str +' --HeadendIP %s --HeadendPort %s' %(headend, port)
        
    print '*INFO* %s' % cmd_str
    return cmd_str
