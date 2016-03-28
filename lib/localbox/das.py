import glob
import os
import os.path
import string
import xml
import xml.etree.ElementTree as ET

from utils.local import _run_local_command
from utils.rc import _rc
from VenueVariables import *

def get_DVT_rule_file():
    """ Search for the local DVT rule file in the LOCAL_DAS_DIR folder, and return it.
        This function will find the latest DVT rule if multiple files is found.
        The rule of deciding the latest rule file is checking the digit in the file name.
        Normally, the file name should be 'TRWFRules-72_L7_v2.1.0_SNFDCMPLR_20151118.xml', '72' can be used for sorting the file.
        
        Argument:
        return : the DVT rule file name
        
        Example:
        ${ruleFilePath} | get_DVT_rule_file |
    """
    files = glob.glob(os.path.join(LOCAL_DAS_DIR, '*TRWFRules*.xml'))
    if len(files) == 0:
        raise AssertionError('*ERROR* Cannot find DVT rule file in %s' %LOCAL_DAS_DIR)
    files.sort(key = lambda x:filter(str.isdigit, os.path.basename(x)))
    return files[-1]  

def run_das_dvt_locally(PcapFile, outputfile, source, filter, rule, ProtocolType='MTP'):
    """ run DAS locally.\n
    PcapFile is the pcap file fullpath.\n
    outputfile is the output file fullpath.\n
    
    return 0 or 4. 0 mean generate output successfully, 4 mean no output generated.
    
    Examples:
    | ${res} | run das dvt locally | C:/Program Files/Reuters Test Tools/DAS | c:/temp/rat2.pcap | c:/temp/1.csv | CHE | All_msgBase_msgKey_name = &quot;!!DAST.PA&quot; | c:/TRWFRules.xml |
    | ${res} | run das dvt locally | C:/Program Files/Reuters Test Tools/DAS | c:/temp/rat2.pcap | c:/temp/1.csv | CVA | All_msgBase_msgKey_name = &quot;!!DAST.PA&quot; | c:/TRWFRules.xml | MTP |
    """
    _gen_dvt_parameter(outputfile, source, filter, rule)
    parameterfile = '%s/parameter_file.xml' %LOCAL_TMP_DIR
    return _run_local_das(PcapFile,parameterfile,outputfile, ProtocolType, source, rule)

def run_das_extractor_locally(PcapFile, outputfile, filter, ProtocolType='MTP', maxFileSize=0):
    """ run DAS locally.\n
    PcapFile is the pcap file fullpath.\n
    outputfile is the output file fullpath. Make sure the suffix is correct, because the suffix will determine the outputFormat.
    
    return 0 or 4. 0 mean generate output successfully, 4 mean no output generated.
    
    Examples:
    | ${res} | run das extractor locally | C:/Program Files/Reuters Test Tools/DAS | c:/temp/rat2.pcap | c:/temp/1.xml | All_msgBase_msgKey_name = &quot;!!DAST.PA&quot; |
    | ${res} | run das extractor locally | C:/Program Files/Reuters Test Tools/DAS | c:/temp/rat2.pcap | c:/temp/1.txt | All_msgBase_msgKey_name = &quot;!!DAST.PA&quot; | MTP |
    | ${res} | run das extractor locally | C:/Program Files/Reuters Test Tools/DAS | c:/temp/rat2.pcap | c:/temp/1.xml | AND(All_msgBase_msgKey_name = &quot;${ric}&quot;, All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;) | MTP |
    """
    _gen_extractor_parameter(outputfile, filter, ProtocolType, maxFileSize)
    parameterfile = '%s/parameter_file.xml' %LOCAL_TMP_DIR
    return _run_local_das(PcapFile,parameterfile,outputfile, ProtocolType,'','')

def _run_local_das(PcapFile, parameterfile, outputfile, ProtocolType, source, rule):
    cmd = 'DASCLI.exe -f "%s" -c "%s" -p %s' % (PcapFile, parameterfile, ProtocolType)
    rc,stdout,stderr = _run_local_command(cmd, True, LOCAL_DAS_DIR)
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

def _gen_extractor_parameter(outputfile, filter, ProtocolType, maxFileSize=0):
    outputformat = os.path.splitext(outputfile)[1][1:]
    if outputformat.lower() == 'txt':
        outputformat = 'TEXT'
    else:
        outputformat = outputformat.upper()
    
    objFile1 = open('%s/parameter_file.xml' %LOCAL_TMP_DIR, 'w')        
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
    return '%s/parameter_file.xml' %LOCAL_TMP_DIR

def _gen_dvt_parameter(outputfile, source, filter, rule):
    objFile1 = open('%s/parameter_file.xml' %LOCAL_TMP_DIR, 'w') 
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
    return '%s/parameter_file.xml' %LOCAL_TMP_DIR
