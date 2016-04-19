from __future__ import with_statement
from datetime import datetime, timedelta
import glob
import os
import os.path
import string
import time

import das
import fidfilterfile
import statblock
from utils.ssh import _exec_command, _check_process, _start_command
import xmlutilities

FID_CONTEXTID = '5357'

#############################################################################
# Keywords that use local copy of MTE output message capture file
#############################################################################

def get_FidValue_in_message(pcapfile,ricname, msgClass):
    """ To verify the insert icf file can update the changed fid and value correct
    
    Argument :         
                pcapFile : is the pcap fullpath at local control PC                       
                ricname:    
                msgClass: UPDATE or RESPONSE               
              : 
                return : Fid Value pair from pcap
        
    Verify:
             Have 1 C1 message, the changed fids' value is correct
             If need to check all the Fids, all the Fid Value pair same with the defaultFidValue
             
    Example:
            | ${defaultFidsValues}  |  get_FidValue_in_message  |  ${LOCAL_TMP_DIR}/capture_localDefault.pcap  |  ${pubRic} | UPDATE
             | ${defaultFidsValues}  |  get_FidValue_in_message  |  ${LOCAL_TMP_DIR}/capture_localDefault.pcap |  ${pubRic} | RESPONSE
            
    """ 
            
    outputfileprefix = 'updateCheckC1'
      
    if msgClass == 'RESPONSE' :
        filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_constitNum = &quot;1&quot;))'%(ricname)
    elif msgClass == 'UPDATE' :
        filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_UPDATE&quot;, Update_constitNum = &quot;1&quot;))'%(ricname)
    else:
        raise AssertionError('*ERROR* msgClass is not correct, please use UPDATE or RESPONSE' )
    
                   
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,outputfileprefix)
    
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)        
    
    if (len(messages) == 1):            
        fidsAndValues = xmlutilities.xml_parse_get_fidsAndValues_for_messageNode(messages[0])                
    else:
        raise AssertionError('*ERROR* No. of C1 message received not equal to 1 for RIC %s during icf insert, received (%d) message(s)'%(ricname,len(messages)))
    
    
    for delFile in outputxmlfilelist:
        os.remove(delFile)
        
    os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")  
    
    return fidsAndValues

def get_RICs_from_pcap(pcapfile,domain,includeSystemRics=False):
    """ Get the unique set of RIC names from a PCAP file
    
        pcapFile : is the pcap fullpath at local control PC
        domain : in format like MARKET_PRICE, MARKET_BY_PRICE, MARKET_BY_ORDER
        includeSystemRics: should system RICs be included in the list
        return : sorted list of RICs found in pcap file   
    """                
    ricsDict = dict({})
            
    #Check if pcap file exist
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)                       
    
    #Convert pcap file to xml
    outputfileprefix = 'ricList'
    filterDomain = 'TRWF_TRDM_DMT_'+ domain
    filterstring = 'All_msgBase_msgKey_domainType = &quot;%s&quot;' %filterDomain
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,outputfileprefix,20)
    
    for outputxmlfile in outputxmlfilelist:
        _get_RICs_from_das_xml(outputxmlfile, ricsDict, includeSystemRics)
        os.remove(outputxmlfile)
    os.remove(os.path.dirname(outputxmlfile) + "/" + outputfileprefix + "xmlfromDAS.log")
    
    print '*INFO* found %d unique RICs' %len(ricsDict)
    return sorted(ricsDict.keys())

def get_txt_from_pcap(pcapfile, filterstring, outputFilePrefix, maxFileSize=0):
    """ run DAS extractor locally and get DAS extractor's text output file
     Returns List output text file(s). Caller is responsible for deleting this generated text file.        
     Argument : pcap file| filter string| outputFilePrefix
     maxFileSize (MB): =0 mean no control on the output file size, > 0 output file would auto split to multiple files with suffix  filename_x 
    """ 
    outdir = os.path.dirname(pcapfile)
    pcap_to_txt_file_name = 'txtfromDAS.txt'
    outputtxtfile = outdir + "/" + outputFilePrefix + pcap_to_txt_file_name   
    rc = das.run_das_extractor_locally(pcapfile, outputtxtfile, filterstring, 'MTP', maxFileSize)
            
    if (rc == 4 and maxFileSize == 0):
        raise AssertionError('*ERROR* No output file found : no match filter %s '%filterstring)
    
    outputtxtfilelist = []
    #multiple files would be created
    if (maxFileSize != 0):
        outputtxtfiles = ""
        ext = outputtxtfile.rfind('.')
        if (ext != -1):
            outputtxtfiles = outputtxtfile[0:ext] + "*" + outputtxtfile[ext:len(outputtxtfile)] 
            outputtxtfilelist = glob.glob(outputtxtfiles)
            if (len(outputtxtfilelist) == 0):
                raise AssertionError('*ERROR* No output file found : no match filter %s '%filterstring)
    else:
        outputtxtfilelist.append(outputtxtfile)
             
    return outputtxtfilelist

def get_xml_from_pcap(pcapfile, filterstring, outputFilePrefix, maxFileSize=0):
    """ run DAS extractor locally and get DAS extractor's xml output file
     Returns List output xml file(s). Caller is responsible for deleting this generated xml file.        
     Argument : pcap file| filter string| outputFilePrefix
     maxFileSize (MB): =0 mean no control on the output file size, > 0 output file would auto split to multiple files with suffix  filename_x 
    """ 
    outdir = os.path.dirname(pcapfile)
    pcap_to_xml_file_name = 'xmlfromDAS.xml'
    outputxmlfile = outdir + "/" + outputFilePrefix + pcap_to_xml_file_name   
    rc = das.run_das_extractor_locally(pcapfile, outputxmlfile, filterstring, 'MTP', maxFileSize)
            
    if (rc == 4 and maxFileSize == 0):
        raise AssertionError('*ERROR* No output file found : no match filter %s '%filterstring)
    
    outputxmlfilelist = []
    #multiple files would be created
    if (maxFileSize != 0):
        outputxmlfiles = ""
        ext = outputxmlfile.rfind('.')
        if (ext != -1):
            outputxmlfiles = outputxmlfile[0:ext] + "*" + outputxmlfile[ext:len(outputxmlfile)] 
            outputxmlfilelist = glob.glob(outputxmlfiles)
            if (len(outputxmlfilelist) == 0):
                raise AssertionError('*ERROR* No output file found : no match filter %s '%filterstring)
    else:
        outputxmlfilelist.append(outputxmlfile)
             
    return outputxmlfilelist

def validate_messages_against_DVT_rules(pcapfile,rulefile):
    """ Perform DVT Validation
        
        Argument:
        pcapfile : the local pcap file path
        rulefile: the rule file path, see 'get_DVT_rule_file' founction
        return : N/A
        
        Example:
        validate messages against DVT rules | c:\temp\local_capture.pcap | ${ruleFilePath}
    """   
    
    #Check if pcap file exist
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)

    #Check if rule file exist
    if (os.path.exists(rulefile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %rulefile)

    pcappath = os.path.dirname(pcapfile)
    outputfile = os.path.join(pcappath, 'DVT_output.csv')

    res = das.run_das_dvt_locally(pcapfile, outputfile, 'CHE', '', rulefile)
    if res != 0:
        raise AssertionError('*ERROR* DVT validate output file is not generated')
    
    with open (outputfile, "r") as myfile:
        linesRead = myfile.readlines()
    foundErrorHearderLine = 0
    errors = []
    for line in linesRead:
        if len(line) != 0:
            if line.startswith('Packet#'):
                foundErrorHearderLine = 1
                continue
            if foundErrorHearderLine == 1:
                errors.append(line)

    if len(errors) != 0:
        for str in errors:
            print '*ERROR* DVT Violation: %s' %str
        raise AssertionError('*ERROR* Found DVT violation')
    os.remove(outputfile)

def verify_all_response_message_num(pcapfile,ricname):
    """ keyword used to verify the response message for RIC in MTE output pcap message, 
        pcapFile : is the pcap fullpath at local control PC  
        ricname : target ric name            
        return : Nil
        
        verify:
        1. C0 , C1 and C63 message response 
        
        example:
        verify all response message num  |   ${LOCAL_TMP_DIR}/capture_local.pcap  |   ${pubRic}
    """   
    _verify_response_message_num_with_constnum(pcapfile,ricname,0)    
    _verify_response_message_num_with_constnum(pcapfile,ricname,1)    
    _verify_response_message_num_with_constnum(pcapfile,ricname,63)

def verify_ClosingRun_message_in_messages(pcapfile,ricname):
    """ verify ClosingRun message for RIC in MTE output pcap message
        pcapFile : is the pcap fullpath at local control PC
        ricname : target ric name    
        return : Nil
        
        Examples:
        | verify ClosingRun message in messages  | C:\\temp\\capture_local.pcap  |  /ThomsonReuters/Venues/ | C:\\Program Files\\Reuters Test Tools\\DAS |   AAAAX.O |              
    """           
    #Check if pcap file exist
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)                       
    
    outputfileprefix = 'ClosingRun'
    filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_UPDATE&quot;, AND(Update_itemSeqNum != &quot;0&quot;, Update_constitNum = &quot;1&quot;)))'%(ricname)
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,outputfileprefix)
    
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
    
    if (len(messages) == 1):
        updateType = xmlutilities.xml_parse_get_field_for_messageNode(messages[0],'UpdateTypeNum')
        if (updateType != '6'):
            raise AssertionError('*ERROR* ClosingRun message for RIC (%s) not found'%(ricname))                   
    else:
        raise AssertionError('*ERROR* No. of ClosingRun message received not equal to 1 for RIC %s during RIC ClosingRun, received (%d) message(s)'%(ricname,len(messages)))        
    
    for delFile in outputxmlfilelist:
        os.remove(delFile)
    
    os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")

