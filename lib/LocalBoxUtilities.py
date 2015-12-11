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
from LinuxToolUtilities import LinuxToolUtilities
from utils._ToolUtil import _ToolUtil
from sets import Set

FID_CONTEXTID = '5357'

class LocalBoxUtilities(_ToolUtil):
        
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()   
    
    linuxToolUtilInst = LinuxToolUtilities()

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
    
    def _xml_parse_get_PermissionInfo_for_messageNode (self,messageNode):
        """ get PE from <PermissionInfo> of header from a message node
            messageNode : iterator pointing to one message node
            return : PE value
            Assertion : <PermissionInfo> not found
        """
                            
        for fieldEntry in messageNode.getiterator('PermissionInfo'):
            pe = fieldEntry.find('PE')
            if (pe != None):                   
                return pe.attrib['value']

        raise AssertionError('*ERROR* Missing <PermissionInfo>')
        
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
        fidfilter = self.linuxToolUtilInst.get_contextId_fids_constit_from_fidfiltertxt(venuedir)
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
        fidfilter = self.linuxToolUtilInst.get_contextId_fids_constit_from_fidfiltertxt(venuedir)
        
        for outputxmlfile in outputxmlfilelist_1:
            self._verify_FIDfilter_FIDs_are_in_message_from_das_xml(outputxmlfile, fidfilter, ricsDict)
                
        #[ConstitNum = 0]
        #Convert pcap file to xml
        filterstring = 'AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_constitNum = &quot;0&quot;)'
        outputxmlfilelist_0 = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,'fidfilterVspcapC0',20)
        
        #Get the fidfilter
        fidfilter = self.linuxToolUtilInst.get_contextId_fids_constit_from_fidfiltertxt(venuedir)
        
        for outputxmlfile in outputxmlfilelist_0:
            self._verify_FIDfilter_FIDs_are_in_message_from_das_xml(outputxmlfile, fidfilter, ricsDict)        
        
        print '*INFO* %d Rics verified'%(len(ricsDict))
           
        for delFile in outputxmlfilelist_0:
            os.remove(delFile)
        os.remove(os.path.dirname(outputxmlfilelist_0[0]) + "/fidfilterVspcapC1xmlfromDAS.log")
            
        for delFile in outputxmlfilelist_1:
            os.remove(delFile)          
        os.remove(os.path.dirname(outputxmlfilelist_1[0]) + "/fidfilterVspcapC0xmlfromDAS.log")
    
    def verify_unsolicited_resp_for_ric_are_in_message(self,pcapfile,venuedir,dasdir,ricname):
        """ verify if unsolicited response for RIC has found in MTE output pcap message
            pcapFile : is the pcap fullpath at local control PC  
            venuedir : location from remote TD box for search FIDFilter.txt
            dasdir : location of DAS tool  
            ricname : target ric name    
            return : Nil
        """           
        #Check if pcap file exist
        if (os.path.exists(pcapfile) == False):
            raise AssertionError('*ERROR* %s is not found at local control PC' %pcapfile)                       
        
        #[ConstitNum = 1]
        #Convert pcap file to xml
        outputfileprefix = 'unsolpcap'
        filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, Response_responseTypeNum = &quot;TRWF_TRDM_RPT_UNSOLICITED_RESP&quot;)'%(ricname)
        outputxmlfilelist = self._get_extractorXml_from_pcap(dasdir,pcapfile,filterstring,outputfileprefix)
                
        for delFile in outputxmlfilelist:
            os.remove(delFile)
        
        os.remove(os.path.dirname(outputxmlfilelist[0]) + "/" + outputfileprefix + "xmlfromDAS.log")
                          
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
            headerPE = self._xml_parse_get_PermissionInfo_for_messageNode(messages[0])
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
        filterstring = 'AND(All_msgBase_msgKey_name = &quot;%s&quot;, AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_constitNum = &quot;1&quot;))'%(ricname)
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
            
            headerPE = self._xml_parse_get_PermissionInfo_for_messageNode(messages[0])
            if (headerPE != oldPE):
                raise AssertionError('*ERROR* 1st C1 message : Old PE in header (%s) not equal to (%s)'%(headerPE,oldPE))
            
            #2nd C1 message : C1 Response, new PE in header, all payload FIDs included
            dummyricDict = {}
            fidfilter = self.linuxToolUtilInst.get_contextId_fids_constit_from_fidfiltertxt(venuedir)   
            self._verify_FIDfilter_FIDs_in_single_message(messages[1],fidfilter, dummyricDict)    
            
            headerPE = self._xml_parse_get_PermissionInfo_for_messageNode(messages[1])
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
        fidfilter = self.linuxToolUtilInst.get_contextId_fids_constit_from_fidfiltertxt(venuedir)
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
            
            headerPE = self._xml_parse_get_PermissionInfo_for_messageNode(messages[0])
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
           
    def get_EXL_files(self,fmsDir,fileType):
        """ Get EXL file(s) for fileType:
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1687

            fileType options: ['Closing Run', 'DST', 'Feed Time', 'Holiday', 'OTFC', 'Trade Time', 'All']
            
            return : List containing full directory path and name of EXL file(s), if found. 
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
        
    def get_EXL_file_from_domain(self, fmsDir, domain):
        """ Get EXL file(s) for fileType:
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1795
            Argument: 
                fmsDir: The Location of the FMS on the local machine
                domain: The market domain ['MARKET_PRICE', 'MARKET_BY_ORDER', 'MARKET_BY_ORDER']
            
            return : Full file path and name of an EXL file containing at least one RIC with the given domain 
        """ 
        exlFiles = self.get_EXL_files(fmsDir, "All")

        for exlFile in exlFiles:
            # Open up the source EXL file with an XML parser
            xmlParser = None
            try:
                xmlParser = xml.dom.minidom.parse(exlFile)  
            except Exception, exception:
                raise AssertionError('XML DOM parser failed to open EXL file %s Exception: %s' % (exlFile, exception))
                return 1
    
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
    
            # Get the exlObjects section of the data.  This is where the RIC definitions 
            # are.  If this section doesn't exist in the given EXL file thats an error.
            exlObjectNode = xmlParser.getElementsByTagName('exlObjects') 
            if(len(exlObjectNode) == 0):
                continue

            # Get the exlObjects withing the exlObjects tag and make sure at least 
            # one RIC definition exists.  There will be only one exlObjects tag so its
            # okay to only look at array index 0.
            ricNodes = exlObjectNode[0].getElementsByTagName('exlObject')
            if(len(ricNodes) == 0):
                continue
    
            # The XML parser treats the value of a tag as a child node of that tag.  To get 
            # the actual value you must call the "nodeValue" method on that child node.  As shown
            # above in our EXL file example we expect a single "it:DOMAIN" tag with a single value.
            for ricNode in ricNodes:
                ricNodeDomainTag = ricNode.getElementsByTagName("it:DOMAIN")  
                if(len(ricNodeDomainTag) != 1): # We always expect one it:DOMAIN tag
                    continue
                if(len(ricNodeDomainTag[0].childNodes) != 1):  # We always expect one it:DOMAIN value
                    continue
                valueNode = ricNodeDomainTag[0].childNodes[0]  # Get the value of the it:DOMAIN tag
                if(valueNode.nodeValue == domain):
                    return exlFile

        raise AssertionError('*ERROR* Failed to find any EXL files in %s with data for domain %s' % (fmsdir, domain))
        
    def get_EXL_from_RIC_and_domain(self,ricName,domainName,fmsDir,fileType):
        """ Get EXL file from given RIC and domain pair:
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1737

            fileType options: ['Closing Run', 'DST', 'Feed Time', 'Holiday', 'OTFC', 'Trade Time', 'All']
            
            return : Full directory path and name of EXL file, if found. 
                     If multiple files or none found, will raise an error.
        """ 
        
        exlFiles = self.get_EXL_files(fmsDir, fileType)
        
        matchedExlFiles = []
        
        for exlFile in exlFiles:
            dom = xml.dom.minidom.parse(exlFile)  
            iteratorlist = dom.getElementsByTagName('exlObject') 
            
            #find the ric and domain
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
    
    def get_ric_and_domain_from_EXL(self,exlFile):
        """ Get RIC and domain from EXL
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1733

            return : First discovered RIC and domain pair in EXL file, if found. Otherwise, returns 'Not Found'.
        """ 
        
        dom = xml.dom.minidom.parse(exlFile)  
        iteratorlist = dom.getElementsByTagName('exlObject') 
        
        #find the ric and domain
        for node in iteratorlist:
            ric = "Not Found"
            domain = "Not Found"
            for subnode in node.childNodes:
                if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:RIC':
                    ric = subnode.firstChild.data
                if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:DOMAIN':
                    domain = subnode.firstChild.data
            if ric != "Not Found" and domain != "Not Found":
                break

        if ric == "Not Found" or domain == "Not Found":
            raise AssertionError('*ERROR* Missing RIC/domain pair: RIC(%s), domain(%s)' %(ric, domain))
            
        return ric, domain
    
    def get_DST_and_holiday_RICs_from_EXL(self,exlFile):
        """ Get DST RIC and holiday RIC from EXL
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1735

            return : DST RIC and holiday RIC, if found. Otherwise, returns 'Not Found'.
        """ 
        
        dom = xml.dom.minidom.parse(exlFile)  
        iteratorlist = dom.getElementsByTagName('exlHeaderFields') 
        
        #find the RICs
        for node in iteratorlist:
            dstRic = "Not Found"
            holidayRic = "Not Found"
            for subnode in node.childNodes:
                if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:DST_REF':
                    dstRic = subnode.firstChild.data
                if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:HOLIDAYS_REF1':
                    holidayRic = subnode.firstChild.data

        if dstRic == "Not Found" or holidayRic == "Not Found":
            raise AssertionError('*ERROR* Missing DST and holiday RICs from EXL: %s' %(exlFile))
            
        return dstRic, holidayRic
    
    def get_ric_fields_from_EXL(self,exlFile,ricName,*fieldnames):
        """ Get field values of RIC from EXL
           Argument:
               exlFile : full path of exlfile			   
               ricName : ric 
			   fieldnames : list of fields want to retrieve
           Return : list of value corresponding to fieldnames
           Example:
                get ric fields from EXL |C:\\config\\DataFiles\\Groups\\RAM\\MFDS\\MUT\\EXL Files\\nasmf_a.exl|AAAAX.O|PROD_PERM|
           
        """
         
        retList = []
        heanderDict = self._get_exlHeaderField_value_from_EXL(exlFile,fieldnames)        
        ObjDict = self._get_exlObject_field_value_of_ric_from_EXL(exlFile,ricName,fieldnames)
        
        for fieldname in fieldnames:
            if (ObjDict[fieldname] != "NOT Found"):
                retList.append(ObjDict[fieldname])
            elif (heanderDict[fieldname] != "NOT Found"):
                retList.append(heanderDict[fieldname])
            else:
                raise AssertionError('*ERROR* %s not found for RIC(%s) in %s' %(fieldname, ricName, exlFile))

        return retList
         
    def _get_exlHeaderField_value_from_EXL(self,exlFile,fieldnames):
        """ Get field value(s) from EXL exlHeaderField
            Argument:
                fieldnames : list of fields name
           Return : Dictionary with key = item found in fieldnames list
           [Remark] WE don't raise assertion for field not found case, as for some case we just want to check if field is exist
        """ 
        
        dom = xml.dom.minidom.parse(exlFile)  
        iteratorlist = dom.getElementsByTagName('exlHeaderFields')
        
        #find the field
        fieldValues = {}
        for fieldname in fieldnames:
            fieldValues[fieldname] = "NOT Found"
            
        for node in iteratorlist:
            for subnode in node.childNodes:
                for fieldname in fieldnames:
                    if (subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:'+fieldname):               
                        fieldValues[fieldname] = subnode.firstChild.data
                    
        return fieldValues 
    
    def _get_exlObject_field_value_of_ric_from_EXL(self,exlFile,ricName,fieldnames):
        """ Get field value(s) from EXL exlObject given the ricname
            Argument:
                ricName : ric name
                fieldnames : list of fields name
            Return : Dictionary with key = item found in fieldnames list
           [Remark] WE don't raise assertion for field not found case, as for some case we just want to check if field is exist
        """ 
        
        dom = xml.dom.minidom.parse(exlFile)  
        iteratorlist = dom.getElementsByTagName('exlObject') 
        
        #find the ric and field
        fieldValues = {}            
        for node in iteratorlist:
            for fieldname in fieldnames:
                fieldValues[fieldname] = "NOT Found"
            
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
                
        if (ric == ""):
            raise AssertionError('*ERROR* RIC(%s) not found in %s' %(ricName, exlFile))
                        
        return fieldValues      
       
    def get_all_data_from_cachedump(self, cachedump_file_name):
        """Returns a dictionary with key = 1st row found in cachdump csv file and each key corresponding a list of data
         Argument : 
         cachedump_file_name : cache dump file full path
         
         Keys found in cacheddump are :
         
         ITEM_ID,RIC,DOMAIN,TYPE,SIC,PUBLISH_KEY,CONTEXT_ID,STALE,PUBLISHABLE,CURR_SEQ_NUM,OTF_STATUS,
         C++_TYPE,TIME_CREATED,LAST_ACTIVITY,LAST_UPDATED,DELETION_DELAY_DAYS_REMAINING,RIC_LOOKUP_STATUS,
         SIC_LOOKUP_STATUS,MANGLING_RULE,NON_PUBLISHABLE_REASONS,THREAD_ID,ITEM_FAMILY

        Examples:
        | get all data from cachedump | cachedump file name |     
        """
        if not os.path.exists(cachedump_file_name):
            raise AssertionError('*ERROR*  %s is not available' %cachedump_file_name)
        
        dataMap = {}
        
        n = 0
        try:
            with open(cachedump_file_name) as fileobj:
                for line in fileobj:
                    n = n+1
                    if n == 1:
                        keys = line.strip("\n").split(",")
                        for key in keys:
                            dataMap[key] = list([])
                    if n>1:
                        records = line.strip("\n").split(",")
                        idx = 0
                        for record in records:
                            dataMap[keys[idx]].append(record)
                            idx = idx + 1
                            
        except IOError:
            raise AssertionError('*ERROR* failed to open file %s' %cachedump_file_name)
                            
        return dataMap      
    
    def get_ric_names_from_cachedump(self, cachedump_file_name, no_ric=1, domain='MarketPrice'):
        """Returns a list of rics given domain and no. of sample is required
         Argument : 
         cachedump_file_name : cache dump file full path
         num_ric : expected number of ric names
         domain : either MarketPrice, MarketByPrice, MarketByOrder         

        Examples:
        | get ric names from cachedump | cachedump file name | 10
        """
        
        dataMap = self.get_all_data_from_cachedump(cachedump_file_name)
        domainKey = 'DOMAIN'
        ricKey = 'RIC'
        publishableKey = 'PUBLISHABLE'
        out_rics_list = []
        
        if (len(dataMap) > 0):
            if (len(dataMap[domainKey]) > 0):
                if (len(dataMap[ricKey]) > 0):
                    if (len(dataMap[publishableKey]) > 0):
                        domain_list = dataMap[domainKey]
                        rics_list = dataMap[ricKey]
                        publishablekey_list = dataMap[publishableKey]
                        
                        idx = 0
                        for ric in rics_list:
                            if (domain_list[idx] == domain and publishablekey_list[idx] == 'TRUE'):
                                out_rics_list.append(ric)
                            
                            if (len(out_rics_list) >= int(no_ric)):
                                break
                            
                            idx = idx + 1
                            
                    else:
                        raise AssertionError('*ERROR*  %s data is missing in %s' %(publishableKey,cachedump_file_name))                         
                else:
                    raise AssertionError('*ERROR*  %s data is missing in %s' %(ricKey,cachedump_file_name))                  
            else:
                raise AssertionError('*ERROR*  %s data is missing in %s' %(domainKey,cachedump_file_name))  
        else:
            raise AssertionError('*ERROR* No data found in %s' %cachedump_file_name)
        
        
        if (len(out_rics_list) == 0):
            raise AssertionError('*ERROR* No Ric found for domain %s in %s' %(domain, cachedump_file_name))
        
        if (len(out_rics_list) < int(no_ric)):
            raise AssertionError('*ERROR* Number of Ric found (%d) for %s domain in %s is less than required (%s)' %(len(out_rics_list), domain, cachedump_file_name, no_ric))
        
        return out_rics_list

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
        constituNumSet = Set();
        for atype in treeRoot.findall('.//FieldID'):
            val_result = atype.get('value')
            constituNumSet.add(val_result)
        
        return constituNumSet         

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
    
    def get_first_ric_for_domain_from_exl(self, domain, fms_dir):
        """Find first non-state-ric with specified domain from exl files located at LOCAL_FMS_DIR and its sub-directories
         Returns : [ric name, fms service name, full path file name of Exl]
         example of result list
         ['AAAAX.O',  'MFDS', 'D:\tools\FMSCMD\config\DataFiles\Groups\RAM\MFDS\EXL Files\nasmf_a.exl']
         Argument : 
            domain : either MARKET_PRICE,MARKET_BY_PRICE,MARKET_BY_ORDER
        """ 
                        
        list_of_state_ric_exl = ['_cs_run', '_dl_sav', '_fd_time', '_mk_holiday', '_otfc','_trd_time', '_venue_heartbeat']
        filestr = '*.exl'
        
        for root, dirnames, filenames in os.walk(fms_dir):
            for filename in fnmatch.filter(filenames, filestr):
                if not self._list_item_is_substring_of_searched_item(filename, list_of_state_ric_exl):
                    dict = self.get_first_ric_domain_service_from_exl(os.path.join(root, filename))
                    if (dict['DOMAIN'] == domain):
                        return dict['RIC'], dict['SERVICE'], os.path.join(root, filename)
                
        raise AssertionError('*ERROR* non-state-ric for domain %s not found in directory %s and its sub-directories' %(domain,fms_dir))       
    
    def get_first_ric_domain_service_from_exl(self, non_state_ric_exl_file):
        """Get first occurrence of service name, RIC and domain in exl file
         Returns a dictionary contains service, RIC and domain information
         example of result {'DOMAIN' : 'MARKET_PRICE', 'RIC' : 'AAAAX.O', 'SERVICE' : 'MFDS'}
         Argument : full path name to exl file 
        """ 
        
        if not non_state_ric_exl_file:
            raise AssertionError('*ERROR* non-state-ric exl file name %s is invalid' %non_state_ric_exl_file)
        
        if not os.path.exists(non_state_ric_exl_file):
            raise AssertionError('*ERROR*  %s is not available' %non_state_ric_exl_file)
        
        dict1 = {}
        doc = xml.dom.minidom.parse(non_state_ric_exl_file)
        tag = 'it:SERVICE'
        dict1['SERVICE'] = self._find_first_node_data(non_state_ric_exl_file, doc, tag) 
        
        tag = 'it:RIC'
        dict1['RIC'] = self._find_first_node_data(non_state_ric_exl_file, doc, tag) 
        
        tag = 'it:DOMAIN'
        dict1['DOMAIN'] = self._find_first_node_data(non_state_ric_exl_file, doc, tag) 
                
        if len(dict1)!=3:
            raise AssertionError('*ERROR* could not get DOMAIN, RIC, SERVICE information from exl file %s' %non_state_ric_exl_file)
        
        return  dict1 
               
    def _find_first_node_data(self, exl_file, doc, tag):
        """Get first occurrence of node data by given the node tag and dom parsed doc   
        """ 
        nodelist = doc.getElementsByTagName(tag)
        if len(nodelist)<1:
            raise AssertionError('*ERROR* could not get %s nodes from exl file %s' %(tag, exl_file))
            
        name = ''    
        for node in nodelist:
            name = node.firstChild.data
            break
            
        if not name:
            raise AssertionError('*ERROR* invalid first node %s data in node %s from exl file %s' %(name, tag, exl_file))    
        return name
                
    def find_first_non_state_ric_exl_file(self, fms_dir, list_of_state_ric_exl):
        """Find first non-state-ric exl file from LOCAL_FMS_DIR and its sub-directories
         Returns a list contains filename, file path, full path file name
         example of result list
         ['nasmf_a.exl', 
         'D:\tools\FMSCMD\config\DataFiles\Groups\RAM\MFDS\EXL Files\', 
         'D:\tools\FMSCMD\config\DataFiles\Groups\RAM\MFDS\EXL Files\nasmf_a.exl']
         Argument : fms file directory and list contains state ric exl file name keyword ['_cs_run', '_dl_sav', '_fd_time', '_mk_holiday', '_otfc','_trd_time', '_venue_heartbeat']
        """ 
        filestr = '*.exl'
        find_file_list = []
        for root, dirnames, filenames in os.walk(fms_dir):
            for filename in fnmatch.filter(filenames, filestr):
                if not self._list_item_is_substring_of_searched_item(filename, list_of_state_ric_exl):
                    find_file_list.append(filename)
                    find_file_list.append(root)
                    find_file_list.append(os.path.join(root, filename))
                    return find_file_list
            
        raise AssertionError('*ERROR* non-state-ric exl file could not be found in directory %s and its sub-directories' %fms_dir)
                         
    def _list_item_is_substring_of_searched_item(self, search_str, list_of_state_ric_exl):
        """check if list item is substring of the search_str
        Return True if find matched item.
        """
        
        for x in list_of_state_ric_exl:
            if re.search(x, search_str):
                return True
            
        return False

    def verify_ric_in_cachedump(self, cachedump_file_name, long_ric):
        """verify ric in cachedump file
        Returns True if long ric exists in file.
        Argument : cache dump file, long ric    
        """ 
        if not os.path.exists(cachedump_file_name):
            raise AssertionError('*ERROR*  %s is not available' %cachedump_file_name)
        
        try:
            with open(cachedump_file_name) as fileobj:
                for line in fileobj:
                    if long_ric in line:
                        return True
        except IOError:
            raise AssertionError('*ERROR* failed to open file %s' %cachedump_file_name)
        
                
        raise AssertionError('*ERROR* RIC %s cannot be found in cachedump file %s' %(long_ric,cachedump_file_name))
             
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
        
        filterstring_context_id_set = self._get_context_ids_from_fms_filter_string(filter_string)
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
    
    def _get_context_ids_from_fms_filter_string(self, fms_filter_string): 
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
    
    def get_MTE_config_list(self,venueConfigFile,*xmlPath):
        """ Gets value(s) from venue config file
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1798
            
            params : venueConfigFile - full path to local copy of venue configuration file
                     xmlPath - one or more node names that identify the XML path

            return : list containing value(s) of given xmlPath, if found. Otherwise, returns "NOT FOUND" if nothing found.
            
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
            return "NOT FOUND"
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
