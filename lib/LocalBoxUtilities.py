'''
Created on Aug 27, 2015

@author: jason.lo

'''
from __future__ import with_statement
from utils.version import get_version

import os
import re
import glob
import fnmatch
import string
import os.path
from datetime import datetime, timedelta
import xml
import xml.etree.ElementTree as ET
from xml.dom import minidom
from subprocess import Popen, PIPE
from sets import Set
from LinuxToolUtilities import LinuxToolUtilities
from LinuxFSUtilities import LinuxFSUtilities
from FMUtilities import _FMUtil
from utils.local import _run_local_command
from utils._ToolUtil import _ToolUtil
from utils._FSUtil import _FSUtil

FID_CONTEXTID = '5357'

class LocalBoxUtilities(_ToolUtil):
        
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()   
    
    def _xml_parse_get_all_elements_by_name (self,xmlfile,tagName):
        """ get iterator for all elements with tag=tagName from xml file
            xmlfile : xml fullpath
            tagName : tag name that want to search
            return : iterator of the elements it found in xml file
            Assertion : if no element found for tagName
            
        """                
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        retIter = root.getiterator(tagName)
        
        #Check if not found
        if (len(retIter) == 0):
            raise AssertionError('*ERROR* tagName=%s not found in %s'%(tagName,xmlfile))
            
        return  retIter
    
    def _xml_parse_get_HeaderTag_Value_for_messageNode (self,messageNode,headerTag,fieldName):
        """ get specific header tag info from a message node
            messageNode : iterator pointing to one message node
            headerTag: the Tag is searched for in the message node.
            fieldName: the field is within the headerTag, the value for this field will be returned
            return : the value of the specified field within the headerTag
            Assertion : <headerTag> not found
            Example:
            <Message>
              <MsgBase>
                <ContainerType value="NoData"/>
              </MsgBase>
            </Message>    
            |_xml_parse_get_HeaderTag_Value_for_messageNode | Message[0] | MsgBase | ContainerType |
            
        """
                            
        for fieldEntry in messageNode.getiterator(headerTag):
            foundfield = fieldEntry.find(fieldName)
            if (foundfield != None):                   
                return foundfield.attrib['value']

        raise AssertionError('*ERROR* Missing %s'%(headerTag))
        
    def _xml_parse_get_fidsAndValues_for_messageNode (self,messageNode):
        """ get FIDs and corresponding value from a message node
            messageNode : iterator pointing to one message node
            return : dictionary of FIDs and corresponding value (key=FID no.)
            Assertion : NIL
        """
                            
        fidsAndValues = {}
        for fieldEntry in messageNode.getiterator('FieldEntry'):
            fieldId = fieldEntry.find('FieldID')
            fieldValue = fieldEntry.find('Data')
            
            if (fieldId != None and fieldValue != None):                   
                fidsAndValues[fieldId.attrib['value']] = fieldValue.attrib['value']
            elif (fieldId != None and fieldValue == None):
                fidsAndValues[fieldId.attrib['value']] = 'NoData'
            
        return fidsAndValues
    
    def _xml_parse_get_field_for_messageNode (self,messageNode,fieldName):
        """ get field value from a message node
            messageNode : iterator pointing to one message node
            fieldName : tag name we want to get the value
            return : constituent no.
            Assertion : if ConstitNun tag not found
        """
                
        element = messageNode.find(fieldName)
        if (element != None):
            return element.attrib['value']
        else:
            raise AssertionError('*ERROR* %s field is missing from response message'%(fieldName))     
    
    def _xml_parse_get_field_from_MsgKey(self,messageNode, fieldName):
        """ get field value from a message node : <MsgKey> 
            messageNode : iterator pointing to one message node
            fieldName
            return : ric name
            Assertion : if MsgKey/Name tag not found
        """
                
        for msgkey in messageNode.getiterator('MsgKey'):
            element = msgkey.find(fieldName)
            if (element != None):
                return element.attrib['value']
            
        raise AssertionError('*ERROR* MsgKey:%s is missing from message'%(fieldName))    
    
    def verify_csv_files_match(self, file1, file2, ignorefids):
        """Verify two .csv files match.

        Argument ignorefids is a comma separated list of fields to ignore.
        If it is used, the first line of file must contain the field names.
        Those columns will be excluded during the comparision.
        
        Does not return a value; raises an error if any differences are found.

        Examples:
        | Verify csv Files Match  | file1  | file2  | ignorefids=CURR_SEQ_NUM,LAST_UPDATED  |
        | Verify csv Files Match  | file1  | file2  | CURR_SEQ_NUM,LAST_UPDATED             |
        """
        fileobj1= open(file1,'r')
        lines1 = fileobj1.readlines()
        fileobj1.close()
        fileobj2= open(file2,'r')
        lines2 = fileobj2.readlines()
        fileobj2.close()
        ignorelist = ignorefids.split(',')
        ignorepositions = []
        if lines1[0].find(ignorelist[0])!=-1:
            # rstrip to remove newline
            itemslist = lines1[0].rstrip().split(',')
            for item in itemslist:
                if item in ignorelist:
                    ignorepositions.append(itemslist.index(item))
        else:
            ignorepositions = ignorelist
        print '*INFO* ignoring columns %s' %ignorepositions
        
        count = 0
        NotMatchlines =[]
        if len(lines1) != len(lines2):
            raise AssertionError('*ERROR* line count differs %s:%s' %(len(lines1),len(lines2)))
        
        while count < len(lines1) and count < len(lines2):
            items1 = lines1[count].split(',')
            items2 = lines2[count].split(',')
            if len(items1) != len(items2):
                NotMatchlines.append([lines1[count],lines2[count]])
            else:
                for idx in range(len(items1)):
                    if idx not in ignorepositions and items1[idx] != items2[idx]:
                        NotMatchlines.append([lines1[count],lines2[count]])
                        break
            count = count+1
        
        if len(NotMatchlines)!=0:
            raise AssertionError('*ERROR* %s lines are different' %len(NotMatchlines))
        else:
            print '*INFO* the files are identical'         

    def verify_fid_in_fidfilter_by_contextId_against_message(self,messageNode,fidfilter,contextId,constit):
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
                
        fidsAndValues = self._xml_parse_get_fidsAndValues_for_messageNode(messageNode)
        ricname = self._xml_parse_get_field_from_MsgKey(messageNode,'Name')        
            
        if (len(fidsAndValues) == 0):            
            raise AssertionError('*ERROR* Empty payload found in response message for Ric=%s' %ricname)
        
        for fid in fidsAndValues.keys():
            if (fidfilter[contextId][constit].has_key(fid) == False):
                raise AssertionError('*ERROR* FID %s is not found in FIDFilter.txt for Ric=%s has published' %(fid,ricname))
    
    def _verify_fid_in_fidfilter_by_contextId_against_das_xml(self,xmlfile,fidfilter,contextId,constit):
        """ verify MTE output (in XML format) FIDs found in FIDFilter.txt given context ID and constituent and constit
             pcapfile : MTE output capture pcap file fullpath
             context Id : context Id that want to check 
             constit : constituent number that want to check
             msgType : 'Response' = Checking Response message, 'Update' = Checking Update message
            return : Nil      
        """
        parentName  = 'Message'
        messages = self._xml_parse_get_all_elements_by_name(xmlfile,parentName)
        
        for message in messages:
            self.verify_fid_in_fidfilter_by_contextId_against_message(message,fidfilter,contextId,constit)           
    
    def _verify_fid_in_fidfilter_by_contextId_and_constit_against_pcap_msgType(self,pcapfile,fidfilter,contextId,constit,dasdir,msgType='Response'):
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
                   
        outputxmlfile = self._get_extractorXml_from_pcap(dasdir, pcapfile, filterstring, 'pcapVsfidfilter')
        
        self._verify_fid_in_fidfilter_by_contextId_against_das_xml(outputxmlfile[0],fidfilter,contextId,constit)  
        os.remove(outputxmlfile)
            
    def verify_fid_in_fidfilter_by_contextId_and_constit_against_pcap(self,pcapfile,contextId,constit,venuedir,dasdir):
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
        fidfilter = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt(venuedir)
        if (fidfilter.has_key(contextId) == False):
            raise AssertionError('*ERROR* required context ID %s not found in FIDFilter.txt '%contextId)
        elif ((fidfilter[contextId].has_key(constit) == False)):
            raise AssertionError('*ERROR* required constituent %s not found in FIDFilter.txt '%constit)          
                
        #For Response
        self._verify_fid_in_fidfilter_by_contextId_and_constit_against_pcap_msgType(pcapfile,fidfilter,contextId,constit,dasdir,'Response')
        
        #For Update
        self._verify_fid_in_fidfilter_by_contextId_and_constit_against_pcap_msgType(pcapfile,fidfilter,contextId,constit,dasdir,'Update')  
    
    def verify_fid_in_range_against_message(self,messageNode,fid_range):
        """ verify MTE output FIDs is within specific range from message node
             messageNode : iterator pointing to one message node
             fid_range : list with content [min_fid_id,max_fid_id]       
            return : Nil
            Assertion : 
            (1) Empty payload detected
            (2) FID is out side the specific range        
        """ 
                
        fidsAndValues = self._xml_parse_get_fidsAndValues_for_messageNode(messageNode)
        ricname = self._xml_parse_get_field_from_MsgKey(messageNode,'Name')        
            
        if (len(fidsAndValues) == 0):            
            raise AssertionError('*ERROR* Empty payload found in response message for Ric=%s' %ricname)
        
        for fid in fidsAndValues.keys():
            if (int(fid) < fid_range[0] or int(fid) > fid_range[1]):
                raise AssertionError('*ERROR* FID %s is out of range[%s,%s] for Ric=%s' %(fid,fid_range[0],fid_range[1],ricname))
        
    def _verify_fid_in_range_against_das_xml(self,xmlfile,fid_range):
        """ verify MTE output FIDs is within specific range from DAS converted xml file
             fid_range : list with content [min_fid_id,max_fid_id]       
            return : Nil      
        """        
        
        parentName  = 'Message'
        messages = self._xml_parse_get_all_elements_by_name(xmlfile,parentName)
        
        for message in messages:
            self.verify_fid_in_range_against_message(message,fid_range)
    
    def _verify_fid_in_range_by_constit_against_pcap_msgType(self,pcapfile,fid_range,constit,dasdir,msgType='Response'):
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
        
        outputxmlfile = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,'pcapVsfidrange')
        
        self._verify_fid_in_range_against_das_xml(outputxmlfile[0],fid_range)
        os.remove(outputxmlfile)
                      
    def verify_fid_in_range_by_constit_against_pcap(self,pcapfile,dasdir,constit,fid_range=[-36768,32767]):
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
        self._verify_fid_in_range_by_constit_against_pcap_msgType(pcapfile,fid_range,constit,dasdir)
        
        #Checking Update
        self._verify_fid_in_range_by_constit_against_pcap_msgType(pcapfile,fid_range,constit,dasdir,'Update')
    
    def _verify_FIDfilter_FIDs_in_single_message(self,messageNode,fidfilter, ricsDict):
        """ compare value found in FIDFilter.txt against MTE Response Message
            messageNode : iterator pointing to one message node
            fidfilter : dictionary of fidfilter (captured from LinuxToolUtilities::get_contextId_fids_constit_from_fidfiltertxt)
            ricsDist : updated with the RIC/contextID information during verification of reponse message with constit=1
            return : NIL
            Error : (1) No FIDs found in response message (Empty payload case)
                    (2) FIDs found in FIDFilter not found int MTE response
                    (3) Context ID found in MTE response not found in FIDFilter.txt  
                    
            [Pending : Response Message without FID 5357 could be SPS > Skip checking ?]                  
        """           
        
        fidsAndValues = self._xml_parse_get_fidsAndValues_for_messageNode(messageNode)
        constit = self._xml_parse_get_field_for_messageNode(messageNode,'ConstitNum')
        ricname = self._xml_parse_get_field_from_MsgKey(messageNode,'Name')
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
                        
    def _verify_FIDfilter_FIDs_are_in_message_from_das_xml(self,xmlfile,fidfilter, ricsDict):
        """ compare value found in FIDFilter.txt against xml file which converted from MTE output pcap
            messages : iterator for all Message tag found in xml
            fidfilter : dictionary of fidfilter (captured from LinuxToolUtilities::get_contextId_fids_constit_from_fidfiltertxt)
            ricsDist : updated with the RIC/contextID information during verification of reponse message with constit=1
            return : Nil
            Assertion : Nil             
        """            
                   
        parentName  = 'Message'
        messages = self._xml_parse_get_all_elements_by_name(xmlfile,parentName)
        
        for message in messages:
            self._verify_FIDfilter_FIDs_in_single_message(message,fidfilter, ricsDict)
               
    def verify_FIDfilter_FIDs_are_in_message(self,pcapfile,venuedir,dasdir):
        """ compare  value found in FIDFilter.txt against MTE output pcap
            pcapFile : is the pcap fullpath at local control PC  
            venuedir : location from remote TD box for search FIDFilter.txt
            dasdir : location of DAS tool      
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
        outputxmlfilelist_1 = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,'fidfilterVspcapC1',20)
        
        #Get the fidfilter
        fidfilter = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt(venuedir)
        
        for outputxmlfile in outputxmlfilelist_1:
            self._verify_FIDfilter_FIDs_are_in_message_from_das_xml(outputxmlfile, fidfilter, ricsDict)
                
        #[ConstitNum = 0]
        #Convert pcap file to xml
        filterstring = 'AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_constitNum = &quot;0&quot;)'
        outputxmlfilelist_0 = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,'fidfilterVspcapC0',20)
        
        #Get the fidfilter
        fidfilter = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt(venuedir)
        
        for outputxmlfile in outputxmlfilelist_0:
            self._verify_FIDfilter_FIDs_are_in_message_from_das_xml(outputxmlfile, fidfilter, ricsDict)        
        
        print '*INFO* %d Rics verified'%(len(ricsDict))
           
        for delFile in outputxmlfilelist_0:
            os.remove(delFile)
        os.remove(os.path.dirname(outputxmlfilelist_0[0]) + "/fidfilterVspcapC1xmlfromDAS.log")
            
        for delFile in outputxmlfilelist_1:
            os.remove(delFile)          
        os.remove(os.path.dirname(outputxmlfilelist_1[0]) + "/fidfilterVspcapC0xmlfromDAS.log")
    
    
    def verify_message_fids_are_in_FIDfilter(self, localPcap, venuedir, dasdir, ric, domain, contextId):
        '''
         verify that message's fids set from pcap for the ric, with domain, contextId is the subset of the fids set defined in FidFilter file for a particular constituent under the context id
        '''
        constituents = self.get_constituents_from_FidFilter(venuedir, contextId)
        for constituent in constituents:
            # create fidfilter fids set under contextId and constituent
            contextIdMap = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt(venuedir)
            constitWithFIDs = contextIdMap[contextId]
            fidsdict = constitWithFIDs[constituent]
            fidsList = fidsdict.keys()
            filterFilefidsSet = frozenset(fidsList);
            
            # create filter string for each constituent to get the message fids set
            filterDomain = 'TRWF_TRDM_DMT_'+ domain
            filterstring = 'AND(All_msgBase_msgKey_domainType = &quot;%s&quot;, AND(All_msgBase_msgKey_name = &quot;%s&quot;, Response_constitNum = &quot;%s&quot;))'%(filterDomain, ric, constituent)
            outputfile = self._get_extractorXml_from_pcap(dasdir, localPcap, filterstring, "out1")
            msgFidSet = self.get_all_fids_name_from_DASXml(outputfile[0])
           
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
            
            
            
    def get_constituents_from_FidFilter(self, venue_dir, context_id):
        """ 
            Return : constituent list which contains unique constituents defined in venue FidFilter.txt file for the context_id
        """ 
        fidfilter = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt(venue_dir)
        if (fidfilter.has_key(context_id) == False):
            raise AssertionError('*ERROR* Context ID %s does not exist in FIDFilter.txt file' %(context_id))  
        
        fidDic = fidfilter[context_id]
        if len(fidDic.keys()) == 0:
            raise AssertionError('*ERROR* No FID dictionary exists in FIDFilter.txt file for Context ID %s' %(context_id))  
        
        return fidDic.keys()
             
           
    def verify_solicited_response_in_capture(self, pcapfile, das_dir, ric, domain, constituent_list):
        """ verify the pcap file contains solicited response messages for all possible constituents defined in fidfilter.txt
            Argument : pcapfile : MTE output capture pcap file fullpath
                       das_dir : path for DAS tool
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
            outputxmlfile = self._get_extractorXml_from_pcap(das_dir, pcapfile, filterstring, outputfileprefix)
            
            for exist_file in outputxmlfile:
                os.remove(exist_file)
            
            os.remove(os.path.dirname(outputxmlfile[0]) + "/" + outputfileprefix + "xmlfromDAS.log")
    
    def verify_unsolicited_response_in_capture (self,pcapfile, das_dir, ric, domain, constituent_list):
        """ verify if unsolicited response for RIC has found in MTE output pcap message
            Argument : pcapfile : MTE output capture pcap file fullpath
                       das_dir : path for DAS tool
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
            outputxmlfile = self._get_extractorXml_from_pcap(das_dir, pcapfile, filterstring, outputfileprefix)                
                
            for exist_file in outputxmlfile:
                os.remove(exist_file)
        
            os.remove(os.path.dirname(outputxmlfile[0]) + "/" + outputfileprefix + "xmlfromDAS.log")

    def verify_unsolicited_response_NOT_in_capture (self,pcapfile, das_dir, ric, domain, constituent_list):
        """ verify if unsolicited response for RIC has found in MTE output pcap message
            Argument : pcapfile : MTE output capture pcap file fullpath
                       das_dir : path for DAS tool
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
                outputxmlfile = self._get_extractorXml_from_pcap(das_dir, pcapfile, filterstring, outputfileprefix)                
            except AssertionError:
                return
            
            for exist_file in outputxmlfile:
                os.remove(exist_file)
        
            os.remove(os.path.dirname(outputxmlfile[0]) + "/" + outputfileprefix + "xmlfromDAS.log")
                              
    def _verify_PE_change_in_message_c0(self,pcapfile,dasdir,ricname,newPE):
        """ internal function used to verify PE Change response (C0) for RIC in MTE output pcap message
            pcapFile : is the pcap fullpath at local control PC  
            dasdir : location of DAS tool  
            ricname : target ric name    
            newPE : new value of PE
            return : Nil
            
            Verify:
            1. C0 Response, new PE in header
        """         
        
        outputfileprefix = 'peChgCheckC0'
        filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, AND(Response_itemSeqNum != &quot;0&quot;, Response_constitNum = &quot;0&quot;)))'%(ricname)
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,outputfileprefix)
        
        parentName  = 'Message'
        messages = self._xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
        
        if (len(messages) == 1):
            #1st C0 message : C0 Response, new PE in header
            headerPE = self._xml_parse_get_HeaderTag_Value_for_messageNode(messages[0],'PermissionInfo','PE')
            if (headerPE != newPE):
                raise AssertionError('*ERROR* C0 message : New PE in header (%s) not equal to (%s)'%(headerPE,newPE))                   
        else:
            raise AssertionError('*ERROR* No. of C0 message received not equal to 1 for RIC %s during PE change, received (%d) message(s)'%(ricname,len(messages)))        
        
        for delFile in outputxmlfilelist:
            os.remove(delFile)
        
        os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")
    
    def _verify_PE_change_in_message_c1(self,pcapfile,venuedir,dasdir,ricname,oldPE,newPE):
        """ internal function used to verify PE Change response (C1) for RIC in MTE output pcap message
            pcapFile : is the pcap fullpath at local control PC  
            venuedir : location from remote TD box for search FIDFilter.txt
            dasdir : location of DAS tool  
            ricname : target ric name
            oldPE : original value of PE
            newPE : new value of PE
            return : Nil
            
            Verify:
            1. C1 Response, OLD PE in header, New PE in payload, no other FIDs included
            2. C1 Response, new PE in header, all payload FIDs included
        """ 
                
        outputfileprefix = 'peChgCheckC1'
        filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, AND(Response_itemSeqNum != &quot;0&quot;, Response_constitNum = &quot;1&quot;)))'%(ricname)
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,outputfileprefix)
        
        parentName  = 'Message'
        messages = self._xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
        
        if (len(messages) == 2):
            #1st C1 message : C1 Response, OLD PE in header, New PE in payload, no other FIDs included
            fidsAndValues = self._xml_parse_get_fidsAndValues_for_messageNode(messages[0])
            if (fidsAndValues.has_key('1')):
                if (fidsAndValues['1'] != newPE):
                    raise AssertionError('*ERROR* 1st C1 message : New PE in payload (%s) not equal to (%s)'%(fidsAndValues['1'],newPE))
            else:
                raise AssertionError('*ERROR* 1st C1 message : Missing FID 1 (PROD_PERM) in payload')
            
            headerPE = self._xml_parse_get_HeaderTag_Value_for_messageNode(messages[0],'PermissionInfo','PE')
            if (headerPE != oldPE):
                raise AssertionError('*ERROR* 1st C1 message : Old PE in header (%s) not equal to (%s)'%(headerPE,oldPE))
            
            #2nd C1 message : C1 Response, new PE in header, all payload FIDs included
            dummyricDict = {}
            fidfilter = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt(venuedir)   
            self._verify_FIDfilter_FIDs_in_single_message(messages[1],fidfilter, dummyricDict)    
            
            headerPE = self._xml_parse_get_HeaderTag_Value_for_messageNode(messages[1],'PermissionInfo','PE')
            if (headerPE != newPE):
                raise AssertionError('*ERROR* 2nd C1 message : New PE in header (%s) not equal to (%s)'%(headerPE,newPE))
        else:
            raise AssertionError('*ERROR* No. of C1 message received not equal to 2 for RIC %s during PE change, received (%d) message(s)'%(ricname,len(messages)))
        
        for delFile in outputxmlfilelist:
            os.remove(delFile)
        
        os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")                

    def _verify_PE_change_in_message_c63(self,pcapfile,venuedir,dasdir,ricname,newPE):
        """ internal function used to verify PE Change response (C63) for RIC in MTE output pcap message
            pcapFile : is the pcap fullpath at local control PC  
            venuedir : location from remote TD box for search FIDFilter.txt
            dasdir : location of DAS tool  
            ricname : target ric name
            newPE : new value of PE
            return : Nil
            
            Verify:
            1. C63 Response, new PE in header, all payload FIDs included.
        """         
        hasC63 = False
        fidfilter = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt(venuedir)
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
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,outputfileprefix)
        
        parentName  = 'Message'
        messages = self._xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
        
        if (len(messages) == 0):
            print '*INFO* NO C63 found'
        elif (len(messages) == 1):
            #1st C63 Response, new PE in header, all payload FIDs included.
            dummyricDict = {}
            self._verify_FIDfilter_FIDs_in_single_message(messages[0],fidfilter, dummyricDict)                
            
            headerPE = self._xml_parse_get_HeaderTag_Value_for_messageNode(messages[0],'PermissionInfo','PE')
            if (headerPE != newPE):
                raise AssertionError('*ERROR* C63 message : New PE in header (%s) not equal to (%s)'%(headerPE,newPE))                
        else:
            raise AssertionError('*ERROR* No. of C63 message received not equal to 1 for RIC %s during PE change, received (%d) message(s)'%(ricname,len(messages)))        
                  
        for delFile in outputxmlfilelist:
            os.remove(delFile)
        
        os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")
        
    def verify_PE_change_in_message(self,pcapfile,venuedir,dasdir,ricname,oldPE,newPE):
        """ verify PE Change response for RIC in MTE output pcap message
            pcapFile : is the pcap fullpath at local control PC  
            venuedir : location from remote TD box for search FIDFilter.txt
            dasdir : location of DAS tool  
            ricname : target ric name    
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
        self._verify_PE_change_in_message_c0(pcapfile,dasdir,ricname,newPE)
        
        #C1
        self._verify_PE_change_in_message_c1(pcapfile,venuedir,dasdir,ricname,oldPE,newPE)
        
        #C63
        self._verify_PE_change_in_message_c63(pcapfile,venuedir,dasdir,ricname,newPE)
  
    def verify_DROP_message_in_itemstatus_messages(self,pcapfile,venuedir,dasdir,ricname):
        """ verify DROP message for RIC in MTE output pcap message
            pcapFile : is the pcap fullpath at local control PC  
            venuedir : location from remote TD box for search FIDFilter.txt
            dasdir : location of DAS tool  
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
        self._verify_DROP_message_in_specific_constit_message(pcapfile,dasdir,ricname,0)
        
        #C1
        self._verify_DROP_message_in_specific_constit_message(pcapfile,dasdir,ricname,1)
        
        #C63
        self._verify_DROP_message_in_specific_constit_message(pcapfile,dasdir,ricname,63)
    
    def _verify_DROP_message_in_specific_constit_message(self,pcapfile,dasdir,ricname,constnum):
        """ internal function used to verify DROP message (C0) for RIC in MTE output pcap message
            pcapFile : is the pcap fullpath at local control PC  
            dasdir : location of DAS tool  
            ricname : target ric name 
            constnum:  the constitNum in itemstatus message   
            return : Nil
            
            Verify:
            1. Drop message: msg class: Item Status, ContainerType should be NoData
        """         
        
        outputfileprefix = 'peChgCheckC'+str(constnum)
        filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_ITEM_STATUS&quot;, AND(ItemStatus_itemSeqNum != &quot;0&quot;, ItemStatus_constitNum = &quot;%s&quot;)))'%(ricname,constnum)
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,outputfileprefix)
        
        parentName  = 'Message'
        messages = self._xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
        
        if (len(messages) == 1):
            containterType = self._xml_parse_get_HeaderTag_Value_for_messageNode (messages[0],'MsgBase','ContainerType')
            if (containterType != 'NoData'):
                raise AssertionError('*ERROR* C%s message : Drop message for RIC (%s) not found'%(constnum,ricname))                   
        else:
            raise AssertionError('*ERROR* No. of C%s message received not equal to 1 for RIC %s during RIC drop, received (%d) message(s)'%(constnum,ricname,len(messages)))        
        
        for delFile in outputxmlfilelist:
            os.remove(delFile)
        
        os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")
        
    def verify_ClosingRun_message_in_messages(self,pcapfile,dasdir,ricname):
        """ verify ClosingRun message for RIC in MTE output pcap message
            pcapFile : is the pcap fullpath at local control PC
            dasdir : location of DAS tool  
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
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,outputfileprefix)
        
        parentName  = 'Message'
        messages = self._xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
        
        if (len(messages) == 1):
            updateType = self._xml_parse_get_field_for_messageNode (messages[0],'UpdateTypeNum')
            if (updateType != '6'):
                raise AssertionError('*ERROR* ClosingRun message for RIC (%s) not found'%(ricname))                   
        else:
            raise AssertionError('*ERROR* No. of ClosingRun message received not equal to 1 for RIC %s during RIC ClosingRun, received (%d) message(s)'%(ricname,len(messages)))        
        
        for delFile in outputxmlfilelist:
            os.remove(delFile)
        
        os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")
        
    
    def verify_MTE_heartbeat_in_message(self,pcapfile,dasdir,intervalInSec):
        """ verify MTE heartbeat in  MTE output pcap message
            pcapFile : is the pcap fullpath at local control PC  
            dasdir : location of DAS tool  
            intervalInSec : expected interval that one heartbeat should sent out   
            return : Nil
                    
            Examples:
            | verify MTE heartbeat in message  | C:\\temp\\capture_local.pcap | C:\\Program Files\\Reuters Test Tools\\DAS | 1 |            
        """ 
        
        #Convert pcap to .txt 
        #Remark : getting MTP_ARB_FLAG_POLLING from pcap, we MUST convert it to text format (not support for xml)
        outputfileprefix = 'mteHeartbeat'
        filterstring = 'MTP_ArbFlag = &quot;MTP_ARB_FLAG_POLLING&quot;'
        outputtxtfilelist = self._get_extractorTxt_from_pcap(dasdir,pcapfile,filterstring,outputfileprefix)
        
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
  
    def _verify_FID_value_in_message(self,fidsAndValues,FID,newFIDValue):
        """ compare the value found in pcap message for specific FID with the requirement
            fidsAndValues   : dictionary of FIDs and corresponding values (key = FID no., content = FID value) 
            FID             : FID no. 
            newFIDValue     : Expected value for the given FID no.
            return : Nil         
        """
        refValue = newFIDValue
        if (newFIDValue.isnumeric() == False):
            refValue = ""
            for character in newFIDValue:
                refValue = refValue + (character.encode("hex")).upper()
            print '*INFO* FID value is string. Convert FID value from (%s) to Hex (%s)'%(newFIDValue,refValue)
                    
        if (fidsAndValues.has_key(FID)):                        
            if (fidsAndValues[FID] != refValue):
                raise AssertionError('*ERROR* FID value in message (%s) not equal to (%s)'%(fidsAndValues[FID],refValue))
        else:
            raise AssertionError('*ERROR* Missing FID (%s) in message '%FID)    
    
    def verify_correction_change_in_message(self,pcapfile,dasdir,ricname,FIDs,newFIDValues):
        """ verify correction type changes in  MTE output pcap message
            pcapFile   : is the pcap fullpath at local control PC  
            dasdir     : location of DAS tool  
            ricname    : ric name that involved in correction change
            FIDs       : list of FIDs want to verify
            newFIDValues : list of FID values to check if value change is successfully or not
            return : Nil
                    
            Examples:
            | verify correction change in message  | C:\\temp\\capture_local.pcap | C:\\Program Files\\Reuters Test Tools\\DAS |AAAAX.O|['3'] |['NewValue']            
        """   
                             
        outputfileprefix = 'correctionUpdateChk'
        filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, Update_updateTypeNum = &quot;TRWF_TRDM_UPT_CORRECTION&quot;)'%(ricname)
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,outputfileprefix)
                
        parentName  = 'Message'
        messages = self._xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
                
        if (len(messages) == 1):
            fidsAndValues = self._xml_parse_get_fidsAndValues_for_messageNode(messages[0])
            
            if (len(FIDs) != len(newFIDValues)):
                raise AssertionError('*ERROR* no. of item found in FIDs list (%d) and new FID values list (%d) is not equal'%(len(FIDs),len(newFIDValues)))
            
            for idx in range(0,len(FIDs)):                    
                self._verify_FID_value_in_message(fidsAndValues, FIDs[idx], newFIDValues[idx])
        else:
            raise AssertionError('*ERROR* No. of correction message received not equal to 1 for RIC %s received (%d) message(s)'%(ricname,len(messages)))                                
        
        for delFile in outputxmlfilelist:
            os.remove(delFile)
        
        os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")
           
    def _get_EXL_files(self,fmsDir,fileType):
        """ Get EXL file(s) for fileType:
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1687

            fileType options: ['Closing Run', 'DST', 'Feed Time', 'Holiday', 'OTFC', 'Trade Time', 'All']
            
            return : List containing full path name of EXL file(s), if found. 
                     If none found, will raise an error.
        """ 
        
        if fileType.lower() == "closing run":
            print '*INFO* Closing Run:'
            searchFileString = "*_cs_run.exl"
        elif fileType.lower() == "dst":
            print '*INFO* DST:'
            searchFileString = "*_dl_save.exl"
        elif fileType.lower() == "feed time":
            print '*INFO* Feed Time:'
            searchFileString = "*_fd_time.exl"
        elif fileType.lower() == "holiday":
            print '*INFO* Holiday:'
            searchFileString = "*_mk_holiday.exl"
        elif fileType.lower() == "otfc":
            print '*INFO* OTFC:'
            searchFileString = "*_otfc.exl"
        elif fileType.lower() == "trade time":
            print '*INFO* Trade Time:'
            searchFileString = "*_trd_time.exl"
        elif fileType.lower() == "all":
            print '*INFO* All:'
            searchFileString = "*.exl"
        else:
            raise AssertionError('*ERROR* Invalid file type provided: %s' %fileType)
        
        cmdstr = 'cmd /c dir /S /B \"' + fmsDir + '\"\\' +  searchFileString
        print '*INFO* cmdstr: %s' %cmdstr
        p = Popen(cmdstr, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
        exlFiles = p.stdout.read().strip().split(os.linesep)
        if len(exlFiles) < 1 or exlFiles[0].lower() == "file not found" or exlFiles[0] == '':
            raise AssertionError('*ERROR* Search returned no results for: %s' %cmdstr)
        return exlFiles      
    
    def get_state_EXL_file(self,ricName,domainName,service,fmsDir,fileType):
        """ Get EXL file from given RIC, domain, and service:
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1737

            fileType options: ['Closing Run', 'DST', 'Feed Time', 'Holiday', 'OTFC', 'Trade Time', 'All']
            
            return : Full path name of EXL file, if found. 
                     If multiple files or none found, will raise an error.
        """ 
        
        exlFiles = self._get_EXL_files(fmsDir, fileType)
        
        matchedExlFiles = []
        
        for exlFile in exlFiles:
            dom = xml.dom.minidom.parse(exlFile)
            
            # skip file if service does not match
            fieldNames = ['SERVICE']
            result = self._get_EXL_header_values(dom,fieldNames)
            if result['SERVICE'] != service:
                continue
            
            #find the ric and domain
            iteratorlist = dom.getElementsByTagName('exlObject') 
            for node in iteratorlist:
                foundRic = False
                foundDomain = False
                for subnode in node.childNodes:
                    if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:RIC':
                        if subnode.firstChild.data == ricName:
                            foundRic = True
                    if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:DOMAIN':
                        if subnode.firstChild.data == domainName:
                            foundDomain = True
                if foundRic == True and foundDomain == True:
                    matchedExlFiles.append(exlFile)
    
        if len(matchedExlFiles) == 0:
            raise AssertionError('*ERROR*  Failed to locate RIC/domain pair (%s, %s) in EXL.' %(ricName, domainName))
        elif len(matchedExlFiles) > 1:
            raise AssertionError('*ERROR*  Found multiple EXLs for RIC/domain pair (%s, %s): [%s]' %(ricName, domainName, ', '.join(map(str, matchedExlFiles))))
        else:
            return matchedExlFiles[0]
    
    def get_EXL_for_RIC(self, fmsDir, domain, service, ric):
        """ Find the EXL file with the specified RIC, domain, and service
            
            Argument: 
                fmsDir:  The Location of the FMS on the local machine
                domain:  The market domain ['MARKET_PRICE', 'MARKET_BY_ORDER', 'MARKET_BY_ORDER']
                service: The service name
                ricName:  The RIC to find
            
            return : Full EXL file path name
        """ 
        
        exlFiles = self._get_EXL_files(fmsDir, "All")
        
        for exlFile in exlFiles:
            dom = xml.dom.minidom.parse(exlFile)
            
            # skip file if service does not match
            fieldNames = ['SERVICE']
            result = self._get_EXL_header_values(dom,fieldNames)
            if result['SERVICE'] != service:
                continue
            
            #find the ric and domain
            iteratorlist = dom.getElementsByTagName('exlObject') 
            for node in iteratorlist:
                foundRic = False
                foundDomain = False
                for subnode in node.childNodes:
                    if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:RIC':
                        if subnode.firstChild.data == ric:
                            foundRic = True
                    if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:DOMAIN':
                        if subnode.firstChild.data == domain:
                            foundDomain = True
                if foundRic == True and foundDomain == True:
                    return exlFile
    
        raise AssertionError('*ERROR* RIC %s, domain %s, service %s not found in any EXL file:' %(ric,domain,service))
    
    def get_EXL_and_RIC_from_domain_and_service(self, fmsDir, domain, service):
        """ Find first non-state-ric EXL file with a RIC for the specified domain and service
            The following state ric files are ignored:
            '*_cs_run', '*_dl_sav', '*_fd_time', '*_mk_holiday', '*_otfc','*_trd_time', '*_venue_heartbeat'
            
            Argument: 
                fmsDir: The Location of the FMS on the local machine
                domain: The market domain ['MARKET_PRICE', 'MARKET_BY_ORDER', 'MARKET_BY_ORDER']
                service: The service name
            
            return : Full EXL file path name and first RIC name
            
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1795
        """ 
        # It might help explain the code below, to understand that the structure of 
        # an EXL file.  A RIC definition is an "exlObject".  Example:
        # <exlObjects>
        #     <exlObject>
        #         <it:SYMBOL>BBFIX</it:SYMBOL>
        #         <it:RIC>BBFIX.O</it:RIC>
        #         <it:DOMAIN>MARKET_PRICE</it:DOMAIN>
        #         <it:INSTRUMENT_TYPE>NORMAL_RECORD</it:INSTRUMENT_TYPE>
        #         <exlObjectFields>
        #             <it:DSPLY_NAME>WM BLAIR BD INST</it:DSPLY_NAME>
        #             <it:OFFCL_CODE>000969251305</it:OFFCL_CODE>
        #        </exlObjectFields>
        #    </exlObject>
        #    <!-- Additional exlObject Tags --->
        # </exlObjects>
        
        list_of_state_ric_exl = ['_cs_run', '_dl_sav', '_fd_time', '_mk_holiday', '_otfc','_trd_time', '_venue_heartbeat']
        exlFiles = self._get_EXL_files(fmsDir, "All")

        for exlFile in exlFiles:
            # ignore state ric files
            if self._list_item_is_substring_of_searched_item(exlFile, list_of_state_ric_exl):
                continue
            dom = xml.dom.minidom.parse(exlFile)
            
            # skip file if service does not match
            fieldNames = ['SERVICE']
            result = self._get_EXL_header_values(dom,fieldNames)
            if result['SERVICE'] != service:
                continue
            
            #find first ric for the domain
            iteratorlist = dom.getElementsByTagName('exlObject') 
            for node in iteratorlist:
                ric = "Not Found"
                exlDomain = "Not Found"
                for subnode in node.childNodes:
                    if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:RIC':
                        ric = subnode.firstChild.data
                    if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:DOMAIN':
                        exlDomain = subnode.firstChild.data
                if ric != "Not Found" and exlDomain == domain:
                    return exlFile, ric
    
        raise AssertionError('*ERROR* No RIC found for domain %s and service %s in any EXL file:' %(domain,service))
    
    def get_DST_and_holiday_RICs_from_EXL(self,exlFile,ricName):
        """ Get DST RIC and holiday RIC from EXL
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1735

            return : DST RIC and holiday RIC, if found. Otherwise, returns 'Not Found'.
        """ 
        
        return self.get_ric_fields_from_EXL(exlFile,ricName,'DST_REF','HOLIDAYS_REF1')
    
    def get_ric_fields_from_EXL(self,exlFile,ricName,*fieldnames):
        """ Get field values of RIC from EXL.
           Looks for field in exlObject, if not found in exlObject, looks for field in exlHeader
           Argument:
               exlFile : full path of exlfile			   
               ricName : ric 
			   fieldnames : list of fields want to retrieve
           Return : list of value corresponding to fieldnames
           Example:
                get ric fields from EXL |C:\\config\\DataFiles\\Groups\\RAM\\MFDS\\MUT\\EXL Files\\nasmf_a.exl|AAAAX.O|PROD_PERM|
           
        """
         
        retList = []
        dom = xml.dom.minidom.parse(exlFile) 
        heanderDict = self._get_EXL_header_values(dom,fieldnames)
        ObjDict = self._get_EXL_object_values(dom,ricName,fieldnames)
        
        for fieldname in fieldnames:
            if (ObjDict[fieldname] != "Not Found"):
                retList.append(ObjDict[fieldname])
            elif (heanderDict[fieldname] != "Not Found"):
                retList.append(heanderDict[fieldname])
            else:
                raise AssertionError('*ERROR* %s not found for RIC(%s) in %s' %(fieldname, ricName, exlFile))

        return retList
         
    def _get_EXL_header_values(self,dom,fieldnames):
        """ Get field value(s) from EXL Header
            Arguments:
                dom: Dom object from parsing EXL file
                fieldnames : list of fields name
           Return : Dictionary with key = item found in fieldnames list
           [Remark] WE don't raise assertion for field not found case, as for some case we just want to check if field is exist
        """ 

        iteratorlist = dom.getElementsByTagName('exlHeader')
        
        #find the field
        fieldValues = {}
        for fieldname in fieldnames:
            fieldValues[fieldname] = "Not Found"
            
        for node in iteratorlist:
            for subnode in node.childNodes:
                for fieldname in fieldnames:
                    if subnode.nodeType == node.ELEMENT_NODE:
                            if subnode.nodeName == 'it:'+fieldname:        
                                fieldValues[fieldname] = subnode.firstChild.data
                            elif subnode.nodeName == 'exlHeaderFields':
                                for subnode_child in subnode.childNodes:
                                    if subnode_child.nodeName == 'it:'+fieldname:
                                        fieldValues[fieldname] = subnode_child.firstChild.data
        return fieldValues 
    
    def _get_EXL_object_values(self,dom,ricName,fieldnames):
        """ Get field value(s) from EXL exlObject given the ricname
            Arguments:
                dom: Dom object from parsing EXL file
                ricName : ric name
                fieldnames : list of fields name
            Return : Dictionary with key = item found in fieldnames list
           [Remark] WE don't raise assertion for field not found case, as for some case we just want to check if field is exist
        """ 
        
        iteratorlist = dom.getElementsByTagName('exlObject') 
        
        #find the ric and field
        fieldValues = {}            
        for node in iteratorlist:
            for fieldname in fieldnames:
                fieldValues[fieldname] = "Not Found"
            
            ric = ""
            for subnode in node.childNodes:
                if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:RIC':
                    if subnode.firstChild.data == ricName:
                        ric = subnode.firstChild.data
                for fieldname in fieldnames:
                    if subnode.nodeType == node.ELEMENT_NODE:
                        if subnode.nodeName == 'it:'+fieldname:
                            fieldValues[fieldname] = subnode.firstChild.data
                        elif subnode.nodeName == 'exlObjectFields':
                            for subnode_child in subnode.childNodes:
                                if subnode_child.nodeName == 'it:'+fieldname:
                                    fieldValues[fieldname] = subnode_child.firstChild.data
            if ric != "":
                break                
                        
        return fieldValues      
    
    def verify_no_duplicate_fids_between_constituents(self, das_path, pcapfile, constituNum1, constituMum2):
        """ compare two set of Fids name based on the input constituNums
            return : true if two set data are unique
            Argument : das_path| pcap file| constituNum1 | constituNum1
        """
        filter1 = 'TRWF_ConstituentNum = &quot;' + constituNum1 + '&quot;'
        filter2 = 'TRWF_ConstituentNum = &quot;' + constituMum2 + '&quot;'
        
        outputfile1 = self._get_extractorXml_from_pcap(das_path, pcapfile, filter1, "out1")
        outputfile2 = self._get_extractorXml_from_pcap(das_path, pcapfile, filter2, "out2")

        set1 = self.get_all_fids_name_from_DASXml(outputfile1[0])
        set2 = self.get_all_fids_name_from_DASXml(outputfile2[0])

        os.remove(outputfile1[0])
        os.remove(outputfile2[0])
            
        if not self.are_two_set_data_unique(set1, set2):
            raise AssertionError('*ERROR* duplicate fid has been found for constituents: %s in fid set: %s and constituents: %s in fid set: %s' %(constituNum1, set1, constituNum2, set2))
        
    def are_two_set_data_unique(self, set1, set2):
        new_set = set1.intersection(set2)
        if(len(new_set) == 0):
            return True
        
        return False    

    def _get_extractorTxt_from_pcap(self, das_path, pcapfile, filterstring, outputFilePrefix, maxFileSize=0):
        """ run DAS extractor locally and get DAS extractor's text output file
         Returns List output text file(s). Caller is responsible for deleting this generated text file.        
         Argument : das_path| pcap file| filter string| outputFilePrefix
         maxFileSize (MB): =0 mean no control on the output file size, > 0 output file would auto split to multiple files with suffix  filename_x 
        """ 
        outdir = os.path.dirname(pcapfile)
        pcap_to_txt_file_name = 'txtfromDAS.txt'
        outputtxtfile = outdir + "/" + outputFilePrefix + pcap_to_txt_file_name   
        rc = self.run_das_extractor_locally(das_path, pcapfile, outputtxtfile, filterstring, 'MTP', maxFileSize)
                
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

    def _get_extractorXml_from_pcap(self, das_path, pcapfile, filterstring, outputFilePrefix, maxFileSize=0):
        """ run DAS extractor locally and get DAS extractor's xml output file
         Returns List output xml file(s). Caller is responsible for deleting this generated xml file.        
         Argument : das_path| pcap file| filter string| outputFilePrefix
         maxFileSize (MB): =0 mean no control on the output file size, > 0 output file would auto split to multiple files with suffix  filename_x 
        """ 
        outdir = os.path.dirname(pcapfile)
        pcap_to_xml_file_name = 'xmlfromDAS.xml'
        outputxmlfile = outdir + "/" + outputFilePrefix + pcap_to_xml_file_name   
        rc = self.run_das_extractor_locally(das_path, pcapfile, outputxmlfile, filterstring, 'MTP', maxFileSize)
                
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

    def get_all_fids_name_from_DASXml(self, xmlfile):
        """get all fids from DAS extractor's xml output file
         Returns a set of fids appeared in the file.
         Argument : DAS extractor's xml output file name    
        """ 
        treeRoot = ET.parse(xmlfile).getroot()
        fidSet = Set();
        for atype in treeRoot.findall('.//FieldID'):
            val_result = atype.get('value')
            fidSet.add(val_result)
        
        return fidSet         

    def blank_out_holidays(self, srcExlFile, destExlFile):
        """ removes any defined holidays in the given srcExlFile and saves it to destExlFile
            srcExlFile : The full path and filename of the EXL file to remove blank out holidays in
            destExlFile : The full path and filename of the modified EXL file (to save to)
            return : 0 for success, non-zero for failure
            Assertion : When file open fails
        """                

        # Inner function to handle file opening
        def open_file(filename, mode):
            try:
                fileHandle = open(filename, mode) 
            except:
                raise AssertionError('Failed to open file %s' %filename)
                return 1, "NULL"
            return (0, fileHandle)

        # First open the exlFile for reading
        (returnCode, exlFileHandle) = open_file(srcExlFile, 'r')
        if returnCode != 0:
            return returnCode

        # Initialize some variables used for processing the file
        newExlFileContents = ""
        inExlObjectFields = bool(False)
        firstHolidayTag = bool(True)

        # Loop through each line of the file, examining the line
        for currentLine in exlFileHandle:
            # Here we track if we're in the <exlObjectFields> section
            if re.match('<exlObjectFields>', currentLine):
                inExlObjectFields = True
            elif re.match('</exlObjectFields>', currentLine):
                inExlObjectFields = False

            # Only write the current line if it's not holiday definition in the 
            # <exlObjectFields> sections. Holiday definitions begins with <it:HLY
            if inExlObjectFields  and re.match('^<it:HLY.', currentLine):
                if firstHolidayTag:
                    # Replace all holiday definitions with just a single blank one
                    newExlFileContents += "<it:HLY00_START_TIME>#BLANK#</it:HLY00_START_TIME>\n"
                    newExlFileContents += "<it:HLY00_END_TIME>#BLANK#</it:HLY00_END_TIME>\n"
                    newExlFileContents += "<it:HLY00_DESC>#BLANK#</it:HLY00_DESC>\n"
                    firstHolidayTag = False
            else:
                    newExlFileContents += currentLine

        # Close the EXL file we opened for reading
        exlFileHandle.close()

        # Overwrite the EXL file with the new contents
        (returnCode, exlFileHandle) = open_file(destExlFile, 'w')
        if returnCode != 0:
            return returnCode
        exlFileHandle.write(newExlFileContents)
        exlFileHandle.close()

        return 0
    
    def _list_item_is_substring_of_searched_item(self, search_str, list_of_state_ric_exl):
        """check if list item is substring of the search_str
        Return True if find matched item.
        """
        
        for x in list_of_state_ric_exl:
            if re.search(x, search_str):
                return True
            
        return False

    def convert_to_lowercase_workaround(self, str1):
        """This KW is temporary because 'Convert to lowercase' KW is not available until Robot Framework 2.8.6.   
        After upgrading to Robot 2.8.6, this KW should be deprecated and 'Convert to Lowercase' used
        """
        lower = str1.lower()
        return lower
        
    def get_matches_workaround(self, listToSearch, pattern):
        """This KW is temporary because 'Get Matches' KW is not available until Robot Framework 2.8.6.   
        After upgrading to Robot 2.8.6, this KW should be deprecated and 'Get Matches' used
        
        Returns a list of matches to pattern in list

        Example:
        | get matches workaround | ${FMScategories} | Service_*
        """
        matches = []
        for x in listToSearch:
            if re.search(pattern, x):
                matches.append(x)
        return matches
        
    def verify_cache_contains_only_configured_context_ids(self, cachedump_file_name_full_path, filter_string): 
        """Get set of context ID from cache dump file and venue xml_config file
        and verify the context id set from cache dump is subset of context id set defined in fms filter string
        Argument : cachedump file, venue configuration file
        Returns : true if dumpcache_context_ids_set <= filterstring_context_id_set
        
        Examples:
        | verify cache contains only configured context ids | cache dump file |venue configuration file   
        """       
        
        filterstring_context_id_set = self.get_context_ids_from_fms_filter_string(filter_string)
        if len(filterstring_context_id_set) == 0:
            raise AssertionError('*ERROR* cannot find context ids from fms filter string %' %filter_string)
        
        dumpcache_context_ids_set = self.get_context_ids_from_cachedump(cachedump_file_name_full_path)
        if len(dumpcache_context_ids_set) == 0:
            raise AssertionError('*ERROR* cannot found dumpcache context ids in %s' %cachedump_file_name_full_path)
        
        if dumpcache_context_ids_set <= filterstring_context_id_set:
            return True
        else:
            raise AssertionError('*ERROR* dumpcache context ids %s are not all in configured context ids %s' %(dumpcache_context_ids_set, filterstring_context_id_set))
        
    def get_context_ids_from_cachedump(self, cachedump_file_name):  
        """Returns a set of context_ids appeared in the cachedump.csv file.
         Argument : cache dump file full path

        Examples:
        | get context ids from cachedump | cachedump file name |     
        """    
        if not os.path.exists(cachedump_file_name):
            raise AssertionError('*ERROR*  %s is not available' %cachedump_file_name)
            
        context_id_val_set = Set()
        n = 0
        try:
            with open(cachedump_file_name) as fileobj:
                for line in fileobj:
                    n = n+1
                    if n>1:
                        context_id_val = line.split(",")[6]
                        if context_id_val:
                            context_id_val_set.add(context_id_val)
                            
        except IOError:
            raise AssertionError('*ERROR* failed to open file %s' %cachedump_file_name)
            
                    
        return context_id_val_set   #Set(['3470', '3471', '2452', '1933', '1246', '1405'])
    
    def get_context_ids_from_fms_filter_string(self, fms_filter_string): 
        """Returns a set of context_ids appeared in the fms filter string.
         Argument : fms_filter_string like <FilterString>CONTEXT_ID = 1052 OR CONTEXT_ID = 1053</FilterString>    
        """ 
        context_id_set = Set()
        match = []
        if fms_filter_string and fms_filter_string.strip():
            match  = re.findall(r'\bCONTEXT_ID\s*=\s*\w*', fms_filter_string)
              
        for m in match:
            n = m.split('=')
            if len(n) == 2:
                context_id_set.add(n[1].strip())
            
        return context_id_set

    def add_ric_to_exl_file(self, exlFileSource, exlFileTarget, ric, symbol=None, domain="MARKET_PRICE", instrumentType="NORMAL_RECORD", displayName="TEST RIC", officialCode="1"):
        """ Add a new RIC to an existing EXL file:
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1713
            Argument : exlFileSource: Full path name to the EXL file you wish to add a RIC to
                       exlFileTarget: Full path to the saved off file that will contain the added RIC after calling this method
                       ric: Name of RIC you wish to add
                       symbol: Symbol name of RIC you wish to add (default is same as RIC name)
                       domain: Domain of RIC you wish to add (default is MARKET_PRICE)
                       instrumentType: Instrument Type of RIC you wish to add (default is NORMAL_RECORD)
                       displayName: Display Name of RIC you wish to add (default is TEST RIC)
                       officialCode: Official Code of RIC you wish to add (default is 1)
            return : A successful return code is 0.  All others are errors.
        """ 

        # This is an inner sub to get the "value node" for a given tag node.  The way 
        # the XML parser works is that the value of a tag is a child node of the 
        # "tag node".
        def get_tag_value_node(node, tag):
           tagNode = node.getElementsByTagName(tag)
           if(len(tagNode) == 0):
                return None
           if(tagNode[0].hasChildNodes() == False):
                return None
           return tagNode[0].childNodes[0]

        # This is an inner sub to get the value of a given tag in a node
        def get_tag_value(node, tag):
            tagValueNode = get_tag_value_node(node, tag)
            if(tagValueNode == None):
                return None
            return tagValueNode.nodeValue

        # This is an inner sub to set the value of a given tag in a node
        def replace_tag_value(node, tag, value):
            tagValueNode = get_tag_value_node(node, tag)
            if(tagValueNode != None):
                tagValueNode.nodeValue = value

		# Open up the source EXL file with an XML parser
        xmlParser = None
        try:
            xmlParser = xml.dom.minidom.parse(exlFileSource)  
        except Exception, exception:
            raise AssertionError('XML DOM parser failed to open EXL source file %s Exception: %s' % (exlFileSource, exception))
            return 1

        # Get the exlObjects section of the data.  This is where the RIC definitions 
        # are.  If this section doesn't exist in the given EXL file thats an error.
        exlObjectNode = xmlParser.getElementsByTagName('exlObjects') 
        if(len(exlObjectNode) == 0):
            raise AssertionError('No exlObjects tags found in EXL file')
            return 2
        
        # Get the exlObjects within the exlObjects tag and make sure at least 
        # one RIC definition exists.
        ricNodes = exlObjectNode[0].getElementsByTagName('exlObject')
        if(len(ricNodes) == 0):
            raise AssertionError('No exlObject tag found in EXL file')
            return 3

        # Make sure the given RIC doesn't already exist in the EXL file
        for ricNode in ricNodes:
            if(ric == get_tag_value(ricNode, "it:RIC")):
                raise AssertionError('RIC %s already exists in EXL file %s' % (ric, exlFileSource))
                return 4

        # Clone the first RIC EXL object to use as a template for our new RIC
        newNode = ricNodes[0].cloneNode(1)

        # If no specific symbol is given we make it the same as the RIC
        if(symbol == None): 
            symbol = ric

        # Replace the values in our template with given values
        replace_tag_value(newNode, "it:RIC", ric)
        replace_tag_value(newNode, "it:SYMBOL", symbol)
        replace_tag_value(newNode, "it:DOMAIN", domain)
        replace_tag_value(newNode, "it:INSTRUMENT_TYPE", instrumentType)
        replace_tag_value(newNode, "it:DSPLY_NAME", displayName)
        replace_tag_value(newNode, "it:OFFCL_CODE", officialCode)

        # Insert the new RIC EXL Object
        exlObjectNode[0].insertBefore(newNode, exlObjectNode[0].childNodes[0])

        # Save the output EXL file
        try:
            fileHandle = open(exlFileTarget, 'w') 
            fileHandle.write(xmlParser.toxml())
            fileHandle.close()
        except Exception, exception:
            raise AssertionError('Failed to open EXL target file %s Exception: %s' % (exlFileTarget, exception))
            return 5

        return 

    def _search_MTE_config_file(self,venueConfigFile,*xmlPath):
        foundConfigValues = []
        
        xmlPathLength = len(xmlPath)
        if xmlPathLength < 1:
            raise AssertionError('*ERROR*  Need to provide xmlPath to look up.')
        elif xmlPathLength > 1:
            xmlPathString = '/'.join(map(str, xmlPath))
        else:
            xmlPathString = str(xmlPath[0])
            
        if not os.path.exists(venueConfigFile):
            raise AssertionError('*ERROR*  %s is not available' %venueConfigFile)
        
        with open (venueConfigFile, "r") as myfile:
            linesRead = myfile.readlines()
    
        # Note that the following workaround is needed to make the venue config file a valid XML file.
        linesRead = "<GATS>" + ''.join(linesRead) + "</GATS>"
        
        root = ET.fromstring(linesRead)
        
        for foundNode in root.iterfind(".//" + xmlPathString):
            foundConfigValues.append(foundNode.text)
            
        return foundConfigValues
    
    def get_MTE_config_list_by_path(self,venueConfigFile,*xmlPath):
        """ Gets value(s) from venue config file
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1798
            
            params : venueConfigFile - full path to local copy of venue configuration file
                     xmlPath - one or more node names that identify the XML path

            return : list containing value(s) of given xmlPath, if found. Otherwise, returns empty list
            
            Examples :
            | ${domainList}= | get MTE config list | ${LOCAL_TMP_DIR}/venue_config.xml | FMS | MFDS | Domain | Z |

            Venue config file example:
            <FMS>
              <Services type="multistring">
                <Z>MFDS</Z>
              </Services>
              <MFDS>
                <Domain type="multistring">
                  <Z>MARKET_PRICE</Z>
                  <Z>MARKET_BY_PRICE</Z>
                </Domain>
                <FilterString>CONTEXT_ID = 1052 OR CONTEXT_ID = 1053</FilterString>
              </MFDS>
            </FMS>
        """ 
        
        foundConfigValues = self._search_MTE_config_file(venueConfigFile,*xmlPath)
        
        if len(foundConfigValues) == 0:
            return []
        else:
            return foundConfigValues
        
    def get_MTE_config_value(self,venueConfigFile,*xmlPath):
        """ Gets value from venue config file
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1736
            
            params : venueConfigFile - full path to local copy of venue configuration file
                     xmlPath - one or more node names that identify the XML path

            return : value of given xmlPath, if found. If multiple values found, will assert an error. Otherwise, returns "NOT FOUND" if nothing found.
            
            Examples :
            | ${filterString}= | get MTE config value | FMS | MFDS | FilterString |
            | ${connectTimesRIC}= | get MTE config value | ConnectTimesRIC |
            
            Venue config file example:
            <FMS>
              <Services type="multistring">
                <Z>MFDS</Z>
              </Services>
              <MFDS>
                <Domain type="multistring">
                  <Z>MARKET_PRICE</Z>
                  <Z>MARKET_BY_PRICE</Z>
                </Domain>
                <FilterString>CONTEXT_ID = 1052 OR CONTEXT_ID = 1053</FilterString>
              </MFDS>
            </FMS>
        """ 
        
        foundConfigValues = self._search_MTE_config_file(venueConfigFile,*xmlPath)
        
        if len(foundConfigValues) == 0:
            return "NOT FOUND"
        elif len(foundConfigValues) > 1:
            raise AssertionError('*ERROR*  Found more than 1 value [%s] in venue config file: %s' %(', '.join(foundConfigValues), venueConfigFile))
        else:
            return foundConfigValues[0]
        
        
        
    def get_MTE_config_list_by_section(self, venueConfigFile, section, tag):
        """ Gets value(s) from venue config file based on the venue config file section node name and subelement node name (tag)
            Argument : venueConfigFile : full path to local copy of venue configuration file
                     section : top section node in venueConfigFile
                     tag : subelement node name under section appeared in venueConfigFile
            Return : value list of given node name, if found. Otherwise, returns 'Not Found'.
            Examples :
            | ${labelIDs}= | get MTE config value list| venue_config_file| Publishing | LabelID |
             
        """ 
        if not os.path.exists(venueConfigFile):
            raise AssertionError('*ERROR*  %s is not available' %venueConfigFile)
         
        with open (venueConfigFile, "r") as myfile:
            linesRead = myfile.readlines()
        # Note that the following workaround is needed to make the venue config file a valid XML file.
        linesRead = "<GATS>" + ''.join(linesRead) + "</GATS>"
        root = ET.fromstring(linesRead)
        sectionNode = root.find(section)
        if sectionNode is None:
            raise AssertionError('*ERROR*  Missing [%s] element from venue config file: %s' %(section, venueConfigFile))
            
        labelIDNode = sectionNode.findall('.//%s'%tag)
        if labelIDNode is None:
            raise AssertionError('*ERROR*  Missing %s element under section %s from venue config file: %s' %(tag, section, venueConfigFile))
        
        LabelIdList = []
        for val in labelIDNode:
            if val.text:
                LabelIdList.append(val.text)
                
        if not len(LabelIdList):  
            raise AssertionError('*ERROR*  Missing %s element text from venue config file: %s' %(tag, venueConfigFile))
        
        return LabelIdList
    
            
    def remove_xinclude_from_labelfile(self, ddnLabels_file, updated_ddnLabels_file):
        '''  
            Argument : ddnLabels_file : local ddnLabels.xml file or ddnReqLabels.xml
                       updated_ddnLabels_file : output file name
            Return : updated_ddnLabels_file with line <xi:include href="ddnServers.xml"/> removed from ddnLabels_file
        '''
        xi_include = 'xi:include' 
        label_file = open(ddnLabels_file,'r')
        modified_label_file = open(updated_ddnLabels_file,'w')
        
        label_file_lines = label_file.readlines()
        for line in label_file_lines:
            if xi_include not in line:
                modified_label_file.write(line)
              
        label_file.close()
        modified_label_file.close()
        
    
    def get_multicast_address_from_lable_file(self, ddnLabels_file, labelID):
        ''' Extract multicast IP and port from label file based on the labelID
            Argument : ddnLabels_file:  ddnLabels or ddnReqLabels file
                       labelID : labelID defined in venue config file
            Return : list contains multicast ip and port
        '''     
        tree = ET.parse(ddnLabels_file)
        root = tree.getroot()
        
        labelNode = root.findall('.//label')
        if not labelNode: 
            raise AssertionError('*ERROR* label element does not exist in %s' % ddnLabels_file)
        
        for node in labelNode:
            if node.get('ID') == labelID:
                multTagText = node.find('multTag').text
                break
        
        if not multTagText:
            raise AssertionError('*ERROR* could not find multTag text for labelID %s' % labelID)
        
        multAddrNode = root.findall('.//multAddr')    
        for node in multAddrNode:
            if node.get('TAG') == multTagText:
                multicast_ip = node.get('ADDR')
                multicast_port_tag = node.get('PORT')
                break;
            
        if not multicast_port_tag:
            raise AssertionError('*ERROR* could not find port for multAddr node %s' % multTagText)
        
        for node in root.findall('.//port'):
            if node.get('ID') == multicast_port_tag:
                multicast_port = node.text
                
        if not multicast_ip and not multicast_port: 
            raise AssertionError('*ERROR* failed to get multicast address for LabelID %s' % labelID)
        
        multicast_address = []        
        multicast_address.append(multicast_ip)
        multicast_address.append(multicast_port)
        
        return multicast_address
    
    
    def map_to_PMAT_numeric_domain(self, domain):
        ''' Map string domain to PMAT numeric domain
            Argument : domain : Data domain in following format
                                MarketByOrder, MarketByPrice, MarketMaker, MarketPrice, symbolList.
            Return : 0 for MarketByOrder, 1 for MarketByPrice, 2 for MarketMaker, 3 for MarketPrice, 4 for symbolList.
        ''' 
        domainDict = {'MARKETBYORDER': 0, 'MARKETBYPRICE': 1, 'MARKETMAKER': 2, 'MARKETPRICE': 3, 'SYMBOLList':4}
        domainUpper = domain.upper()
        ret = domainDict[domainUpper]
        if not (ret >= 0 and ret <=4):
            raise AssertionError('*ERROR* invalid domain %s for PMAT' %domain)
        
        return ret
        
        
    def run_PMAT(self, pmat_dir, action,*params):    
        ''' Call PMAT.exe  
            PMAT doc is available at https://thehub.thomsonreuters.com/docs/DOC-110727
            Argument : pmat_dir : PMAT installed directory
                       action : possible values are Dump, Drop, Modify, Upgrade, Insert
                       params : a variable list of  arguments based on action.
            Return : rc should be 0.  
            examples : | ${ret}= | run PMAT| dump | --dll Schema_v6.dll | --db local_persist_file.DAT | --ric AAAAX.O | --domain 3 | --outf c:/tmp/pmat_dump.xml |
                       | ${ret}= | run PMAT| drop | --dll Schema_v5.dll | --db local_persist_file.DAT | --id 2 |
                       | ${ret}= | run PMAT| upgrade | --dll upgrade_Schema_v5.Schema_v6.dll | --db c:\PERSIST_CXA_V5.DAT | --newdb c:\PERSIST_CXA_V6.DAT
                       | ${ret}= | run PMAT| modify | --dll <modify dll> | --db <database file> | --xml <xml command file>
        '''
        #output_file = 'pmat_dump.txt'
        #cmdstr = 'pmat dump --dll Schema_v6.dll --db %s --ric %s --domain %d --outf %s'%(local_persist_file, ric, domain_no, output_file)
        
        cmd = 'PMAT %s' %action
        cmd = cmd + ' ' + ' '.join(map(str, params))
    
        rc,stdout,stderr  = _run_local_command(cmd, True, pmat_dir)
        if rc != 0:
            raise AssertionError('*ERROR* in running PMAT %s' %stderr)  
        
        return rc
        
        
    def verify_ric_in_persist_dump_file(self, persist_dump_file, ric, domain):
        ''' Check if ric and domain appeared in the persist_dump_file. 
            persist_dump_file usually contains one RIC and Domain if user applies RIC and Domain filter in running PMAT dump.
            Argument : persist_dump_file:  the output file generated by runing PMAT with dump option
                       ric :  ric that need to be checked
                       domain : data domain for the ric in PMAT domain format: MarketPrice, MarketByOrder etc
            Return : Nil
        '''     
        if not os.path.exists(persist_dump_file):
            raise AssertionError('*ERROR*  %s is not available' %persist_dump_file) 
        
        tree = ET.parse(persist_dump_file)
        root = tree.getroot() 
        
        ric_path = './/DatabaseEntry/RIC'
        domain_path = './/DatabaseEntry/DOMAIN'
    
        ric_nodes = root.findall(ric_path)
        if ric_nodes is None:
            raise AssertionError('*ERROR*  Missing RIC element under %s from file: %s' %(ric_path, persist_dump_file))

        ric_exist = False
        for val in ric_nodes:
            if val.text == ric:
                ric_exist = True
                break
                
        if not ric_exist:  
            raise AssertionError('*ERROR* ric %s is not found in persist file %s' %(ric, persist_dump_file))  
        
        domain_exist = False
        domain_nodes = root.findall(domain_path)
        if domain_nodes is None:
            raise AssertionError('*ERROR*  Missing DOMAIN element under %s from file: %s' %(domain_path, persist_dump_file))
        
        for val in domain_nodes:
            if val.text.upper() == domain.upper():
                domain_exist = True
                break
                
        if not domain_exist:  
            raise AssertionError('*ERROR* domain %s is not found in persist file %s' %(domain, persist_dump_file))  
    
    def get_all_fids_from_PersistXml(self, xmlfile):
        """get all fids from PMAT extactor's xml output file
         Returns a list of fids appeared in the file.
         Argument : PMAT extractor's xml output file name    
        """ 
        treeRoot = ET.parse(xmlfile).getroot()
        fidsSet = [];
        for atype in treeRoot.findall('.//FIELD'):
            fid = atype.get('id')
            fidsSet.append(fid)
        
        return fidsSet
    
    def get_sps_ric_name_from_label_file(self, ddnLabelFile, MTEName, labelID):
        ''' Extract multicast IP and port from label file based on the labelID
        
            Argument : ddnLabelsFile - the local ddnLabels file name e.g. c:\temp\ddnLabel.xml
                       MTEName - the MTE name, e.g. MFDS1M
                       labelID - labelID defined in venue config file

            Return : the text of SPS RIC name
            
            Examples :
            ${spsRicName} | get sps ric name from label file | c:\temp\ddnLabel.xml | MFDS1M | 1234 |
            
        '''     
        tree = ET.parse(ddnLabelFile)
        root = tree.getroot()
        
        labelNodes = root.findall('.//label')
        if not labelNodes: 
            raise AssertionError('*ERROR* label element does not exist in %s' % ddnLabelFile)
        
        for labelNode in labelNodes:
            if labelNode.get('ID') == labelID:
                providerNodes = labelNode.findall('provider')
                for providerNode in providerNodes:
                    if providerNode.get('NAME') == MTEName:
                        spsText = providerNode.find('sps').text
                        return spsText
                break
        
        if not spsText:
            raise AssertionError('*ERROR* could not find sps ric text for labelID %s' % labelID)
    
    def _and_DAS_filter_string(self, filterString1, filterStirng2):
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
        

    def _build_DAS_filter_string(self, msgClass = '*', ric = '*', constitNum = '*'):
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
            filterstring = self._and_DAS_filter_string(filterstring, filterstring_for_ric)
        else:
            pass
        
        if constitNum != '*':
            filterstring_for_constitNum = 'Response_constitNum = &quot;%s&quot;' % constitNum
            filterstring = self._and_DAS_filter_string(filterstring, filterstring_for_constitNum)
        else:
            pass
        
        return filterstring

    def verify_fid_value_in_message(self, pcapfile, dasdir, ric, constitNum, fidList=[], valueList=[]):
        """ Verify if the fid value equals to the specified value

            Argument : pcapfile - the full name of pacpfile, it should be local path e.g. C:\\temp\\capture.pcap
                       dasdir - the installation folder of DAS, e.g. C:\\Program Files\\Reuters Test Tools\\DAS
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
        filterstring = self._build_DAS_filter_string('Response', ric, constitNum);
        
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,'fidVerificationVspcap',20)
        
        messageNode = self._xml_parse_get_all_elements_by_name(outputxmlfilelist[0], 'Message')
        
        fidsAndValues = self._xml_parse_get_fidsAndValues_for_messageNode(messageNode[0])

        ricname = self._xml_parse_get_field_from_MsgKey(messageNode[0],'Name')

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
            self._verify_FID_value_in_message(fidsAndValues, fid, valueList[i])
            i += 1
            
        for delFile in outputxmlfilelist:
            os.remove(delFile)

    def verify_CMP_NME_ET_in_message(self, pcapfile, dasdir, ric):
        """ Verify CMP_NME_ET in message, it should be 0 or 1 or 2 or 3

            Argument : pcapfile - the full name of pacpfile, it should be local path e.g. C:\\temp\\capture.pcap
                       dasdir - the installation folder of DAS, e.g. C:\\Program Files\\Reuters Test Tools\\DAS
                       ric - the specified ric name if you want to check

            Return : Nil
            
            Examples :
            verify CMP_NME_ET in message | capture.pcap | C:\\Program Files\\Reuters Test Tools\\DAS | AAAX.O |
            
        """
        #Check if pcap file exist
        if (os.path.exists(pcapfile) == False):
            raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)
        #Build the filterstring
        filterstring = self._build_DAS_filter_string('*', ric, 0);
        
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,'setIDVerificationVspcap',20)
        
        messageNode = self._xml_parse_get_all_elements_by_name(outputxmlfilelist[0], 'Message')
        
        fidsAndValues = self._xml_parse_get_fidsAndValues_for_messageNode(messageNode[0])

        ricname = self._xml_parse_get_field_from_MsgKey(messageNode[0],'Name')

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

    def verify_setID_in_message(self, pcapfile, dasdir, ric, expectedSetID, msgType):
        """ Verify if the SetID in message equals with expected value 

            Argument : pcapfile - the full name of pacpfile, it should be local path e.g. C:\\temp\\capture.pcap
                       dasdir - the installation folder of DAS, e.g. C:\\Program Files\\Reuters Test Tools\\DAS
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
        filterstring = self._build_DAS_filter_string('*', ric);
        
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,'setIDVerificationVspcap',20)
        
        messageNode = self._xml_parse_get_all_elements_by_name(outputxmlfilelist[0], 'Message')
        
        for msgkey in messageNode[0].getiterator('MsgBase'):
            element = msgkey.find('SetID')
            if (element != None):
                if element.get('value') != expectedSetID:
                    raise AssertionError('*ERROR* The set id in message is %s does not equal the expected %s' % (element.text, expectedSetID))
                
        for delFile in outputxmlfilelist:
            os.remove(delFile)
            
    def verify_key_compression_in_message(self, pcapfile, dasdir, ric):
        """ Verify if the key name compression is enabled 

            Argument : pcapfile - the full name of pacpfile, it should be local path e.g. C:\\temp\\capture.pcap
                       dasdir - the installation folder of DAS, e.g. C:\\Program Files\\Reuters Test Tools\\DAS
                       ric - the specified ric name if you want to check
            Return : Nil
            
            Examples :
            verify key compression in message | capture.pcap | C:\\Program Files\\Reuters Test Tools\\DAS | AAAX.O | 
            
        """        
        #Check if pcap file exist
        if (os.path.exists(pcapfile) == False):
            raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)
        #Build the filterstring
        filterstring = self._build_DAS_filter_string('*', ric);
        
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,'setIDVerificationVspcap',20)
        
        messageNode = self._xml_parse_get_all_elements_by_name(outputxmlfilelist[0], 'Message')
        for node in messageNode:
            NameEncodingType = self._xml_parse_get_field_from_MsgKey(node,'NameEncodingType')
            print NameEncodingType
            if NameEncodingType == '0':
                    raise AssertionError('*ERROR* The compression in message is %s ' % (NameEncodingType))
        
        for delFile in outputxmlfilelist:
            os.remove(delFile)
            
    def get_mangling_rule_content(self,rule,configFileLocalFullPath):
        """ Get the setting for specific mangling rule found in manglingConfiguration.xml
            This include 
            tag <RIC> : enabled , Prefix, Suffix
            tag <PE> : enabled, PE value
            tag <IMSOUT> : enabled, IMSOUT value
            
            Argument : rule -  'SOU', 'BETA', RRG', 'UNMANGLED'
                       configFileLocalFullPath - full path included config filename at Control PC
                       
            Return : dictionary of setting e.g.
                 {'RIC': {'Prefix': '![', 'enabled': 'true', 'Suffix': None}, 
                  'PE': {'enabled': 'false', 'text': '0'}, 
                  'IMSOUT': {'enabled': 'false', 'text': '0'}}
            
            Examples :
            | &{manglingRuleContent}| get mangling rule content |SOU | C:\\temp\\manglingConfiguration.xml
        """
                
        #safe check for rule value
        if (LinuxToolUtilities().MANGLINGRULE.has_key(rule.upper()) == False):
            raise AssertionError('*ERROR* (%s) is not a standard name' %rule)    
        
        retContent= {}
        tree = ET.parse(configFileLocalFullPath)
        root = tree.getroot()
        retIter = root.iter('Rule')
        for child in retIter:
            if (child.attrib['id'] == LinuxToolUtilities().MANGLINGRULE[rule]):
                for index in range(len(child)):
                    retContent[child[index].tag] = child[index].attrib
                    if (child[index].tag == 'RIC'):
                        for sub_index in range(len(child[index])):
                            retContent[child[index].tag][child[index][sub_index].tag] = child[index][sub_index].text 
                    else:
                        retContent[child[index].tag]['text'] = child[index].text

        if (len(retContent) == 0):
            raise AssertionError('*ERROR* Missing mangling configuration for rule %s in %s'%(rule,configFileLocalFullPath))
        
        if not (retContent.has_key('RIC')):
            raise AssertionError('*ERROR* Missing <RIC> in %s'%(configFileLocalFullPath))
        
        if not (retContent['RIC'].has_key('Prefix')):
            raise AssertionError('*ERROR* Missing <Prefix> under <RIC> in %s'%(configFileLocalFullPath))
            
        if not (retContent.has_key('PE')):
            raise AssertionError('*ERROR* Missing <PE> in %s'%(configFileLocalFullPath))            
        
        if not (retContent['PE'].has_key('text')):
            raise AssertionError('*ERROR* Missing value for <PE> in %s'%(configFileLocalFullPath))  
                
        return retContent
      
    def convert_dataView_response_to_dictionary(self,dataview_response):
        """ capture the FID Name and FID value from DateView output which return from run  run_dataview

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
                if (len(fidAndValue) == 2):
                    fidIdAndfidName = fidAndValue[0].split()
                    if (len(fidIdAndfidName) == 3):
                        fidsAndValuesDict[fidIdAndfidName[2].strip()] = fidAndValue[1].strip()
                    else:
                        raise AssertionError('*ERROR* Unexpected FID/value format found in dataview response (%s), expected format (FIDNUM -> FIDNAME, FIDVALUE)',line) 
                else:
                    raise AssertionError('*ERROR* Unexpected FID/value format found in dataview response (%s), expected format (FIDNUM -> FIDNAME, FIDVALUE)',line)
        
        return fidsAndValuesDict
    
    def verify_mangling_from_dataview_response(self,dataview_response,expected_pe,expected_ricname):
        """ Based on the DataView response to check if the expected Ric could be retrieved from MTE and having expected PE value

            Argument : dataview_response - stdout return from run_dataview
                       expected_pe - a list of expected PE values
                       expected_ricname - expected RIC name
                       
            Return : N/A
            
            Examples :
            |verify mangling from dataview response |  response | [4128, 4245, 4247] | ![HSIU5
        """   
                        
        fidsAndValues = self.convert_dataView_response_to_dictionary(dataview_response)
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
    
    def _verify_response_message_num_with_constnum(self,pcapfile,venuedir,dasdir,ricname,constnum):
        """ internal function used to verify response message with constnum for RIC in MTE output pcap message 

            Argument : pcapFile : is the pcap fullpath at local control PC  
            venuedir : location from remote TD box for search FIDFilter.txt
            dasdir : location of DAS tool  
            ricname : target ric name    
            constnum: Response_constitNum       
            return : Nil
                       
            Return : N/A   
        """  
        if (constnum == 63):
            hasC = False
            fidfilter = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt(venuedir)
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
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,outputfileprefix)
        messages = self._xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)
        if (len(messages) == 0):
            raise AssertionError('*ERROR* no C%s message found'%constnum) 
        if (len(messages) > 1):
            raise AssertionError('*ERROR* more than 1 C%s message found, the num is %s'%(constnum,len(messages))) 
                
        for delFile in outputxmlfilelist:
            os.remove(delFile)
        
        os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log") 
        
    def verify_all_response_message_num(self,pcapfile,venuedir,dasdir,ricname):
        """ keyword used to verify the response message for RIC in MTE output pcap message, 
            pcapFile : is the pcap fullpath at local control PC  
            venuedir : location from remote TD box for search FIDFilter.txt
            dasdir : location of DAS tool  
            ricname : target ric name            
            return : Nil
            
            verify:
            1. C0 , C1 and C63 message response 
            
            example:
            verify all response message num  |   ${LOCAL_TMP_DIR}/capture_local.pcap  |   ${VENUE_DIR}   |  ${DAS_DIR}  |   ${pubRic}
        """   
        self._verify_response_message_num_with_constnum(pcapfile,venuedir,dasdir,ricname,0)    
        self._verify_response_message_num_with_constnum(pcapfile,venuedir,dasdir,ricname,1)    
        self._verify_response_message_num_with_constnum(pcapfile,venuedir,dasdir,ricname,63)   
   

    def get_DVT_rule_file(self, dir):
        """ Search a local DVT rule file in the specified folder, and return it.
            This function will find the latest DVT rule if multiple files is found.
            The rule of deciding the latest rule file is checking the digit in the file name.
            Normally, the file name should be 'TRWFRules-72_L7_v2.1.0_SNFDCMPLR_20151118.xml', '72' can be used for sorting the file.
            
            Argument:
            dir : the local folder you want to search, normally it should be ${DAS_DIR}, e.g. 'C:\Program Files\Reuters Test Tools\DAS'
            return : the DVT rule file name
            
            Example:
            ${ruleFilePath} | get_DVT_rule_file | ${DAS_DIR}
        """
        files = glob.glob(os.path.join(dir, '*TRWFRules*.xml'))
        if len(files) == 0:
            raise AssertionError('*ERROR* Cannot find DVT rule file in %s' %dir)
        files.sort(key = lambda x:filter(str.isdigit, os.path.basename(x)))
        return files[-1]

    def validate_messages_against_DVT_rules(self,pcapfile,dasdir,rulefile):
        """ Perform DVT Validation
            
            Argument:
            pcapfile : the local pcap file path
            dasdir: the das installed path
            rulefile: the rule file path, see 'get_DVT_rule_file' founction
            return : N/A
            
            Example:
            validate messages against DVT rules | c:\temp\local_capture.pcap | ${DAS_DIR} | ${ruleFilePath}
        """   
        
    	#Check if pcap file exist
        if (os.path.exists(pcapfile) == False):
            raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)

        #Check if rule file exist
        if (os.path.exists(rulefile) == False):
            raise AssertionError('*ERROR* %s is not found at local control PC' %rulefile)

        pcappath = os.path.dirname(pcapfile)
        outputfile = os.path.join(pcappath, 'DVT_output.csv')

        res = self.run_das_dvt_locally(dasdir, pcapfile, outputfile, 'CHE', '', rulefile)
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
    
    def _run_local_SCWCLI(self,scwcli_dir,cmd):
        """ Run SCWCli at Slave

            Argument : scwcli_dir - full path of SCWCli.exe
                       cmd - input parameters for SCWCLi.exe
                       
            Return :
            
            Examples :
            |${ret}| run SCWCLI | C:\\SCW\\ | -demote HKF02M A -ip 10.32.15.187 -port 27000 -user root -pass Pegestech01|
        """
        
        cmd = 'SCWCLi.exe %s'%cmd
        print cmd
    
        rc,stdout,stderr  = _run_local_command(cmd, True, scwcli_dir)
        if rc != 0:
            raise AssertionError('*ERROR* in running SCWLLi.exe %s' %stderr)  
        
        return rc
    
    def switch_MTE_LIVE_STANDBY_status(self,scwcli_dir,mteName,node,status,user,password,che_ip,port='27000'):
        """ To switch specific MTE instance to LIVE or STANDBY

            Argument : scwcli_dir - full path of SCWCli.exe
                       mteName - MTE instance name e.g. HKF02M
                       node - A,B,C,D
                       status - LIVE:Switch to Live, STANDBY:Switch to Standby
                       user - login name for the TD box
                       password - login password for the TD box
                       che_ip - IP of the TD box
                       port - port no. that used to communicate with the SCW at TD box
                             
            Return :
            
            Examples :
            |switch MTE LIVE STANDBY status | C:\\SCW\\bin  | HKF02M | A | LIVE | ${USERNAME} | ${PASSWORD} | ${CHE_A_IP} | 
        """
       
        if (status == 'LIVE'):
            cmd = "-promote "
        elif(status == 'STANDBY'):
            cmd = "-demote "
        else:
            raise AssertionError('*ERROR* Unknown status %s' %status)
            
        cmd = cmd + '%s %s -ip %s -port %s -user %s -pass %s'%(mteName,node,che_ip,port,user,password)
        self._run_local_SCWCLI(scwcli_dir,cmd)
    
    def get_FidValue_in_message(self,pcapfile,dasdir,ricname, msgClass):
        """ To verify the insert icf file can update the changed fid and value correct
        
        Argument :         
                    pcapFile : is the pcap fullpath at local control PC                      
                    dasdir : location of DAS tool  
                    ricname:    
                    msgClass: UPDATE or RESPONSE               
                  : 
                    return : Fid Value pair from pcap
            
        Verify:
                 Have 1 C1 message, the changed fids' value is correct
                 If need to check all the Fids, all the Fid Value pair same with the defaultFidValue
                 
        Example:
                | ${defaultFidsValues}  |  get_FidValue_in_message  |  ${LOCAL_TMP_DIR}/capture_localDefault.pcap  |  ${DAS_DIR}  |  ${pubRic} | UPDATE
                 | ${defaultFidsValues}  |  get_FidValue_in_message  |  ${LOCAL_TMP_DIR}/capture_localDefault.pcap  |  ${DAS_DIR}  |  ${pubRic} | RESPONSE
                
        """ 
                
        outputfileprefix = 'updateCheckC1'
          
        if msgClass == 'RESPONSE' :
            filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_constitNum = &quot;1&quot;))'%(ricname)
        elif msgClass == 'UPDATE' :
            filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_UPDATE&quot;, Update_constitNum = &quot;1&quot;))'%(ricname)
        else:
            raise AssertionError('*ERROR* msgClass is not correct, please use UPDATE or RESPONSE' )
        
                       
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,outputfileprefix)
        
        parentName  = 'Message'
        messages = self._xml_parse_get_all_elements_by_name(outputxmlfilelist[0],parentName)        
        
        if (len(messages) == 1):            
            fidsAndValues = self._xml_parse_get_fidsAndValues_for_messageNode(messages[0])                
        else:
            raise AssertionError('*ERROR* No. of C1 message received not equal to 1 for RIC %s during icf insert, received (%d) message(s)'%(ricname,len(messages)))
        
        
        for delFile in outputxmlfilelist:
            os.remove(delFile)
            
        os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")  
        
        return fidsAndValues
                        
     
    def get_REAL_Fids_in_icf_file(self, srcfile, count = 1):
        """to Get some FIDs with outputFormat value TRWF_REAL_NOT_A_NUM 
         
        Argument:    
                srcfile : the icf file.\n
                count : the totol number of the Fids we want get
        
        return:
                Fidlist : some REAL type Fids' name list       
        Examples :
        
            |${FidList} | ${haveDefaultValue} | get REAL Fids in icf file  | C:\\temp\\extractFile.icf |  3   |    
        """
        dom = xml.dom.minidom.parse(srcfile)  
        root = dom.documentElement  
        iteratorlist = dom.getElementsByTagName('r')     
        Fidlist= []    
        fidCount = 0
                
        for node in iteratorlist:
            for subnode in node.childNodes:
                for ssubnode in subnode.childNodes:                    
                    if ssubnode.nodeType == node.ELEMENT_NODE and ssubnode.nodeName == 'it:outputFormat' and ssubnode.firstChild.data == 'TRWF_REAL_NOT_A_NUM':
                        tempList = subnode.nodeName.split(':') 
                        Fidlist.append(tempList[1])
                        fidCount = fidCount + 1
                        if fidCount >= count :
                            return Fidlist
        
        
        raise AssertionError('*ERROR* not enough REAL type Fids found in icf file %s'%(srcfile))   
        
        

    def modify_REAL_items_in_icf(self, srcfile, dstfile, ric, domain, fidsAndValues={}):   
        """to modify some REAL type items with FIDs and Value list in icf
                
        Argument:         
                    srcfile : the original icf file.\n
                    dstfile : the modified icf file
                    ric, domain
                    fidsAndValues: the Fid name and value dictionary need to be changed
         
        return nil
        """  
             
        index = 0
        itemList = []
        
        for (fid,value) in fidsAndValues.items():
            item = '<it:%s>\n <it:outputFormat>TRWF_REAL_NOT_A_NUM</it:outputFormat>\n <it:value>%s</it:value>\n</it:%s>'%(fid,value,fid)
            itemList.append(item)
        
        _FMUtil().modify_icf(srcfile, dstfile, ric, domain, *itemList)        
  