def verify_CMP_NME_ET_in_message(pcapfile, ric):
    """ Verify CMP_NME_ET in message, it should be 0 or 1 or 2 or 3

        Argument : pcapfile - the full name of pacpfile, it should be local path e.g. C:\\temp\\capture.pcap
                   ric - the specified ric name if you want to check

        Return : Nil
        
        Examples :
        verify CMP_NME_ET in message | capture.pcap | C:\\Program Files\\Reuters Test Tools\\DAS | AAAX.O |
        
    """
    #Check if pcap file exist
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)
    #Build the filterstring
    filterstring = _build_DAS_filter_string('*', ric, 0);
    
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,'setIDVerificationVspcap',20)
    
    messageNode = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfilelist[0], 'Message')
    
    fidsAndValues = xmlutilities.xml_parse_get_fidsAndValues_for_messageNode(messageNode[0])

    ricname = xmlutilities.xml_parse_get_field_from_MsgKey(messageNode[0],'Name')

    if (len(fidsAndValues) == 0):            
        raise AssertionError('*ERROR* Empty payload found in response message for Ric=%s' %ricname)
    
    FID = '6397'
    if (fidsAndValues.has_key(FID)):                        
        if (fidsAndValues[FID] != '0' and fidsAndValues[FID] != '1' and fidsAndValues[FID] != '2' and fidsAndValues[FID] != '3'):
            raise AssertionError('*ERROR* CMP_NME_ET in message (%s) not equal to 0 or 1 or 2 or 3')
    else:
        raise AssertionError('*ERROR* Missing FID (%s) in message '%FID)
    
    for delFile in outputxmlfilelist:
        os.remove(delFile)

def verify_correction_change_in_message(pcapfile,ricname,FIDs,newFIDValues):
    """ verify correction type changes in  MTE output pcap message
        pcapFile   : is the pcap fullpath at local control PC  
        ricname    : ric name that involved in correction change
        FIDs       : list of FIDs want to verify
        newFIDValues : list of FID values to check if value change is successfully or not
        return : Nil
                
        Examples:
        | verify correction change in message  | C:\\temp\\capture_local.pcap | C:\\Program Files\\Reuters Test Tools\\DAS |AAAAX.O|['3'] |['NewValue']            
    """   
                         
    outputfileprefix = 'correctionUpdateChk'
    filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, Update_updateTypeNum = &quot;TRWF_TRDM_UPT_CORRECTION&quot;)'%(ricname)
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,outputfileprefix)
            
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
            
    if (len(messages) == 1):
        fidsAndValues = xmlutilities.xml_parse_get_fidsAndValues_for_messageNode(messages[0])
        
        if (len(FIDs) != len(newFIDValues)):
            raise AssertionError('*ERROR* no. of item found in FIDs list (%d) and new FID values list (%d) is not equal'%(len(FIDs),len(newFIDValues)))
        
        for idx in range(0,len(FIDs)):                    
            _verify_FID_value_in_dict(fidsAndValues, FIDs[idx], newFIDValues[idx])
    else:
        raise AssertionError('*ERROR* No. of correction message received not equal to 1 for RIC %s received (%d) message(s)'%(ricname,len(messages)))                                
    
    for delFile in outputxmlfilelist:
        os.remove(delFile)
    
    os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")

def verify_correction_updates_in_capture(pcapfile):
    """ verify if correction update messages are in pcapfile.
        Argument : pcapfile : MTE output capture pcap file fullpath
        return : Nil
    """           
    verify_updated_message_exist_in_capture(pcapfile, 'MARKET_PRICE')                  
    
    outputfileprefix = 'correction_pcap'
    filterstring = 'AND(All_msgBase_msgKey_domainType = &quot;TRWF_TRDM_DMT_MARKET_PRICE&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_UPDATE&quot;, Update_updateTypeNum != &quot;TRWF_TRDM_UPT_CORRECTION&quot;))'
    try:
        outputxmlfile = get_xml_from_pcap(pcapfile, filterstring, outputfileprefix)                
    except AssertionError:
        print 'update messages with market price domain in pcap file have correction type '
        return   
    
    if (os.path.exists(outputxmlfile[0]) == True): 
        for exist_file in outputxmlfile:
            os.remove(exist_file)
        os.remove(os.path.dirname(outputxmlfile[0]) + "/" + outputfileprefix + "xmlfromDAS.log")   
        raise AssertionError('*ERROR* updates for Market Price domain have type other than "correction" ' )      

def verify_DROP_message_in_itemstatus_messages(pcapfile,ricname):
    """ verify DROP message for RIC in MTE output pcap message
        pcapFile : is the pcap fullpath at local control PC  
        ricname : target ric name    
        return : Nil
        
        Verify:
        1. C0 Item Status, ContainerType value is NoData 
        2. C1 Item Status, ContainerType value is NoData
        3. C63 Item Status, ContainerType value is NoData
        
        Examples:
        | verify DROP message in itemstatus messages  | C:\\temp\\capture_local.pcap  |  /ThomsonReuters/Venues/ | C:\\Program Files\\Reuters Test Tools\\DAS |   AAAAX.O |              
    """           
    #Check if pcap file exist
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)                       
    
    #C0
    _verify_DROP_message_in_specific_constit_message(pcapfile,ricname,0)
    
    #C1
    _verify_DROP_message_in_specific_constit_message(pcapfile,ricname,1)
    
    #C63
    _verify_DROP_message_in_specific_constit_message(pcapfile,ricname,63)

def verify_fid_in_fidfilter_by_contextId_against_message(messageNode,fidfilter,contextId,constit):
    """ verify MTE output (per message) FIDs found in FIDFilter.txt given context ID and constit
         messageNode : iterator pointing to one message node
         fidfilter : dictionary of FIDFilter.txt
         context Id : context Id that want to check 
         constit : constituent number that want to check      
        return : Nil
        Assertion : 
        (1) Empty payload detected
        (2) FID is not found in FIDFilter.txt given contextId     
    """ 
    
    fidsAndValues = xmlutilities.xml_parse_get_fidsAndValues_for_messageNode(messageNode)
    ricname = xmlutilities.xml_parse_get_field_from_MsgKey(messageNode,'Name')        
        
    if (len(fidsAndValues) == 0):            
        raise AssertionError('*ERROR* Empty payload found in response message for Ric=%s' %ricname)
    
    for fid in fidsAndValues.keys():
        if (fidfilter[contextId][constit].has_key(fid) == False):
            raise AssertionError('*ERROR* FID %s is not found in FIDFilter.txt for Ric=%s has published' %(fid,ricname))
        
def verify_fid_in_fidfilter_by_contextId_and_constit_against_pcap(pcapfile,contextId,constit):
    """ compare  value found in FIDFilter.txt against MTE output pcap by given context Id and constituent
        pcapFile : is the pcap fullpath at local control PC        
        return : Nil
        Assertion : If DAS fail to convert pcap to xml file
        
        [Assumption] :
        (1) Pcap file is from MTE output
    """                
            
    #Check if pcap file exist
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)                       

    #Get the fidfilter and checking input argument context ID and constituent is valid in FIDFilter.txt
    fidfilter = fidfilterfile.get_contextId_fids_constit_from_fidfiltertxt()
    if (fidfilter.has_key(contextId) == False):
        raise AssertionError('*ERROR* required context ID %s not found in FIDFilter.txt '%contextId)
    elif ((fidfilter[contextId].has_key(constit) == False)):
        raise AssertionError('*ERROR* required constituent %s not found in FIDFilter.txt '%constit)          
            
    #For Response
    _verify_fid_in_fidfilter_by_contextId_and_constit_against_pcap_msgType(pcapfile,fidfilter,contextId,constit,'Response')
    
    #For Update
    _verify_fid_in_fidfilter_by_contextId_and_constit_against_pcap_msgType(pcapfile,fidfilter,contextId,constit,'Update')  

