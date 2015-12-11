import re
import os
import glob

from GATSNG.utils.rc import _rc
from GATSNG.utils.localconfig import LocalTemp
from GATSNG.utils.local import _run_local_command

class _ToolUtil():
    def _run_local_das(self, InstallPath, PcapFile, parameterfile, outputfile, ProtocolType, source, rule):
        cmd = 'DASCLI.exe -f "%s" -c "%s" -p %s' % (PcapFile, parameterfile, ProtocolType)
        rc,stdout,stderr = _run_local_command(cmd, True, InstallPath)
        if rc != 0:
            raise AssertionError('*ERROR* %s' %stderr)
        if stdout.lower().find('error') != -1 or stderr.lower().find('error') != -1:
            if 'The handle is invalid' not in stdout:
                raise AssertionError('*ERROR* %s, %s' %(stdout,stderr))
        
        if os.path.exists(outputfile):
            return 0
        else:
            ext = outputfile.rfind('.')
            if (ext != -1):
                outputxmlfiles = outputfile[0:ext] + "*" + outputfile[ext:len(outputfile)] 
                outputxmlfilelist = glob.glob(outputxmlfiles)
                if (len(outputxmlfilelist) == 0):
                    _rc(4)
                    return 4
        
    def _gen_extractor_parameter(self, outputfile, filter, ProtocolType, maxFileSize=0):
        outputformat = os.path.splitext(outputfile)[1][1:]
        if outputformat.lower() == 'txt':
            outputformat = 'TEXT'
        else:
            outputformat = outputformat.upper()
           
        objFile1 = open('%s/parameter_file.xml' %LocalTemp, 'w')        
        objFile1.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        objFile1.write('<module name="EXTRACTOR">\n')
        objFile1.write('    <time start="01/02/1000 06:26:34.3631880" end="01/02/9999 06:26:34.3631880" />\n')
        objFile1.write('    <filter file="%s" />\n' % filter)
        
        if ProtocolType in ('RDC', 'ERP', 'MTP'):
            rebuild = 'True'
        else:
            rebuild = 'False'
    
        objFile1.write('    <output file="%s" format="%s" rebuild="%s" showFID="True" showHex="True" volume="%d" />\n' % (outputfile, outputformat, rebuild, maxFileSize))
        objFile1.write('</module>')          
        objFile1.close()
        return '%s/parameter_file.xml' %LocalTemp
        
    def _gen_dvt_parameter(self, outputfile, source, filter, rule):
        objFile1 = open('%s/parameter_file.xml' %LocalTemp, 'w') 
        objFile1.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        objFile1.write('<module name="TRWFDVT">\n')
        objFile1.write('    <time start="" end="" />\n')
        objFile1.write('    <source name="%s"/>\n' %source)
        objFile1.write('    <filter file="%s"/>\n' % filter)
        objFile1.write('    <TRWFPayloadCheck checked="on"/>\n')
        objFile1.write('    <rule file="%s"/>\n' % rule)
        objFile1.write('    <output file="%s"/>\n' % outputfile)
        objFile1.write('</module>')
        objFile1.close()
        return '%s/parameter_file.xml' %LocalTemp
    
    
    def run_das_extractor_locally(self, InstallPath, PcapFile, outputfile, filter, ProtocolType='MTP', maxFileSize=0):
        """ run DAS locally.\n
        InstallPath is DAS install path.\n
        PcapFile is the pcap file fullpath.\n
        outputfile is the output file fullpath. Make sure the suffix is correct, because the suffix will determine the outputFormat.
        
        return 0 or 4. 0 mean generate output successfully, 4 mean no output generated.
        
        Examples:
        | ${res} | run das extractor locally | C:/Program Files/Reuters Test Tools/DAS | c:/temp/rat2.pcap | c:/temp/1.xml | All_msgBase_msgKey_name = &quot;!!DAST.PA&quot; |
        | ${res} | run das extractor locally | C:/Program Files/Reuters Test Tools/DAS | c:/temp/rat2.pcap | c:/temp/1.txt | All_msgBase_msgKey_name = &quot;!!DAST.PA&quot; | MTP |
        | ${res} | run das extractor locally | C:/Program Files/Reuters Test Tools/DAS | c:/temp/rat2.pcap | c:/temp/1.xml | AND(All_msgBase_msgKey_name = &quot;${ric}&quot;, All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;) | MTP |
        """
        self._gen_extractor_parameter(outputfile, filter, ProtocolType, maxFileSize)
        parameterfile = '%s/parameter_file.xml' %LocalTemp
        return self._run_local_das(InstallPath, PcapFile,parameterfile,outputfile, ProtocolType,'','')
    
        
    def run_das_dvt_locally(self, InstallPath, PcapFile, outputfile, source, filter, rule, ProtocolType='MTP'):
        """ run DAS locally.\n
        InstallPath is DAS install path.\n
        PcapFile is the pcap file fullpath.\n
        outputfile is the output file fullpath.\n
        
        return 0 or 4. 0 mean generate output successfully, 4 mean no output generated.
        
        Examples:
        | ${res} | run das dvt locally | C:/Program Files/Reuters Test Tools/DAS | c:/temp/rat2.pcap | c:/temp/1.csv | CHE | All_msgBase_msgKey_name = &quot;!!DAST.PA&quot; | c:/TRWFRules.xml |
        | ${res} | run das dvt locally | C:/Program Files/Reuters Test Tools/DAS | c:/temp/rat2.pcap | c:/temp/1.csv | CVA | All_msgBase_msgKey_name = &quot;!!DAST.PA&quot; | c:/TRWFRules.xml | MTP |
        """
        self._gen_dvt_parameter(outputfile, source, filter, rule)
        parameterfile = '%s/parameter_file.xml' %LocalTemp
        return self._run_local_das(InstallPath, PcapFile,parameterfile,outputfile, ProtocolType, source, rule)
        
    def _gen_FmsCmd_str(self, headend,port, TaskType, RIC, Domain, HandlerName, Services, InputFile , OutputFile, ClosingRunRule, RebuildConstituent, SIC, ExecutionEndPoint, handlerDropType, RebuildFrom, RebuildSpeed, ResetSequenceNumber, Throttle, SRCFile, InputFile2):
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
         
              
    def _check_fmscmd_log(self, stdout):
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
    
    def run_FmsCmd_with_headend(self, headend, port, InstallPath, TaskType, RIC, Domain, HandlerName='', Services='', InputFile='' , OutputFile='', ClosingRunRule='', RebuildConstituent='', SIC='', ExecutionEndPoint='', handlerDropType='', RebuildFrom='', RebuildSpeed='', ResetSequenceNumber='', Throttle='', SRCFile='', InputFile2=''):
        """      
        FmsCmd usage:\n
        --TaskType            FmsCmd TaskTypes: Process, Extract, Insert, Recon, Close, Rebuild, Drop, UnDrop or DBRebuild, search, compare\n
        --InputFile           Input file for tasks: exl, lxl, icf...\n
        --HandlerName         Specify a handlername or do the task again all handlers on the headend IP and port\n
        --RIC                 RIC used in task\n
        --SIC                 SIC used in task\n
        --Domain              Domain used in task, like MARKET_PRICE\n
        --OutputFile          Output file for tasks: icf...\n
        --Services            Services for Recon task\n
        --ClosingRunRule      Closing Run Rule for Close task\n
        --RebuildConstituents Rebuild Constituents for Rebuild and DBRebuild task\n
        --ExecutionEndPoint   Execution End Point for Drop task: "HandlerAndDownstream", "HandlerOnly" or "DownstreamOnly"\n
        --HandlerDropType     Handler Drop Type for Drop task: "Default", "Purge" or "CloseRecover"\n
        --RebuildFrom         Rebuild from time for DBRebuild task in the format of: "yyyy-MM-dd HH:mm:ss"\n
        --RebuildSpeed        Rebuild speed for DBRebuild task: "SLOW" or "FAST"\n
        --ResetSequenceNumber ResetSequenceNumber for DBRebuild task\n
        --Throttle            Throttle for DBRebuild task as messages per seconds, or 0 for no throttle\n
        --SRCFile             SRC file for dual key changing Process task\n
        --InputFile2          used for icf compare task.\n
        
        Return: [RC, fmscmd log, fmscmd cmd]. RC can be 0 or 5 or 13.
        
        Examples:
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Rebuild | CB.N | MARKET_PRICE |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Rebuild | CB.N | MARKET_PRICE | VAE_1 | NYSE | ${EMPTY} | ${EMPTY} | ${EMPTY} | 62 |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Rebuild | ${EMPTY} | ${EMPTY} | VAE_1 | NYSE | c:/StatsRIC.exl  |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Process | ${EMPTY} | ${EMPTY} | VAE_1 | NYSE | c:/StatsRIC.exl |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Close | CB.N | MARKET_PRICE |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Close | ${EMPTY} | ${EMPTY} | VAE_1 | NYSE | c:/StatsRIC.exl |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Close | ${EMPTY} | ${EMPTY} | VAE_1 | NYSE | c:/StatsRIC.exl | ${EMPTY} | 1000 | 
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Close | CB.N | MARKET_PRICE | VAE_1 | NYSE | ${EMPTY} | ${EMPTY} | 1000 |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Extract | CB.N | MARKET_PRICE | ${EMPTY} | ${EMPTY} | ${EMPTY} |  C:/test.icf |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Extract | ${EMPTY} | ${EMPTY} | ${EMPTY} | ${EMPTY} | C:/test.lric | C:/test.icf |  
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Insert | ${EMPTY} | ${EMPTY} | VAE_1 | NYSE | C:/test.icf |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Insert | ${EMPTY} | ${EMPTY} | ${EMPTY} | ${EMPTY} | C:/test.icf |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Drop |  CB.N  |  MARKET_PRICE |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Drop | CB.N | MARKET_PRICE | VAE_1 | NYSE | ${EMPTY} | ${EMPTY} | ${EMPTY} | ${EMPTY} | ${EMPTY} | HandlerAndDownstream | Default |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Drop | ${EMPTY} | ${EMPTY} | VAE_1 | NYSE | c:/StatsRIC.exl | ${EMPTY} | ${EMPTY} | ${EMPTY} | ${EMPTY} | HandlerAndDownstream | Default |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | UnDrop |  CB.N  |  MARKET_PRICE |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | UnDrop | CB.N | MARKET_PRICE | VAE_1 | NYSE | ${EMPTY} | ${EMPTY} | ${EMPTY} | ${EMPTY} | ${EMPTY} | HandlerAndDownstream | Default |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | UnDrop | ${EMPTY} | ${EMPTY} | VAE_1 | NYSE | c:/StatsRIC.exl | ${EMPTY} | ${EMPTY} | ${EMPTY} | ${EMPTY} | HandlerAndDownstream | Default |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | Recon | ${EMPTY} | ${EMPTY} | VAE_1 | NYSE |
        | ${res} | run fmscmd with headend | 10.35.18.249 | 25000 | C:/FmsCmd/bin | dbrebuild | ${EMPTY} | ${EMPTY} | VAE_1 | NYSE |
        """  
        cmd = self._gen_FmsCmd_str(headend, port, TaskType, RIC, Domain, HandlerName, Services, InputFile, OutputFile, ClosingRunRule, RebuildConstituent, SIC, ExecutionEndPoint, handlerDropType, RebuildFrom, RebuildSpeed, ResetSequenceNumber, Throttle, SRCFile, InputFile2)      
        rc,stdout,stderr = _run_local_command(cmd, True, InstallPath)
        if rc != 0:
            raise AssertionError('*ERROR* %s' %stderr)    
        res = self._check_fmscmd_log(stdout)
        return [res, stdout, cmd]
    
    
    
    def run_FmsCmd (self, headendIP, headendPort, InstallPath, TaskType, *optargs):
        """ 
        Argument :
            headendIP : headend IP
            headendPort : headend FMS client port 25000
            InstallPath : FMSCMD bin path.
            TaskType : possible value [Process, Extract, Search, Insert, Recon, Close, Rebuild, Drop, UnDrop, DBRebuild, Compare, ClsRun]
            optargs : a variable list of optional arguments based on TaskType.
            See detailed FmsCmd parameter list at https://thehub.thomsonreuters.com/docs/DOC-172815
        Return: [RC, fmscmd log, fmscmd cmd]. RC can be 0 or 5 or 13.
        examples:

        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Process | --Services MFDS | --InputFile c:/tmp/nasmf_a.exl | --AllowRICChange true|
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Process | --HandlerName VAE_1 | --Services NYSE | --InputFile c:/StatsRIC.exl |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Rebuild | --RIC CB.N | --Domain MARKET_PRICE |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Rebuild | --RIC CB.N | --Domain MARKET_PRICE | --HandlerName VAE_1 | --Services NYSE | --RebuildConstituents 62 |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Rebuild | --HandlerName VAE_1 | --Services NYSE | --InputFile c:/StatsRIC.exl  |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Close   | --RIC CB.N | --Domain MARKET_PRICE |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Close   | --HandlerName VAE_1 | --Services NYSE | --InputFile c:/StatsRIC.exl |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Close   | --HandlerName VAE_1 | --Services NYSE | --InputFile c:/StatsRIC.exl | --ClosingRunRule 1000 | 
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Close   | --RIC CB.N | --Domain MARKET_PRICE | --HandlerName VAE_1 | --Services NYSE | --ClosingRunRule 1000 |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Extract | --RIC CB.N | --Domain MARKET_PRICE | --InputFile C:/test.icf |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Extract | --InputFile C:/test.lric | --OutputFile C:/test.icf |  
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Insert  | --HandlerName VAE_1 | --Services NYSE | --InputFile C:/test.icf |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Insert  | --InputFile C:/test.icf |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Drop    |  --RIC CB.N | --Domain MARKET_PRICE |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Drop    | --RIC CB.N | --Domain MARKET_PRICE | --HandlerName VAE_1 | --Services NYSE | --ExecutionEndPoint HandlerAndDownstream | --handlerDropType Default |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Drop    | --HandlerName VAE_1 | --Services NYSE | --InputFile c:/StatsRIC.exl | --ExecutionEndPoint HandlerAndDownstream | --handlerDropType Default |
        | ${res=} | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | UnDrop  | --RIC CB.N | --Domain MARKET_PRICE |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | UnDrop  | --RIC CB.N | --Domain MARKET_PRICE | --HandlerName VAE_1 | --Services NYSE | --ExecutionEndPoint HandlerAndDownstream | --handlerDropType Default |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | UnDrop  | --HandlerName VAE_1 | --Services NYSE | --InputFile c:/StatsRIC.exl | --ExecutionEndPoint HandlerAndDownstream | --handlerDropType Default |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | Recon   | --HandlerName VAE_1 | --Services NYSE |
        | ${res}= | run fmscmd | ${IP} | ${Port} | ${LOCAL_FMS_BIN} | dbrebuild | --HandlerName VAE_1 | --Services NYSE |
        """ 
            
            
        cmd = 'FmsCmd.exe --HeadendIP %s --HeadendPort %s --TaskType %s ' % (headendIP, headendPort, TaskType)
        cmd = cmd + ' ' + ' '.join(map(str, optargs))
        rc,stdout,stderr = _run_local_command(cmd, True, InstallPath)
        
        if rc != 0:
            raise AssertionError('*ERROR* %s' %stderr)    
        res = self._check_fmscmd_log(stdout)
        return [res, stdout, cmd]