import os
import os.path

from trwf2messages import trwf2messages
from LinuxToolUtilities import LinuxToolUtilities
from utils.version import get_version

FID_CONTEXTID = '5357'

class fidfilter():
    
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()
    
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
    
    def _verify_fid_in_fidfilter_by_contextId_and_constit_against_pcap_msgType(self,pcapfile,fidfilter,contextId,constit,msgType='Response'):
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
                   
        outputxmlfile = trwf2messages().get_extractorXml_from_pcap(pcapfile, filterstring, 'pcapVsfidfilter')
        
        self._verify_fid_in_fidfilter_by_contextId_against_das_xml(outputxmlfile[0],fidfilter,contextId,constit)  
        os.remove(outputxmlfile)
            
    def verify_fid_in_fidfilter_by_contextId_and_constit_against_pcap(self,pcapfile,contextId,constit):
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
        fidfilter = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt()
        if (fidfilter.has_key(contextId) == False):
            raise AssertionError('*ERROR* required context ID %s not found in FIDFilter.txt '%contextId)
        elif ((fidfilter[contextId].has_key(constit) == False)):
            raise AssertionError('*ERROR* required constituent %s not found in FIDFilter.txt '%constit)          
                
        #For Response
        self._verify_fid_in_fidfilter_by_contextId_and_constit_against_pcap_msgType(pcapfile,fidfilter,contextId,constit,'Response')
        
        #For Update
        self._verify_fid_in_fidfilter_by_contextId_and_constit_against_pcap_msgType(pcapfile,fidfilter,contextId,constit,'Update')  
    
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
    
    def _verify_fid_in_range_by_constit_against_pcap_msgType(self,pcapfile,fid_range,constit,msgType='Response'):
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
        
        outputxmlfile = trwf2messages().get_extractorXml_from_pcap(pcapfile,filterstring,'pcapVsfidrange')
        
        self._verify_fid_in_range_against_das_xml(outputxmlfile[0],fid_range)
        os.remove(outputxmlfile)
                      
    def verify_fid_in_range_by_constit_against_pcap(self,pcapfile,constit,fid_range=[-36768,32767]):
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
        self._verify_fid_in_range_by_constit_against_pcap_msgType(pcapfile,fid_range,constit)
        
        #Checking Update
        self._verify_fid_in_range_by_constit_against_pcap_msgType(pcapfile,fid_range,constit,'Update')
    
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
               
    def verify_FIDfilter_FIDs_are_in_message(self,pcapfile):
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
        outputxmlfilelist_1 = trwf2messages().get_extractorXml_from_pcap(pcapfile,filterstring,'fidfilterVspcapC1',20)
        
        #Get the fidfilter
        fidfilter = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt()
        
        for outputxmlfile in outputxmlfilelist_1:
            self._verify_FIDfilter_FIDs_are_in_message_from_das_xml(outputxmlfile, fidfilter, ricsDict)
                
        #[ConstitNum = 0]
        #Convert pcap file to xml
        filterstring = 'AND(All_msgBase_msgClass = &quot;TRWF_MSG_MC_RESPONSE&quot;, Response_constitNum = &quot;0&quot;)'
        outputxmlfilelist_0 = trwf2messages().get_extractorXml_from_pcap(pcapfile,filterstring,'fidfilterVspcapC0',20)
        
        #Get the fidfilter
        fidfilter = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt()
        
        for outputxmlfile in outputxmlfilelist_0:
            self._verify_FIDfilter_FIDs_are_in_message_from_das_xml(outputxmlfile, fidfilter, ricsDict)        
        
        print '*INFO* %d Rics verified'%(len(ricsDict))
           
        for delFile in outputxmlfilelist_0:
            os.remove(delFile)
        os.remove(os.path.dirname(outputxmlfilelist_0[0]) + "/fidfilterVspcapC1xmlfromDAS.log")
            
        for delFile in outputxmlfilelist_1:
            os.remove(delFile)          
        os.remove(os.path.dirname(outputxmlfilelist_1[0]) + "/fidfilterVspcapC0xmlfromDAS.log")
    
    
    def verify_message_fids_are_in_FIDfilter(self, localPcap, ric, domain, contextId):
        '''
         verify that message's fids set from pcap for the ric, with domain, contextId is the subset of the fids set defined in FidFilter file for a particular constituent under the context id
        '''
        constituents = self.get_constituents_from_FidFilter(contextId)
        for constituent in constituents:
            # create fidfilter fids set under contextId and constituent
            contextIdMap = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt()
            constitWithFIDs = contextIdMap[contextId]
            fidsdict = constitWithFIDs[constituent]
            fidsList = fidsdict.keys()
            filterFilefidsSet = frozenset(fidsList);
            
            # create filter string for each constituent to get the message fids set
            filterDomain = 'TRWF_TRDM_DMT_'+ domain
            filterstring = 'AND(All_msgBase_msgKey_domainType = &quot;%s&quot;, AND(All_msgBase_msgKey_name = &quot;%s&quot;, Response_constitNum = &quot;%s&quot;))'%(filterDomain, ric, constituent)
            outputfile = trwf2messages().get_extractorXml_from_pcap(localPcap, filterstring, "out1")
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
            
            
            
    def get_constituents_from_FidFilter(self, context_id):
        """ 
            Return : constituent list which contains unique constituents defined in venue FidFilter.txt file for the context_id
        """ 
        fidfilter = LinuxToolUtilities().get_contextId_fids_constit_from_fidfiltertxt()
        if (fidfilter.has_key(context_id) == False):
            raise AssertionError('*ERROR* Context ID %s does not exist in FIDFilter.txt file' %(context_id))  
        
        fidDic = fidfilter[context_id]
        if len(fidDic.keys()) == 0:
            raise AssertionError('*ERROR* No FID dictionary exists in FIDFilter.txt file for Context ID %s' %(context_id))  
        
        return fidDic.keys()
    
    def verify_no_realtime_update_type_in_capture(self, pcapfile, domain):
        """ Verify update message does not exist for MARKET PRICE, or MARKET_BY_ORDER or MARKET_BY_PRICE domain.
            Argument : pcapfile : MTE output pcap file fullpath
                       domain : in format like MARKET_PRICE, MARKET_BY_PRICE, MARKET_BY_ORDER
            return : Nil
        """  
        try:
            self.verify_updated_message_exist_in_capture(pcapfile, domain)     
        except AssertionError:
            return
               
        raise AssertionError('*ERROR* realtime updates exist for domain %s.' %domain)
    