def verify_fid_in_range_against_message(messageNode,fid_range):
    """ verify MTE output FIDs is within specific range from message node
         messageNode : iterator pointing to one message node
         fid_range : list with content [min_fid_id,max_fid_id]       
        return : Nil
        Assertion : 
        (1) Empty payload detected
        (2) FID is out side the specific range        
    """ 
            
    fidsAndValues = xmlutilities.xml_parse_get_fidsAndValues_for_messageNode(messageNode)
    ricname = xmlutilities.xml_parse_get_field_from_MsgKey(messageNode,'Name')        
        
    if (len(fidsAndValues) == 0):            
        raise AssertionError('*ERROR* Empty payload found in response message for Ric=%s' %ricname)
    
    for fid in fidsAndValues.keys():
        if (int(fid) < fid_range[0] or int(fid) > fid_range[1]):
            raise AssertionError('*ERROR* FID %s is out of range[%s,%s] for Ric=%s' %(fid,fid_range[0],fid_range[1],ricname))

def verify_fid_in_range_by_constit_against_pcap(pcapfile,constit,fid_range=[-36768,32767]):
    """ verify MTE output FIDs is within specific range and specific constituent
         pcapfile : MTE output capture pcap file fullpath
         fid_range : list with content [min_fid_id,max_fid_id]
         constit : constituent number that want to check
        return : Nil      
    """ 
          
    #Check if pcap file exist
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* Pcap file is not found at %s' %pcapfile)    
    
    #Check valid Range
    if ((isinstance(fid_range,list) == False) or (len(fid_range) < 2) or (fid_range[1] < fid_range[0])):
        raise AssertionError('*ERROR* fid_range need to be list type with [min,max]  %s' %fid_range)

    #Checking Response
    _verify_fid_in_range_by_constit_against_pcap_msgType(pcapfile,fid_range,constit)
    
    #Checking Update
    _verify_fid_in_range_by_constit_against_pcap_msgType(pcapfile,fid_range,constit,'Update')

def verify_fid_value_in_message(pcapfile, ric, constitNum, fidList=[], valueList=[]):
    """ Verify if the fid value equals to the specified value

        Argument : pcapfile - the full name of pacpfile, it should be local path e.g. C:\\temp\\capture.pcap
                   ric - the specified ric name if you want to check
                   constitNum - the constitNum you want to check, should be 0, 1 or 63
                   fidList - a list specify the fid you want to check
                   valueList - a list specify the value you want to compare, it should 1:1 correspond with valueList

        Return : Nil
        
        Examples :
        verify fid in message | capture.pcap | C:\\Program Files\\Reuters Test Tools\\DAS | AAAX.O | 1 | ['6401', '6480'] | ['12345','.[SPSMFDS1M_0'] |
        
        The example shows to verify if the RIC publishs the DDS_DSO_ID(6401) equals 12345 and SPS_SP_RIC(6480) equals .[SPSMFDS1M_0.
    """        
    #Check if pcap file exist
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)
    #Build the filterstring
    filterstring = _build_DAS_filter_string('Response', ric, constitNum);
    
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,'fidVerificationVspcap',20)
    
    messageNode = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfilelist[0], 'Message')
    
    fidsAndValues = xmlutilities.xml_parse_get_fidsAndValues_for_messageNode(messageNode[0])

    ricname = xmlutilities.xml_parse_get_field_from_MsgKey(messageNode[0],'Name')

    if (len(fidsAndValues) == 0):            
        raise AssertionError('*ERROR* Empty payload found in response message for Ric=%s' %ricname)
    
    if (len(fidList) != len(valueList)):
        raise AssertionError('*ERROR* The item number of fidList and valueList is not same' )
    
    i = 0
    for fid in fidList:
        if (fid == None):
            raise AssertionError('*ERROR* One fid in fidList is None' )
        if (valueList[i] == None):
            raise AssertionError('*ERROR* One value in valueList is None' )
        _verify_FID_value_in_dict(fidsAndValues, fid, valueList[i])
        i += 1
        
    for delFile in outputxmlfilelist:
        os.remove(delFile)
           
def verify_FIDfilter_FIDs_are_in_message(pcapfile):
    """ compare  value found in FIDFilter.txt against MTE output pcap
        pcapFile : is the pcap fullpath at local control PC  
        return : Nil
        
        [Assumption] :
        (1) Pcap file is from MTE output
        (2) We only focus on Response message        
    """                
    # Dictionary with key = ric name and content = context ID
    # Captured during verify constit=1 response message and used for verify constit=0 response message
    ricsDict = dict({})
            
    #Check if pcap file exist
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)                       
    
    #[ConstitNum = 1]
    #Convert pcap file to xml
    filterstring = 'AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_constitNum = &quot;1&quot;)'
    outputxmlfilelist_1 = get_xml_from_pcap(pcapfile,filterstring,'fidfilterVspcapC1',20)
    
    #Get the fidfilter
    fidfilter = fidfilterfile.get_contextId_fids_constit_from_fidfiltertxt()
    
    for outputxmlfile in outputxmlfilelist_1:
        _verify_FIDfilter_FIDs_are_in_message_from_das_xml(outputxmlfile, fidfilter, ricsDict)
            
    #[ConstitNum = 0]
    #Convert pcap file to xml
    filterstring = 'AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_constitNum = &quot;0&quot;)'
    outputxmlfilelist_0 = get_xml_from_pcap(pcapfile,filterstring,'fidfilterVspcapC0',20)
    
    #Get the fidfilter
    fidfilter = fidfilterfile.get_contextId_fids_constit_from_fidfiltertxt()
    
    for outputxmlfile in outputxmlfilelist_0:
        _verify_FIDfilter_FIDs_are_in_message_from_das_xml(outputxmlfile, fidfilter, ricsDict)        
    
    print '*INFO* %d Rics verified'%(len(ricsDict))
       
    for delFile in outputxmlfilelist_0:
        os.remove(delFile)
    os.remove(os.path.dirname(outputxmlfilelist_0[0]) + "/fidfilterVspcapC1xmlfromDAS.log")
        
    for delFile in outputxmlfilelist_1:
        os.remove(delFile)          
    os.remove(os.path.dirname(outputxmlfilelist_1[0]) + "/fidfilterVspcapC0xmlfromDAS.log")

def verify_key_compression_in_message(pcapfile, ric):
    """ Verify if the key name compression is enabled 

        Argument : pcapfile - the full name of pacpfile, it should be local path e.g. C:\\temp\\capture.pcap
                   ric - the specified ric name if you want to check
        Return : Nil
        
        Examples :
        verify key compression in message | capture.pcap | C:\\Program Files\\Reuters Test Tools\\DAS | AAAX.O | 
        
    """        
    #Check if pcap file exist
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)
    #Build the filterstring
    filterstring = _build_DAS_filter_string('*', ric);
    
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,'setIDVerificationVspcap',20)
    
    messageNode = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfilelist[0], 'Message')
    for node in messageNode:
        NameEncodingType = xmlutilities.xml_parse_get_field_from_MsgKey(node,'NameEncodingType')
        print NameEncodingType
        if NameEncodingType == '0':
                raise AssertionError('*ERROR* The compression in message is %s ' % (NameEncodingType))
    
    for delFile in outputxmlfilelist:
        os.remove(delFile)

def verify_message_fids_are_in_FIDfilter(localPcap, ric, domain, contextId):
    '''
     verify that message's fids set from pcap for the ric, with domain, contextId is the subset of the fids set defined in FidFilter file for a particular constituent under the context id
    '''
    constituents = fidfilterfile.get_constituents_from_FidFilter(contextId)
    for constituent in constituents:
        # create fidfilter fids set under contextId and constituent
        contextIdMap = fidfilterfile.get_contextId_fids_constit_from_fidfiltertxt()
        constitWithFIDs = contextIdMap[contextId]
        fidsdict = constitWithFIDs[constituent]
        fidsList = fidsdict.keys()
        filterFilefidsSet = frozenset(fidsList);
        
        # create filter string for each constituent to get the message fids set
        filterDomain = 'TRWF_TRDM_DMT_'+ domain
        filterstring = 'AND(All_msgBase_msgKey_domainType = &quot;%s&quot;, AND(All_msgBase_msgKey_name = &quot;%s&quot;, Response_constitNum = &quot;%s&quot;))'%(filterDomain, ric, constituent)
        outputfile = get_xml_from_pcap(localPcap, filterstring, "out1")
        msgFidSet = xmlutilities.get_all_fid_names_from_xml(outputfile[0])
       
        # test messages' fids set are sub-set of the fidfilter's fids set for the constituent under contextId
        # this also reflect that there are no duplicated payload FIDs between constituent (C0, C1 etc)
        os.remove(outputfile[0])
        
        if filterFilefidsSet.issuperset(msgFidSet):
            print '*INFO* fids from messages match fids defined in fidfilter file for contextID %s, constituent %s with RIC %s, domain %s' %(contextId, constituent, ric, domain)
        else:
            commonFids = msgFidSet.intersection(filterFilefidsSet)
            unmatchedFids = msgFidSet - commonFids
            raise AssertionError('*ERROR* not all fids from messages match fids defined in fidfilter file.\n       Unmatched fids are %s' % unmatchedFids) 
        
        # if constituent is 63 verify all FIDs are negative
        if constituent == '63':
            for fid in msgFidSet:
                if fid > 0:
                    raise AssertionError ('*ERROR* NONE negtive fid exists for contextID %s, constituent %s with RIC %s, domain %s' %(contextId, constituent, ric, domain))

