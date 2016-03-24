'''
Created on May 12, 2014

@author: xiaoqin.li
'''
from __future__ import with_statement
import codecs
import os
import os.path
import re
from subprocess import Popen, PIPE
import xml
from xml.dom import minidom

from utils.local import _run_local_command
from utils.rc import _rc
from utils.version import get_version
from VenueVariables import *

class fms_exl():
    """A test library providing keywords for handling FMS operations and handling exl, icf, lxl files, or other FMS related things.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()
    
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
            fileHandle.write(xmlParser.toxml("utf-8"))
            fileHandle.close()
        except Exception, exception:
            raise AssertionError('Failed to open EXL target file %s Exception: %s' % (exlFileTarget, exception))
            return 5

        return 
    
    def keep_specified_exlobject(self, exlfilefullpath, RIC, Domain, outputfile):
        """keep the specified ric,domain exl object and remove all other exl objects.

        exlfilefullpath is the exl absolute path on local machine.\n
        RIC is the ric name in exl. Domain is the domain name.\n
        
        Return the modified exl path.

        Examples:
        | ${result} = | keep specified exlobject | c:/temp/test.exl | CB.N | MARKET_PRICE | C:/TEMP/tmp.exl |
        """
        keep=True
        return self._remove_exlobject(exlfilefullpath, RIC, Domain, keep, outputfile)
    
    def remove_specified_exlobject(self, exlfilefullpath, RIC, Domain, outputfile):
        """remove the specified exl object and keep all other exl objects.

        exlfilefullpath is the exl absolute path on local machine.\n
        RIC is the ric name in exl. Domain is the domain name.\n
        
        Return the modified exl path.

        Examples:
        | ${result} = | remove specified exlobject | c:/temp/test.exl | CB.N | MARKET_PRICE | C:/TEMP/tmp.exl |
        """
        keep=False
        return self._remove_exlobject(exlfilefullpath, RIC, Domain, keep, outputfile)

    def _remove_exlobject(self, exlfilefullpath, RIC, Domain,keep, outputfile):
        if os.path.abspath(exlfilefullpath) == os.path.abspath(outputfile):
            outputfile= os.path.abspath(os.path.dirname(outputfile)) +'\\' + 'GATS_' +os.path.basename(outputfile)
        try:

            with codecs.open(exlfilefullpath, 'r', 'utf-8') as exlfile:
                with codecs.open(outputfile, 'w', 'utf-8') as exlnewfile:
                    exlline = exlfile.readline()
                    objfind = False
                    Ricfind = False
                    Domainfind = False
                    exlobjlist = []
                    while exlline:
                        if objfind:
                            exlobjlist.append(exlline)
                            if exlline.find('</exlObject>') != -1:
                                objfind = False
                                if Domainfind and Ricfind:
                                    if not keep:
                                        exlobjlist = []
                                        Domainfind = False
                                        Ricfind = False
                                        exlline = exlfile.readline()
                                        continue
                                    else:
                                        Domainfind = False
                                        Ricfind = False
                                        exlnewfile.writelines(exlobjlist)
                                        exlobjlist = []
                                else:
                                    if not keep:
                                        Domainfind = False
                                        Ricfind = False
                                        exlnewfile.writelines(exlobjlist)
                                        exlobjlist = []
                                    else:
                                        exlobjlist = []
                                        Domainfind = False
                                        Ricfind = False
                                        exlline = exlfile.readline()
                                        continue        

                            elif exlline.find('<it:RIC>%s</it:RIC>' % RIC) != -1:
                                Ricfind = True
                            elif exlline.find('<it:DOMAIN>%s</it:DOMAIN>' % Domain) != -1:
                                Domainfind = True
                        else:
                            if exlline.find('<exlObject>') != -1:
                                exlobjlist.append(exlline)
                                objfind = True
                            else:
                                exlnewfile.write(exlline)
                        exlline = exlfile.readline()

        except IOError,e:
            raise AssertionError('*ERROR* %s' %e)
        
        return outputfile
    
    def modify_icf(self, srcfile, dstfile, ric, domain, *ModifyItem):
        """modify icf file for assigned ric and domain item.
        
        srcfile is the original file.\n
        dstfile is the modified output file.\n
        ModifyItem can be one or more items, and it supports one or multiple layers.
        For example: <it:DSPLY_NAME>xiaoqin</it:DSPLY_NAME>, <it:SCHEDULE_MON>\n<it:TIME>00:00:00</it:TIME>\n</it:SCHEDULE_MON>.
        In above example, mean change DSPLY_NAME to xiaoqin, and change SCHEDULE_MON to 00:00:00.\n
        
        Return the modified output file path.

        Examples:
        | ${result} | modify icf | c:/temp/ACLJ.icf | c:/temp/output.icf | ACLJ.JO | MARKET_PRICE | <it:EXCHANGE>test</it:EXCHANGE> | <it:TRDPRC_1>\\n         <it:outputFormat>TRWF_REAL_NOT_A_NUM</it:outputFormat>\\n         <it:value>20</it:value>\\n      </it:TRDPRC_1> |
        =>\n
        * change EXCHANGE's value to test and TRDPRC_1's value to 20\n
        """
        return self._modify_fm_file(srcfile, dstfile, 'r', ric, domain, *ModifyItem)
    
    def modify_exl(self, srcfile, dstfile, ric, domain, *ModifyItem):
        """modify exl file for assigned ric and domain item.
        if the modified item can't be found, then add it.
        
        srcfile is the original file.\n
        dstfile is the modified output file.\n
        ModifyItem can be one or more items, and it supports one or multiple layers.
        For example: <it:DSPLY_NAME>xiaoqin</it:DSPLY_NAME>, <it:SCHEDULE_MON>\n<it:TIME>00:00:00</it:TIME>\n</it:SCHEDULE_MON>.
        In above example, mean change DSPLY_NAME to xiaoqin, and change SCHEDULE_MON to 00:00:00.\n
        
        Return the modified output file path.

        Examples:
        | ${result} | modify exl |c:/temp/ACLJ.exl | c:/temp/output.exl | ACLJ.JO | MARKET_PRICE | <it:DSPLY_NAME>xiaoqin</it:DSPLY_NAME> | 
        """
        return self._modify_fm_file(srcfile, dstfile, 'exlObject', ric, domain, *ModifyItem)
    
    def modify_exl_header(self, srcfile, dstfile, *ModifyItem):
        """modify exl file header.
        
        srcfile is the original file.\n
        dstfile is the modified output file.\n
        ModifyItem can be one or more items, and it supports one or multiple layers.
        For example: <it:DSPLY_NAME>xiaoqin</it:DSPLY_NAME>, <it:SCHEDULE_MON>\n<it:TIME>00:00:00</it:TIME>\n</it:SCHEDULE_MON>.
        In above example, mean change DSPLY_NAME to xiaoqin, and change SCHEDULE_MON to 00:00:00.\n
        
        Return the modified output file path.

        Examples:
        | ${result} | modify exl header |c:/temp/ACLJ.exl | c:/temp/output.exl | <it:EXCHANGE>MP</it:EXCHANGE> | <it:ENABLED>true</it:ENABLED> |
        """
        return self._modify_fm_file(srcfile, dstfile, 'exlHeader', '', '', *ModifyItem)
    
               
    def _modify_fm_file(self, srcfile, dstfile, modifyType, ric, domain, *ModifyItem):
        '''modifyType: exlObject, exlHeader, r'''

        dom = xml.dom.minidom.parse(srcfile)  
        root = dom.documentElement  
        iteratorlist = dom.getElementsByTagName(modifyType) 
        
        if modifyType != 'exlHeader':
            #find the ric and domain parent node
            if domain.lower() == 'shellric' or domain.lower() == 'll2':
                domain = 'MARKET_PRICE'
            findric = False
            finddomain = False
            for node in iteratorlist:
                for subnode in node.childNodes:
                    if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:RIC':
                        if subnode.firstChild.data == ric:
                            findric = True
                    if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:DOMAIN':
                        if subnode.firstChild.data == domain:
                            finddomain = True
                if findric and finddomain:
                    iteratoroot = node
                    break
            if findric == False or finddomain == False:
                raise AssertionError("*ERROR* not found %s and %s in the exl" % (ric, domain))
            
        else:
            iteratoroot = iteratorlist[0]
        
        def setvalue(node, field, value, replnodeflag):
            index= 0
            for subnode in node.childNodes:
                index = index +1
                if subnode.nodeType == node.ELEMENT_NODE:
                    if subnode.nodeName == field:
                        if replnodeflag == False:
                            subnode.firstChild.data = value
                            return True
                        else:
                            value.removeAttribute('xmlns:it')
                            node.replaceChild(value,subnode)                     
                            return True  
       
                    else:
                        result = setvalue(subnode, field, value, replnodeflag)
                        if result == True:
                            return True
            return False     
        
        pat = re.compile('<(.*?)>(.*)</.*?>', re.DOTALL)
        for mitem in ModifyItem:
            modifyflag = False
            match = pat.search(mitem)
            if match:
                field = match.group(1)
                value = match.group(2)
                tempdom = xml.dom.minidom.parseString('<%s xmlns:it="DbFieldsSchema">'%field +value + '</%s>'%field)  
                tempnode = tempdom.documentElement
                if pat.search(value):
                    # multiple layers
                    modifyflag = setvalue(iteratoroot, field, tempnode, True)
                    #print iteratoroot.childNodes.item(11).childNodes.item(1).childNodes
                else:
                    modifyflag = setvalue(iteratoroot, field, value, False)
                if modifyflag == False:
                    #raise AssertionError("*ERROR* not found field %s for %s and %s in exl" % (field, ric, domain))
                    print '*INFO* requested field %s does not exist, adding new field'%field
                    note = iteratoroot.getElementsByTagName('exlObjectFields')   
                    tempnode.removeAttribute('xmlns:it')
                    note[0].appendChild(tempnode)
            else:
                raise AssertionError("*ERROR* the format of modified item is incorrect")
        
        with codecs.open(dstfile,'w','utf-8') as out:
            dom.writexml(out,addindent='',newl='',encoding='utf-8')
        
        return dstfile
    
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
    
    def run_FmsCmd (self, headendIP, TaskType, *optargs):
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
        res = self._check_fmscmd_log(stdout)
        return [res, stdout, cmd]
    
    def _get_EXL_files(self,fileType):
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
        
        cmdstr = 'cmd /c dir /S /B \"' + LOCAL_FMS_DIR + '\"\\' +  searchFileString
        print '*INFO* cmdstr: %s' %cmdstr
        p = Popen(cmdstr, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
        exlFiles = p.stdout.read().strip().split(os.linesep)
        if len(exlFiles) < 1 or exlFiles[0].lower() == "file not found" or exlFiles[0] == '':
            raise AssertionError('*ERROR* Search returned no results for: %s' %cmdstr)
        return exlFiles      
    
    def get_state_EXL_file(self,ricName,domainName,service,fileType):
        """ Get EXL file from given RIC, domain, and service:
            http://www.iajira.amers.ime.reuters.com/browse/CATF-1737

            fileType options: ['Closing Run', 'DST', 'Feed Time', 'Holiday', 'OTFC', 'Trade Time', 'All']
            
            return : Full path name of EXL file, if found. 
                     If multiple files or none found, will raise an error.
        """ 
        
        exlFiles = self._get_EXL_files(fileType)
        
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
    
    def get_EXL_for_RIC(self, domain, service, ric):
        """ Find the EXL file with the specified RIC, domain, and service
            
            Argument: 
                domain:  The market domain ['MARKET_PRICE', 'MARKET_BY_ORDER', 'MARKET_BY_ORDER']
                service: The service name
                ricName:  The RIC to find
            
            return : Full EXL file path name
        """ 
        
        exlFiles = self._get_EXL_files("All")
        
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
                        if fidCount >= int (count) :
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
        
        self.modify_icf(srcfile, dstfile, ric, domain, *itemList)        
  


    def get_exl_file_path_for_lxl_file(self, exl_path): 
        """Deriving exl path for lxl file from exl full file path
                 
        Argument:    
                    exl_path : the exl file path no name.\n     
 
        return:
                    exl directory required by lxl file without file name
                    Example:
                    LOCAL_FMS_DIR  is D:\\tools\\FMSCMD\\config\\DataFiles\\Groups
                    if exl_path D:\\tools\\FMSCMD\\config\\DataFiles\\Groups\\RAM\\MFDS\\EXL Files
                    return empty path 
                    if exl_file D:\\tools\\FMSCMD\\config\\DataFiles\\Groups\\RAM\\MFDS\\MUT\\EXL Files
                    return path RAM/MFDS/MUT/
        """  
            
        new_path = exl_path.replace(LOCAL_FMS_DIR + "\\",'').replace('EXL Files','')
        nodes = new_path.split("\\")   
        nodes = filter(None, nodes)
         
        if len(nodes)<2:
            raise AssertionError('*ERROR* Cannot determine LXL path based on FMS dir [%s] and EXL path [%s]' %(LOCAL_FMS_DIR, exl_path))
         
        if len(nodes)==2:
            return ''
        else:
            new_path = new_path.replace('\\','/')
            
        return new_path
        
            
    def build_LXL_file (self, exl_path_in_lxl, file_list):  
        '''
        Argument:    
                    exl_path_in_lxl : exl path get from by calling get_exl_file_path_for_lxl_file
                    file_list : the exl file name list (without full path).\n
        return: 
                    string contain lxl file content with list of exl file path and name
        
        '''
        file_content = ''
        for item in file_list:
            if exl_path_in_lxl:
                file_content = file_content + exl_path_in_lxl + item + '\n'
            else:
                file_content = file_content + item + '\n'
                
        return file_content
    