def verify_MTE_heartbeat_in_message(pcapfile,intervalInSec):
    """ verify MTE heartbeat in  MTE output pcap message
        pcapFile : is the pcap fullpath at local control PC  
        intervalInSec : expected interval that one heartbeat should sent out   
        return : Nil
                
        Examples:
        | verify MTE heartbeat in message  | C:\\temp\\capture_local.pcap | C:\\Program Files\\Reuters Test Tools\\DAS | 1 |            
    """ 
    
    #Convert pcap to .txt 
    #Remark : getting MTP_ARB_FLAG_POLLING from pcap, we MUST convert it to text format (not support for xml)
    outputfileprefix = 'mteHeartbeat'
    filterstring = 'MTP_ArbFlag = &quot;MTP_ARB_FLAG_POLLING&quot;'
    outputtxtfilelist = get_txt_from_pcap(pcapfile,filterstring,outputfileprefix)
    
    #Capture frame information
    frameTimestamps = []
    try:            
        with open(outputtxtfilelist[0]) as fileobj:    
            for line in fileobj:            
                if (line.find('Frame ') >= 0):            
                    content = line.split(' ')
                    timestampFound = False
                    for searchTimestamp in content:
                        if (searchTimestamp.count(':') == 2):
                            timestampFound = True
                            timestamp = searchTimestamp.split('.')
                            if (len(timestamp) != 2):
                                raise AssertionError('*ERROR* Unexpected timestamp format %s (Expected hh:mm:ss.xxxxxxx' %searchTimestamp)
                            frameTimestamps.append(datetime.strptime(timestamp[0],"%H:%M:%S"))    
                            break
                    if (timestampFound == False):
                        raise AssertionError('*ERROR* Missing timestamp information in %s' %line)      
    except IOError:            
        raise AssertionError('*ERROR* failed to open file %s' %outputtxtfilelist[0])
    
    #Check if heartbeat sent at interval
    if (len(frameTimestamps) == 1):
        raise AssertionError('*ERROR* Only one Heartbeat message found from pcap capture')
    
    requirement = timedelta(seconds=int(intervalInSec))
    delta = timedelta(seconds=1)
    for idx in range (0,len(frameTimestamps)-1):
            diff = frameTimestamps[idx+1] - frameTimestamps[idx]
            if (diff > requirement + delta):
                raise AssertionError('*ERROR* Heartbeat interval in message is (%s) bigger than requirement (%s)' %(diff,requirement+delta))
    
    #Remove files
    for delFile in outputtxtfilelist:
        os.remove(delFile)          
    os.remove(os.path.dirname(outputtxtfilelist[0]) + "/mteHeartbeattxtfromDAS.log")

def verify_no_realtime_update_type_in_capture( pcapfile, domain):
    """ Verify update message does not exist for MARKET PRICE, or MARKET_BY_ORDER or MARKET_BY_PRICE domain.
        Argument : pcapfile : MTE output pcap file fullpath
                   domain : in format like MARKET_PRICE, MARKET_BY_PRICE, MARKET_BY_ORDER
        return : Nil
    """  
    try:
        verify_updated_message_exist_in_capture(pcapfile, domain)     
    except AssertionError:
        return
           
    raise AssertionError('*ERROR* realtime updates exist for domain %s.' %domain)

def verify_PE_change_in_message(pcapfile,ricname,oldPEs,newPE):
    """ verify PE Change response for RIC in MTE output pcap message
        pcapFile : is the pcap fullpath at local control PC  
        ricname : target ric name
        oldPEs : a list of possible original PEs (We use a list of candidates due to the fact we use hardcode way for RIC Mangling test cases)  
        newPE : new value of PE
        return : Nil
        
        Verify:
        1. C1 Response, OLD PE in header, New PE in payload, no other FIDs included
        2. C0 Response, new PE in header
        3. C1 Response, new PE in header, all payload FIDs included
        4. C63 Response, new PE in header, all payload FIDs included.
        
        Examples:
        | verify PE change in message  | C:\\temp\\capture_local.pcap  |  /ThomsonReuters/Venues/ | C:\\Program Files\\Reuters Test Tools\\DAS |   AAAAX.O |  2600| 12341 |            
    """           
    #Check if pcap file exist
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)                       
    
    #C0
    _verify_PE_change_in_message_c0(pcapfile,ricname,newPE)
    
    #C1
    _verify_PE_change_in_message_c1(pcapfile,ricname,oldPEs,newPE)
    
    #C63
    _verify_PE_change_in_message_c63(pcapfile,ricname,newPE)

def verify_realtime_update_type_in_capture(pcapfile, domain):
    """ Verify the realtime updates for MP domain have type "Quote", "Trade".
        Verify the realtime updates for MBP domain have type "unspecified".
        Argument : pcapfile : MTE output pcap file fullpath
                   domain : in format like MARKET_PRICE, MARKET_BY_PRICE, MARKET_BY_ORDER
        return : Nil
    """  
    
    verify_updated_message_exist_in_capture(pcapfile, domain)     
               
    filterstring = ''
    filterDomain = 'TRWF_TRDM_DMT_' + domain
    outputfileprefix = 'updates_pcap'
    if filterDomain == 'TRWF_TRDM_DMT_MARKET_PRICE':
        filterstring = 'AND(All_msgBase_msgKey_domainType = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_UPDATE&quot;, AND (Update_constitNum = &quot;1&quot;, AND(Update_updateTypeNum != &quot;TRWF_TRDM_UPT_QUOTE&quot;, Update_updateTypeNum != &quot;TRWF_TRDM_UPT_TRADE&quot;))))'%(filterDomain)
    if filterDomain == 'TRWF_TRDM_DMT_MARKET_BY_ORDER' or filterDomain == 'TRWF_TRDM_DMT_MARKET_BY_PRICE':
        filterstring = 'AND(All_msgBase_msgKey_domainType = &quot;%s&quot;, AND (Update_constitNum = &quot;1&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_UPDATE&quot;, Update_updateTypeNum != &quot;TRWF_TRDM_UPT_UNSPECIFIED&quot;)))'%(filterDomain)
    if len(filterstring) == 0:
        raise AssertionError('*ERROR* Need MARKET_PRICE, MARKET_BY_ORDER or MARKET_BY_PRICE for domain parameter ')  
              
    try:               
        outputxmlfile = get_xml_from_pcap(pcapfile, filterstring, outputfileprefix) 
    except AssertionError:
        return 
      
    if (os.path.exists(outputxmlfile[0]) == True):                   
        for exist_file in outputxmlfile:
            os.remove(exist_file)
    
        os.remove(os.path.dirname(outputxmlfile[0]) + "/" + outputfileprefix + "xmlfromDAS.log")  
        if filterDomain == 'TRWF_TRDM_DMT_MARKET_PRICE':
            raise AssertionError('*ERROR* realtime updates for domain %s have type other than "Quote", "Trade".' %domain)
        if filterDomain == 'TRWF_TRDM_DMT_MARKET_BY_ORDER' or filterDomain == 'TRWF_TRDM_DMT_MARKET_BY_PRICE':  
            raise AssertionError('*ERROR* realtime updates for domain %s have type other than "unspecified".' %domain)

def verify_setID_in_message(pcapfile, ric, expectedSetID, msgType):
    """ Verify if the SetID in message equals with expected value 

        Argument : pcapfile - the full name of pacpfile, it should be local path e.g. C:\\temp\\capture.pcap
                   ric - the specified ric name if you want to check
                   expectedSetID - the number for SetID, it should be 10 or 12 or 14 or 30
                   msgType - should be 'Resopnse' or 'Update'

        Return : Nil
        
        Examples :
        verify setID in message | capture.pcap | C:\\Program Files\\Reuters Test Tools\\DAS | AAAX.O | 30 |
        
    """        
    #Check if pcap file exist
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)
    #Build the filterstring
    filterstring = _build_DAS_filter_string('*', ric);
    
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,'setIDVerificationVspcap',20)
    
    messageNode = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfilelist[0], 'Message')
    
    for msgkey in messageNode[0].getiterator('MsgBase'):
        element = msgkey.find('SetID')
        if (element != None):
            if element.get('value') != expectedSetID:
                raise AssertionError('*ERROR* The set id in message is %s does not equal the expected %s' % (element.text, expectedSetID))
            
    for delFile in outputxmlfilelist:
        os.remove(delFile)

def verify_solicited_response_in_capture(pcapfile, ric, domain, constituent_list):
    """ verify the pcap file contains solicited response messages for all possible constituents defined in fidfilter.txt
        Argument : pcapfile : MTE output capture pcap file fullpath
                   ric : published RIC
                   domain : domain for published RIC in format like MARKET_PRICE, MARKET_BY_ORDER, MARKET_BY_PRICE etc.
                   constituent_list: list contains all possible constituents
         return : Nil      
    """ 
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* Pcap file is not found at %s' %pcapfile) 
    
    filterDomain = 'TRWF_TRDM_DMT_'+ domain
    outputfileprefix = 'req_response_'
   
    for constit in constituent_list:
        filterstring = 'AND(All_msgBase_msgKey_domainType = &quot;%s&quot;, AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, AND(Response_responseTypeNum= &quot;TRWF_TRDM_RPT_SOLICITED_RESP&quot;, Response_constitNum = &quot;%s&quot;))))'%(filterDomain, ric, constit)
        outputxmlfile = get_xml_from_pcap(pcapfile, filterstring, outputfileprefix)
        
        for exist_file in outputxmlfile:
            os.remove(exist_file)
        
        os.remove(os.path.dirname(outputxmlfile[0]) + "/" + outputfileprefix + "xmlfromDAS.log")

def verify_unsolicited_response_in_capture (pcapfile, ric, domain, constituent_list):
    """ verify if unsolicited response for RIC has found in MTE output pcap message
        Argument : pcapfile : MTE output capture pcap file fullpath
                   ric : published RIC
                   domain : domain for published RIC in format like MARKET_PRICE, MARKET_BY_ORDER, MARKET_BY_PRICE etc.
                   constituent_list: list contains all possible constituents 
        return : Nil
    """           

    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)                       
    
    filterDomain = 'TRWF_TRDM_DMT_'+ domain
    outputfileprefix = 'unsolpcap'
    
    for constit in constituent_list:
        filterstring = 'AND(All_msgBase_msgKey_domainType = &quot;%s&quot;, AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, AND(Response_responseTypeNum= &quot;TRWF_TRDM_RPT_UNSOLICITED_RESP&quot;, Response_constitNum = &quot;%s&quot;))))'%(filterDomain, ric, constit)
        outputxmlfile = get_xml_from_pcap(pcapfile, filterstring, outputfileprefix)                
            
        for exist_file in outputxmlfile:
            os.remove(exist_file)
    
        os.remove(os.path.dirname(outputxmlfile[0]) + "/" + outputfileprefix + "xmlfromDAS.log")

def verify_unsolicited_response_NOT_in_capture (pcapfile, ric, domain, constituent_list):
    """ verify if unsolicited response for RIC has found in MTE output pcap message
        Argument : pcapfile : MTE output capture pcap file fullpath
                   ric : published RIC
                   domain : domain for published RIC in format like MARKET_PRICE, MARKET_BY_ORDER, MARKET_BY_PRICE etc.
                   constituent_list: list contains all possible constituents 
        return : Nil
    """           

    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)                       
    
    filterDomain = 'TRWF_TRDM_DMT_'+ domain
    outputfileprefix = 'unsolpcap'
    
    for constit in constituent_list:
        try:
            filterstring = 'AND(All_msgBase_msgKey_domainType = &quot;%s&quot;, AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, AND(Response_responseTypeNum= &quot;TRWF_TRDM_RPT_UNSOLICITED_RESP&quot;, Response_constitNum = &quot;%s&quot;))))'%(filterDomain, ric, constit)
            outputxmlfile = get_xml_from_pcap(pcapfile, filterstring, outputfileprefix)                
        except AssertionError:
            return
        
        for exist_file in outputxmlfile:
            os.remove(exist_file)
    
        os.remove(os.path.dirname(outputxmlfile[0]) + "/" + outputfileprefix + "xmlfromDAS.log") 

def verify_unsolicited_response_sequence_numbers_in_capture(pcapfile, ric, domain, mte_state):
    """ verify if unsolicited response message sequence numbers for RIC are in increasing order in MTE output pcap message
        if mte_state is startup, the sequence number should start from 0, then 4, 5, ... n, n+1...
        if mte_state is failover, the sequence number could start from 1, then 4, 5, ... n, n+1...
        if mte_state is rollover, the sequence number could start from 3, then 4, 5, ... n, n+1...
        
        Argument : pcapfile : MTE output capture pcap file fullpath
                   ric : published RIC
                   domain : domain for published RIC in format like MARKET_PRICE, MARKET_BY_ORDER, MARKET_BY_PRICE etc.
                   mte_state: possible value startup, rollover, failover.
        return : last item from response message sequence number list
    """           

    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)                       
    
    filterDomain = 'TRWF_TRDM_DMT_'+ domain
    outputfileprefix = 'test_seqnum_resp_'
    filterstring = 'AND(All_msgBase_msgKey_domainType = &quot;%s&quot;, AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_responseTypeNum= &quot;TRWF_TRDM_RPT_UNSOLICITED_RESP&quot;)))'%(filterDomain, ric)
    outputxmlfile = get_xml_from_pcap(pcapfile, filterstring, outputfileprefix)                
    
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfile[0],parentName)
    seqNumList = []
    for messageNode in messages:
        seqNum = xmlutilities.xml_parse_get_field_for_messageNode(messageNode, 'ItemSeqNum')
        seqNumList.append(seqNum)
                
    if len(seqNumList)== 0:
        raise AssertionError('*ERROR* response message for %s, %s does not exist.'%(ric,domain)) 
                
    for i in xrange(len(seqNumList) - 1):
        if int(seqNumList[i]) > int(seqNumList[i+1]):
            print seqNumList
            raise AssertionError('*ERROR* response message for %s, %s are not in correct sequence order. SeqNo[%d] %s should be after SeqNo[%d] %s.'%(ric, domain, i, seqNumList[i], i+1, seqNumList[i+1])) 
            
                 
    for exist_file in outputxmlfile:
        os.remove(exist_file)
    os.remove(os.path.dirname(outputxmlfile[0]) + "/" + outputfileprefix + "xmlfromDAS.log")       
    
    if mte_state == 'startup':
        if seqNumList[0] != '0':
            raise AssertionError('*ERROR* sequence number start from %s, instead it should start from 0' %seqNumList[0])  
        if '1' in seqNumList or '2' in seqNumList or '3' in seqNumList:
            print seqNumList
            raise AssertionError('*ERROR* sequence number 1, 2, 3 should not be in the message sequence number List')
     
    if mte_state == 'failover':  
        if seqNumList[0] != '1':
            raise AssertionError('*ERROR* sequence number start from %s, instead it should start from 1' %seqNumList[0])  
        if '0' in seqNumList or '2' in seqNumList or '3' in seqNumList:
            print seqNumList
            raise AssertionError('*ERROR* sequence number 0, 2, 3 should not be in the message sequence number list')
          
    if mte_state == 'rollover':
        if seqNumList[0] != '3':
            raise AssertionError('*ERROR* sequence number start from %s, instead it should start from 3' %seqNumList[0])  
        
    return seqNumList[-1]

def verify_updated_message_exist_in_capture(pcapfile, domain):
    """ Verify updates for the domain exist in the pcap file
        Argument : pcapfile : MTE output pcap file fullpath
                   domain : in format like MARKET_PRICE, MARKET_BY_PRICE, MARKET_BY_ORDER
        return : Nil
    """  
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)                       
    
    filterDomain = 'TRWF_TRDM_DMT_' + domain
    outputfileprefix = 'updates_pcap'
    filterstring = 'AND (All_msgBase_msgKey_domainType = &quot;%s&quot;, All_msgBase_msgClass = &quot;TRWF_MSG_MC_UPDATE&quot;)'%filterDomain
    
    outputxmlfile = get_xml_from_pcap(pcapfile, filterstring, outputfileprefix)  
    
    if (os.path.exists(outputxmlfile[0]) == True):
        for exist_file in outputxmlfile:
            os.remove(exist_file)
        os.remove(os.path.dirname(outputxmlfile[0]) + "/" + outputfileprefix + "xmlfromDAS.log")   
    else:
       raise AssertionError('*ERROR* No update messages found for domain %s in %s' %(domain, pcapfile))

def verify_updated_message_sequence_numbers_in_capture(pcapfile, ric, domain, mte_state):
    """ verify if updated message sequence number for RIC are in increasing order in MTE output pcap message
        if mte_state is startup, the possible sequence number could start from 4 then 5, ... n, n+1...
        if mte_state is failover, the possible sequence number could start from 1, then 4, 5, ... n, n+1...
        if mte_state is rollover, the sequence number could start from 3, then 4, 5, ... n, n+1...
        Argument : pcapfile : MTE output capture pcap file fullpath
                   ric : published RIC
                   domain : domain for published RIC in format like MARKET_PRICE, MARKET_BY_ORDER, MARKET_BY_PRICE etc.
                   mte_state: possible value startup, rollover, failover.
        return : First item from update message sequence number list
    """       
    if (os.path.exists(pcapfile) == False):
        raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)                       
    
    filterDomain = 'TRWF_TRDM_DMT_'+ domain
    outputfileprefix = 'test_seqnum_update_'
    
    filterstring = 'AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_UPDATE&quot;, AND(All_msgBase_msgKey_name = &quot;%s&quot;, All_msgBase_msgKey_domainType = &quot;%s&quot;))'%(ric, filterDomain)
    outputxmlfile = get_xml_from_pcap(pcapfile,filterstring,outputfileprefix)
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfile[0],parentName)
    
    seqNumList = []
    for messageNode in messages:
        seqNum = xmlutilities.xml_parse_get_field_for_messageNode(messageNode, 'ItemSeqNum')
        seqNumList.append(seqNum)
   
    if len(seqNumList) == 0:
        raise AssertionError('*ERROR* updated message for %s, %s does not exist.'%(ric,domain)) 
      
    for i in xrange(len(seqNumList) - 1):
        if int(seqNumList[i]) > int(seqNumList[i + 1]):
            print seqNumList
            raise AssertionError('*ERROR* update message for %s, %s are not in correct sequence order. SeqNo[%d] %s should be after SeqNo[%d] %s.'%(ric, domain, i, seqNumList[i], i+1, seqNumList[i+1])) 
        
    for exist_file in outputxmlfile:
        os.remove(exist_file)
    os.remove(os.path.dirname(outputxmlfile[0]) + "/" + outputfileprefix + "xmlfromDAS.log")  
    
    if mte_state == 'startup':
        if seqNumList[0] <= '3':
            print seqNumList
            raise AssertionError('*ERROR* sequence number 0, 1, 2, 3 should not be in the message sequence number list')
     
    if mte_state == 'failover':  
        if seqNumList[0] != '1':
            raise AssertionError('*ERROR* sequence number start from %s, instead it should start from 1' %seqNumList[0])  
        if '0' in seqNumList or '2' in seqNumList or '3' in seqNumList:
            print seqNumList
            raise AssertionError('*ERROR* sequence number 0, 2, 3 should not be in the message sequence number list')
          
    if mte_state == 'rollover':
        if seqNumList[0] != '3':
            raise AssertionError('*ERROR* sequence number start from %s, instead it should start from 3' %seqNumList[0])            
        
    return seqNumList[0]

def _and_DAS_filter_string(filterString1, filterStirng2):
    """  Combine two filterStrings with AND keyword
    
        Argument : filterString1 - left filter string
                   filterStirng2 - right filter string
                   
        Return : the combined filfer string
    """
    if(filterString1 != None and filterString1 != ''):
        if (filterStirng2 != None and filterStirng2 != ''):
            return 'AND(' + filterString1 + ', ' + filterStirng2 + ')'
        else:
            return filterString1
    else:
        if (filterStirng2 != None and filterStirng2 != ''):
            return filterStirng2
        else:
            return ''
    
def _build_DAS_filter_string(msgClass = '*', ric = '*', constitNum = '*'):
    """ Build the DAS filter string by specified condition
    
        Argument : msgClass - to filter the pcap message by Response or Update, it should be 'Response' or 'Update' or '*' (by default)
                   ric - to filter the pcap by ric name, it can be a ric name (e.g. AAXRY.O) or '*' (by default)
                   constitNum - to filter the pcap by constitNum, it can be '0' or '1' or '63' or '*' (by default)
        
        Return : The filter string e.g. 'All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot'
        
        Examples :
        filterstring = _build_DAS_filter_string('Response', '*', 1)
        Build a filter string for DAS, DAS will only show the response message whose constitNum = 1
    
    """
    filterstring = ''
    if msgClass == 'Response':
        filterstring = 'All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;'
    elif msgClass == 'Update':
        filterstring = 'All_msgBase_msgClass = &quot;TRWF_MSG_MC_UPDATE&quot;'
    elif msgClass == '*':
        pass
    
    if ric != '*':
        filterstring_for_ric = 'All_msgBase_msgKey_name = &quot;%s&quot;' % ric
        filterstring = _and_DAS_filter_string(filterstring, filterstring_for_ric)
    else:
        pass
    
    if constitNum != '*':
        filterstring_for_constitNum = 'Response_constitNum = &quot;%s&quot;' % constitNum
        filterstring = _and_DAS_filter_string(filterstring, filterstring_for_constitNum)
    else:
        pass
    
    return filterstring

def _get_RICs_from_das_xml(xmlfile, ricsDict, includeSystemRics):
    """Get RICs from all messages in the xml file and add to ricsDict
        pcapFile: is the pcap fullpath at local control PC  
        ricsDict: dictionary of RIC names to be updated
        includeSystemRics: should system RICs be included in the list

        return : Nil (updates ricDict)     
    """        
    
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(xmlfile,parentName)
    
    for message in messages:
        ric = xmlutilities.xml_parse_get_field_from_MsgKey(message,'Name')
        if (not includeSystemRics):
            if (ric.startswith('.[SPS') or ric.startswith('.[----')):
                continue
        ricsDict[ric] = 1 # value is not important, just need RIC name as key

def _verify_DROP_message_in_specific_constit_message(pcapfile,ricname,constnum):
    """ internal function used to verify DROP message (C0) for RIC in MTE output pcap message
        pcapFile : is the pcap fullpath at local control PC  
        ricname : target ric name 
        constnum:  the constitNum in itemstatus message   
        return : Nil
        
        Verify:
        1. Drop message: msg class: Item Status, ContainerType should be NoData, streamState should be 'TRWF_MSG_SST_CLOSED'
    """         
    
    outputfileprefix = 'peChgCheckC'+str(constnum)
    filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_ITEM_STATUS&quot;, AND(ItemStatus_itemSeqNum != &quot;0&quot;, ItemStatus_constitNum = &quot;%s&quot;)))'%(ricname,constnum)
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,outputfileprefix)
    
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
    
    if (len(messages) == 1):
        containterType = xmlutilities.xml_parse_get_HeaderTag_Value_for_messageNode (messages[0],'MsgBase','ContainerType')
        if (containterType != 'NoData'):
            raise AssertionError('*ERROR* C%s message : Drop message for RIC (%s) not found'%(constnum,ricname))    
        streamState = xmlutilities.xml_parse_get_HeaderTag_Value_for_messageNode (messages[0],'ItemState','StreamState')
        if (streamState != '4'):
            raise AssertionError('*ERROR* C%s message : Drop message for RIC (%s) not found'%(constnum,ricname))                    
    else:
        raise AssertionError('*ERROR* No. of C%s message received not equal to 1 for RIC %s during RIC drop, received (%d) message(s)'%(constnum,ricname,len(messages)))        
    
    for delFile in outputxmlfilelist:
        os.remove(delFile)
    
    os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")

def _verify_fid_in_fidfilter_by_contextId_against_das_xml(xmlfile,fidfilter,contextId,constit):
    """ verify MTE output (in XML format) FIDs found in FIDFilter.txt given context ID and constituent and constit
         pcapfile : MTE output capture pcap file fullpath
         context Id : context Id that want to check 
         constit : constituent number that want to check
         msgType : 'Response' = Checking Response message, 'Update' = Checking Update message
        return : Nil      
    """
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(xmlfile,parentName)
    
    for message in messages:
        verify_fid_in_fidfilter_by_contextId_against_message(message,fidfilter,contextId,constit)           

def _verify_fid_in_range_against_das_xml(xmlfile,fid_range):
    """ verify MTE output FIDs is within specific range from DAS converted xml file
         fid_range : list with content [min_fid_id,max_fid_id]       
        return : Nil      
    """        
    
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(xmlfile,parentName)
    
    for message in messages:
        verify_fid_in_range_against_message(message,fid_range)

def _verify_fid_in_fidfilter_by_contextId_and_constit_against_pcap_msgType(pcapfile,fidfilter,contextId,constit,msgType='Response'):
    """ verify MTE output FIDs is align with FIDFilter.txt given context ID and constituent
         pcapfile : MTE output capture pcap file fullpath
         context Id : context Id that want to check 
         constit : constituent number that want to check
         msgType : 'Response' = Checking Response message, 'Update' = Checking Update message
        return : Nil      
    """            
                             
    filterstring = 'AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_constitNum = &quot;' + constit + '&quot;)'
    if (msgType == 'Update'):        
        filterstring = 'AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_UPDATE&quot;, Update_constitNum = &quot;' + constit + '&quot;)'
               
    outputxmlfile = get_xml_from_pcap(pcapfile, filterstring, 'pcapVsfidfilter')
    
    _verify_fid_in_fidfilter_by_contextId_against_das_xml(outputxmlfile[0],fidfilter,contextId,constit)  
    os.remove(outputxmlfile)

def _verify_fid_in_range_by_constit_against_pcap_msgType(pcapfile,fid_range,constit,msgType='Response'):
    """ verify MTE output FIDs is within specific range and specific constituent
         pcapfile : MTE output capture pcap file fullpath
         fid_range : list with content [min_fid_id,max_fid_id]
         constit : constituent number that want to check
         msgType : 'Response' = Checking Response message, 'Update' = Checking Update message
        return : Nil      
    """            
    
    filterstring = 'AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_constitNum = &quot;' + constit + '&quot;)'
    if (msgType == 'Update'):        
        filterstring = 'AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_UPDATE&quot;, Update_constitNum = &quot;' + constit + '&quot;)'
    
    outputxmlfile = get_xml_from_pcap(pcapfile,filterstring,'pcapVsfidrange')
    
    _verify_fid_in_range_against_das_xml(outputxmlfile[0],fid_range)
    os.remove(outputxmlfile)

def _verify_FID_value_in_dict(fidsAndValues,FID,newFIDValue):
    """ compare the value found in pcap message for specific FID with the requirement
        fidsAndValues   : dictionary of FIDs and corresponding values (key = FID no., content = FID value) 
        FID             : FID no. 
        newFIDValue     : Expected value for the given FID no.
        return : Nil         
    """
    refValue = newFIDValue
    if (newFIDValue.isdigit() == False):
        refValue = ""
        for character in newFIDValue:
            refValue = refValue + (character.encode("hex")).upper()
        print '*INFO* FID value is string. Convert FID value from (%s) to Hex (%s)'%(newFIDValue,refValue)
                
    if (fidsAndValues.has_key(FID)):                        
        if (fidsAndValues[FID] != refValue):
            raise AssertionError('*ERROR* FID value in message (%s) not equal to (%s)'%(fidsAndValues[FID],refValue))
    else:
        raise AssertionError('*ERROR* Missing FID (%s) in message '%FID)

def _verify_FIDfilter_FIDs_are_in_message_from_das_xml(xmlfile,fidfilter, ricsDict):
    """ compare value found in FIDFilter.txt against xml file which converted from MTE output pcap
        messages : iterator for all Message tag found in xml
        fidfilter : dictionary of fidfilter (captured from fidfilterfile::get_contextId_fids_constit_from_fidfiltertxt)
        ricsDist : updated with the RIC/contextID information during verification of reponse message with constit=1
        return : Nil
        Assertion : Nil             
    """            
               
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(xmlfile,parentName)
    
    for message in messages:
        _verify_FIDfilter_FIDs_in_single_message(message,fidfilter, ricsDict)

def _verify_FIDfilter_FIDs_in_single_message(messageNode,fidfilter, ricsDict):
    """ compare value found in FIDFilter.txt against MTE Response Message
        messageNode : iterator pointing to one message node
        fidfilter : dictionary of fidfilter (captured from fidfilterfile::get_contextId_fids_constit_from_fidfiltertxt)
        ricsDist : updated with the RIC/contextID information during verification of reponse message with constit=1
        return : NIL
        Error : (1) No FIDs found in response message (Empty payload case)
                (2) FIDs found in FIDFilter not found int MTE response
                (3) Context ID found in MTE response not found in FIDFilter.txt  
                
        [Pending : Response Message without FID 5357 could be SPS > Skip checking ?]                  
    """
    
    fidsAndValues = xmlutilities.xml_parse_get_fidsAndValues_for_messageNode(messageNode)
    constit = xmlutilities.xml_parse_get_field_for_messageNode(messageNode,'ConstitNum')
    ricname = xmlutilities.xml_parse_get_field_from_MsgKey(messageNode,'Name')
    contextId = "-1"
           
    if (len(fidsAndValues) == 0):           
        raise AssertionError('*ERROR* Empty payload found in response message for Ric=%s' %ricname) 
            
    if (constit == '1'):
        #Get Context ID from FID 5357
        if (fidsAndValues.has_key(FID_CONTEXTID) == True):
            contextId = fidsAndValues[FID_CONTEXTID]
            if (fidfilter.has_key(contextId) == True):
                for fid in fidfilter[contextId][constit]:
                    if (fidsAndValues.has_key(fid) == False):                                        
                        raise AssertionError('*ERROR* Missing FID=%s in MTE response output for context ID = %s, Ric = %s' %(fid,contextId,ricname))
                ricsDict[ricname] = contextId
            else:
                raise AssertionError('*ERROR* Context ID (FID %s) = %s found in MTE response output is missing from FIDFilter.txt' %(FID_CONTEXTID,contextId))
                        
    elif (constit == '0'):
        if (ricsDict.has_key(ricname)):
            contextId = ricsDict[ricname]
            if (fidfilter.has_key(contextId) == True):
                for fid in fidfilter[contextId][constit]:
                    if (fidsAndValues.has_key(fid) == False):                                        
                        raise AssertionError('*ERROR* Missing FID=%s in MTE response output for context ID = %s, Ric = %s' %(fid,contextId,ricname))
            else:
                raise AssertionError('*ERROR* Context ID (FID %s) = %s found in MTE response output is missing from FIDFilter.txt' %(FID_CONTEXTID,contextId))

def _verify_PE_change_in_message_c0(pcapfile,ricname,newPE):
    """ internal function used to verify PE Change response (C0) for RIC in MTE output pcap message
        pcapFile : is the pcap fullpath at local control PC  
        ricname : target ric name    
        newPE : new value of PE
        return : Nil
        
        Verify:
        1. C0 Response, new PE in header
    """         
    
    outputfileprefix = 'peChgCheckC0'
    filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, AND(Response_itemSeqNum != &quot;0&quot;, Response_constitNum = &quot;0&quot;)))'%(ricname)
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,outputfileprefix)
    
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
    
    if (len(messages) == 1):
        #1st C0 message : C0 Response, new PE in header
        headerPE = xmlutilities.xml_parse_get_HeaderTag_Value_for_messageNode(messages[0],'PermissionInfo','PE')
        if (headerPE != newPE):
            raise AssertionError('*ERROR* C0 message : New PE in header (%s) not equal to (%s)'%(headerPE,newPE))                   
    else:
        raise AssertionError('*ERROR* No. of C0 message received not equal to 1 for RIC %s during PE change, received (%d) message(s)'%(ricname,len(messages)))        
    
    for delFile in outputxmlfilelist:
        os.remove(delFile)
    
    os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")

def _verify_PE_change_in_message_c1(pcapfile,ricname,oldPEs,newPE):
    """ internal function used to verify PE Change response (C1) for RIC in MTE output pcap message
        pcapFile : is the pcap fullpath at local control PC  
        ricname : target ric name
        oldPEs : a list of possible original PEs (We use a list of candidates due to the fact we use hardcode way for RIC Mangling test cases)  
        newPE : new value of PE
        return : Nil
        
        Verify:
        1. C1 Response, OLD PE in header, New PE in payload, no other FIDs included
        2. C1 Response, new PE in header, all payload FIDs included
    """ 
            
    outputfileprefix = 'peChgCheckC1'
    filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, AND(Response_itemSeqNum != &quot;0&quot;, Response_constitNum = &quot;1&quot;)))'%(ricname)
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,outputfileprefix)
    
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
    
    if (len(messages) == 2):
        #1st C1 message : C1 Response, OLD PE in header, New PE in payload, no other FIDs included
        fidsAndValues = xmlutilities.xml_parse_get_fidsAndValues_for_messageNode(messages[0])
        if (fidsAndValues.has_key('1')):
            if (fidsAndValues['1'] != newPE):
                raise AssertionError('*ERROR* 1st C1 message : New PE in payload (%s) not equal to (%s)'%(fidsAndValues['1'],newPE))
        else:
            raise AssertionError('*ERROR* 1st C1 message : Missing FID 1 (PROD_PERM) in payload')
        
        headerPE = xmlutilities.xml_parse_get_HeaderTag_Value_for_messageNode(messages[0],'PermissionInfo','PE')
        isPass = False
        for oldPE in oldPEs:
            if (headerPE == oldPE):
                isPass = True
        if not (isPass):
            raise AssertionError('*ERROR* 1st C1 message : Old PE in header (%s) no match with any given PEs (%s)'%(headerPE,oldPEs))            
        
        #2nd C1 message : C1 Response, new PE in header, all payload FIDs included
        dummyricDict = {}
        fidfilter = fidfilterfile.get_contextId_fids_constit_from_fidfiltertxt()   
        _verify_FIDfilter_FIDs_in_single_message(messages[1],fidfilter, dummyricDict)    
        
        headerPE = xmlutilities.xml_parse_get_HeaderTag_Value_for_messageNode(messages[1],'PermissionInfo','PE')
        if (headerPE != newPE):
            raise AssertionError('*ERROR* 2nd C1 message : New PE in header (%s) not equal to (%s)'%(headerPE,newPE))
    else:
        raise AssertionError('*ERROR* No. of C1 message received not equal to 2 for RIC %s during PE change, received (%d) message(s)'%(ricname,len(messages)))
    
    for delFile in outputxmlfilelist:
        os.remove(delFile)
    
    os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")                

def _verify_PE_change_in_message_c63(pcapfile,ricname,newPE):
    """ internal function used to verify PE Change response (C63) for RIC in MTE output pcap message
        pcapFile : is the pcap fullpath at local control PC  
        ricname : target ric name
        newPE : new value of PE
        return : Nil
        
        Verify:
        1. C63 Response, new PE in header, all payload FIDs included.
    """         
    hasC63 = False
    fidfilter = fidfilterfile.get_contextId_fids_constit_from_fidfiltertxt()
    contextIDs = fidfilter.keys()
    for contextID in contextIDs:
        constitIDs = fidfilter[contextID].keys()
        if ('63' in constitIDs):
            hasC63 = True
            break
    
    if (hasC63 == False):
        print '*INFO* NO C63 found in FIDFilter.txt, skip C63 requirement checking'
        return
    
    outputfileprefix = 'peChgCheckC63'
    filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_constitNum = &quot;63&quot;))'%(ricname)
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,outputfileprefix)
    
    parentName  = 'Message'
    messages = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
    
    if (len(messages) == 0):
        print '*INFO* NO C63 found'
    elif (len(messages) == 1):
        #1st C63 Response, new PE in header, all payload FIDs included.
        dummyricDict = {}
        _verify_FIDfilter_FIDs_in_single_message(messages[0],fidfilter, dummyricDict)                
        
        headerPE = xmlutilities.xml_parse_get_HeaderTag_Value_for_messageNode(messages[0],'PermissionInfo','PE')
        if (headerPE != newPE):
            raise AssertionError('*ERROR* C63 message : New PE in header (%s) not equal to (%s)'%(headerPE,newPE))                
    else:
        raise AssertionError('*ERROR* No. of C63 message received not equal to 1 for RIC %s during PE change, received (%d) message(s)'%(ricname,len(messages)))        
              
    for delFile in outputxmlfilelist:
        os.remove(delFile)
    
    os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")

def _verify_response_message_num_with_constnum(pcapfile,ricname,constnum):
    """ internal function used to verify response message with constnum for RIC in MTE output pcap message 

        Argument : pcapFile : is the pcap fullpath at local control PC  
        ricname : target ric name    
        constnum: Response_constitNum       
        return : Nil
                   
        Return : N/A   
    """  
    if (constnum == 63):
        hasC = False
        fidfilter = fidfilterfile.get_contextId_fids_constit_from_fidfiltertxt()
        contextIDs = fidfilter.keys()
        for contextID in contextIDs:
            constitIDs = fidfilter[contextID].keys()
            if (constnum in constitIDs):
                hasC = True
                break
        
        if (hasC == False):
            print '*INFO* NO C63 found in FIDFilter.txt, skip C63 requirement checking'
            return   
    
    outputfileprefix = 'rebuildCheckC'
    filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_constitNum = &quot;%s&quot;))'%(ricname,constnum)
    
    parentName  = 'Message'        
    outputxmlfilelist = get_xml_from_pcap(pcapfile,filterstring,outputfileprefix)
    messages = xmlutilities.xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
    if (len(messages) == 0):
        raise AssertionError('*ERROR* no C%s message found'%constnum) 
    if (len(messages) > 1):
        raise AssertionError('*ERROR* more than 1 C%s message found, the num is %s'%(constnum,len(messages))) 
            
    for delFile in outputxmlfilelist:
        os.remove(delFile)
    
    os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")

#############################################################################
# Keywords that use remote MTE output message capture file
#############################################################################
                 
def start_capture_packets(outputfile,interface,ip,port,protocol='UDP'):
    """start capture packets by using tcpdump

    Argument 
    outputfile : outputfilename fullpath
    interface : the nic interface name e.g. eth1
    ip : 'source' ip for data capture
    port : port for data capture
    protocol : protocol for data capture

    Returns NIL.

    Examples:
    | start capture packets | mte.output.pcap | eth0 | 232.2.1.0 | 7777 |
     """

    #Pre Checking
    checkList = _check_process(['tcpdump'])
    if (len(checkList[0]) > 0):
        print '*INFO* tcpdump process already started at the TD box. Kill the exising tcpdump process'
        stop_capture_packets() 
     
    #Create output folder
    cmd = 'mkdir -p' + os.path.dirname(outputfile)
    stdout, stderr, rc = _exec_command(cmd)
    
    #Remove existing pcap
    cmd = 'rm -rf ' + outputfile
    stdout, stderr, rc = _exec_command(cmd)
  
    cmd = ''
    if (len(ip) > 0 and len(port) > 0):
        cmd = 'tcpdump -i ' + interface + ' -s0 \'(host ' + ip +  ' and port ' + port  + ')\' -w ' + outputfile
    else:     
        cmd = 'tcpdump -i' + interface + '-s0 ' + protocol +  '-w ' + outputfile
    
    print '*INFO* ' + cmd    
    _start_command(cmd)
    
    #Post Checking
    time.sleep(5) #wait a while before checking or sometimes it would return false alarm
    checkList = _check_process(['tcpdump'])
    if (len(checkList[1]) > 0):
        raise AssertionError('*ERROR* Fail to start cmd=%s ' %cmd)
                
def stop_capture_packets():
    """stop capture packets by using tcpdump
    Argument NIL
    
    Returns NIL.

    Examples:
    | stop capture packets |
     """
                    
    cmd = 'pkill tcpdump'
    stdout, stderr, rc = _exec_command(cmd)            
    
    if rc==1:
        print '*INFO* tcpdump process NOT found on target box'
    elif rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    else:   
        print '*INFO* tcpdump process stop successfully'

def wait_for_capture_to_complete(instanceName,waittime=5,timeout=30):
    """wait for capture finish by checking the stat block information

    Argument 
    instanceName : either instance of MTE of FH e.g. MFDS1M or MFDS1F
    statBlockList : [list] of stat block name that want to monitor during capture
    waittime : how long we wait for each cycle during checking (second)
    timeout : how long we monitor before we timeout (second)

    Returns NIL.

    Examples:
    | wait for capture to complete | HKF1A | 2 | 300 |
     """
    
    statBlockList = statblock.get_statBlockList_for_mte_input()
    
    #initialize the msgCount for each stat block found in statBlock list 
    msgCountPrev = {}
    msgCountDiff = {}
    for statBlock in statBlockList:
        msgCountPrev[statBlock] =  statblock.get_bytes_received_from_stat_block(instanceName,statBlock)
        msgCountDiff[statBlock] = 0

    # convert  unicode to int (it is unicode if it came from the Robot test)
    timeout = int(timeout)
    waittime = int(waittime)
    maxtime = time.time() + float(timeout) 
    
    while time.time() <= maxtime:
                    
        time.sleep(waittime)  
        
        #Check if msg count difference
        for statBlock in statBlockList:
            msgCountCurr = statblock.get_bytes_received_from_stat_block(instanceName,statBlock)
            msgCountDiff[statBlock] = msgCountCurr - msgCountPrev[statBlock]
            
            if (msgCountDiff[statBlock] < 0):
                raise AssertionError('*ERROR* stat block %s - Current bytes received %d < previous bytes received %d' %(statBlock,msgCountCurr,msgCountPrev[statBlock]))
        
            msgCountPrev[statBlock] = msgCountCurr
            
        #Check time to stop catpure
        isStop = True
        for statBlock in statBlockList:
            if (msgCountDiff[statBlock] != 0):
                isStop = False
        
        if (isStop):
            return                    
    
    #Timeout                    
    raise AssertionError('*ERROR* Timeout %ds : Playback has not ended yet for some channel (suggest to adjust timeout)' %(timeout))
