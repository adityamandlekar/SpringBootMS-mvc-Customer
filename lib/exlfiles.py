﻿from __future__ import with_statement
import codecs
import datetime
import os
import os.path
import re
from subprocess import Popen, PIPE
import string
import xml
import xml.dom.minidom
from xml.dom.minidom import Document

from VenueVariables import *
    
def add_ric_to_exl_file(exlFileSource, exlFileTarget, ric, symbol=None, domain="MARKET_PRICE", instrumentType="NORMAL_RECORD", displayName="TEST RIC", officialCode="1"):
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

def blank_out_holidays(srcExlFile, destExlFile):
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

def build_LXL_file (exlFileNeedToRemove):  
    '''
    Argument:    
                exlFileNeedToRemove : exlFilename that need to exclude in LxL file

    return: 
                string contain lxl file content with list of exl file path and name
    
    '''
   
    exlFilesFullPath = _get_EXL_files("All")

    file_content = ''
    for exlFileFullPath in exlFilesFullPath:

        #extract only the exl file path
        exlFileFullPathSplit = exlFileFullPath.rsplit("\\",1)
        exlFilePath = exlFileFullPathSplit[0]
        exlFile     = exlFileFullPathSplit[-1]

        #convert proper exl file path for LxL file
        exlFilePathNew = _get_exl_file_path_for_lxl_file(exlFilePath)
        if (exlFileNeedToRemove != exlFile):
            file_content = file_content + exlFilePathNew + exlFile + '\n'

    return file_content

def create_RIC_SIC_rename_file(oldRic, oldSic, srcPath, exlfile):
    """ Create src flie dynamically to rename both RIC and SIC:
        Argument :oldRic: old ric name 
             oldSic: old sic name
             srcPath: path for src file and exl file  (e.g. /ChangeSicRic.src)
             exlfile: get full path of exlfile in local from fmscmd (e.g. /nasmf_a.exl)
        return : New Ric and Sic name
        
    """ 
    
    if os.path.exists(srcPath):
        os.remove(srcPath)
        
    srcDoc = Document()
    src = srcDoc.createElement('SRC') #set root element
    src.setAttribute('xmlns', 'SrcSchema')
    src.setAttribute('xmlns:it', 'DbIssueTypeSchema')
    src.setAttribute('xmlns:xsi',"http://www.w3.org/2001/XMLSchema-instance")
    src.setAttribute('xsi:schemaLocation','DbFieldsSchema AllFields.xsd SrcSchema SrcSchema.xsd')
    srcDoc.appendChild(src)
        
    date = srcDoc.createElement ('date')
    date_txt = srcDoc.createTextNode(datetime.datetime.now().strftime("%Y-%m-%d"))
    date.appendChild(date_txt)
    src.appendChild(date)
    
    action = srcDoc.createElement('action')
    action_txt = srcDoc.createTextNode('BOTH')
    action.appendChild(action_txt)
    src.appendChild(action)
        
    dom = xml.dom.minidom.parse(exlfile)
    root = dom.documentElement
     #exlFileName,exchangeName,
    exlFileName = root.getElementsByTagName('name')[0].firstChild.data
    iteratorlist = dom.getElementsByTagName('it:EXCHANGE')
    exchangeName = iteratorlist[0].firstChild.data
    
    exlFile = srcDoc.createElement('exlFile')
    exlFile_txt = srcDoc.createTextNode(exlFileName)
    exlFile.appendChild(exlFile_txt)
    src.appendChild(exlFile)
    
    exchange = srcDoc.createElement('exchange')
    exchange_txt = srcDoc.createTextNode(exchangeName)
    exchange.appendChild(exchange_txt)
    src.appendChild(exchange)
    
    kNode = srcDoc.createElement('k')
    src.appendChild(kNode)
    
    bothNode = srcDoc.createElement('both')
    kNode.appendChild(bothNode)
    
    orNode = srcDoc.createElement('or')
    orNode_txt = srcDoc.createTextNode(oldRic)
    orNode.appendChild(orNode_txt)
    bothNode.appendChild(orNode)
    
    newRic = ('TEST' + oldRic + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))[0:32]
    nrNode = srcDoc.createElement('nr')
    nrNode_txt = srcDoc.createTextNode(newRic)
    nrNode.appendChild(nrNode_txt)
    bothNode.appendChild(nrNode)
    
    osNode = srcDoc.createElement('os')
    osNode_txt = srcDoc.createTextNode(oldSic[2:len(oldSic)] )
    osNode.appendChild(osNode_txt)
    bothNode.appendChild(osNode)
    
    newSic = oldSic[2:len(oldSic)] + 'TestSIC'
    nsNode = srcDoc.createElement('ns')
    nsNode_txt = srcDoc.createTextNode(newSic)
    nsNode.appendChild(nsNode_txt)
    bothNode.appendChild(nsNode)
    
    fileHandle = open(srcPath, 'w') 
    srcDoc.writexml(fileHandle, indent='\t', addindent='\t', newl='\n', encoding="utf-8")
    return newRic, newSic


def get_DST_and_holiday_RICs_from_EXL(exlFile,ricName):
    """ Get DST RIC and holiday RIC from EXL
        http://www.iajira.amers.ime.reuters.com/browse/CATF-1735

        return : DST RIC and holiday RIC, if found. Otherwise, returns 'Not Found'.
    """ 
    
    return get_ric_fields_from_EXL(exlFile,ricName,'DST_REF','HOLIDAYS_REF1')

def _get_exl_file_path_for_lxl_file(exl_path): 
    """Deriving exl path for lxl file from exl full file path
             
    Argument:    
                exl_path : the exl file path no name.\n     

    return:
                exl directory required by lxl file without file name

                Remark: FMSCMD can only hanlde following struture of directory for path found in Lxl file

                1. All EXL Files must be found within "EXL Files" folder

                if exl_path D:\\tools\\FMSCMD\\config\\DataFiles\\Groups\\RAM\\MFDS\\MUT\\ABC Files
                return error

                if exl_path D:\\tools\\FMSCMD\\config\\DataFiles\\Groups\\RAM\\MFDS\\MUT\\
                return error

                2. There must be a subfolder under the service name folder e.g. \\MFDS\\MUT
                D:\\tools\\FMSCMD\\config\\DataFiles\\Groups\\RAM\\MFDS\\MUT\\EXL Files

                if exl_path D:\\tools\\FMSCMD\\config\\DataFiles\\Groups\\RAM\\MFDS\\EXL Files
                return error

                Example:
                LOCAL_FMS_DIR  is D:\\tools\\FMSCMD\\config\\DataFiles\\Groups
                if exl_file D:\\tools\\FMSCMD\\config\\DataFiles\\Groups\\RAM\\MFDS\\MUT\\EXL Files
                return path RAM/MFDS/MUT/
    """  
    
    #Check #1
    split_path = exl_path.split("\\")
    if (split_path[-1] != "EXL Files"):
        raise AssertionError('*ERROR* \'EXL Files\' folder not found in exl path [%s]. This does not fulfill FMSCMD requirements for reconcile by LXL file' %(exl_path))
        
    new_path = exl_path.replace(LOCAL_FMS_DIR + "\\",'').replace('EXL Files','')
    nodes = new_path.split("\\")   
    nodes = filter(None, nodes)

    #Check #2
    if len(nodes)<2:
        raise AssertionError('*ERROR* Cannot determine LXL path based on FMS dir [%s] and EXL path [%s]' %(LOCAL_FMS_DIR, exl_path))
     
    if len(nodes)==2:
        raise AssertionError('*ERROR* Sub-folder not found under the service name [%s]. This does not fulfill FMSCMD requirements for reconcile by LXL file' %(new_path))
    else:
        new_path = new_path.replace('\\','/')
        
    return new_path
    
def get_EXL_for_RIC(domain, service, ric):
    """ Find the EXL file with the specified RIC, domain, and service
        
        Argument: 
            domain:  The market domain ['MARKET_PRICE', 'MARKET_BY_ORDER', 'MARKET_BY_ORDER', 'MARKET_MAKER']
            service: The service name
            ricName:  The RIC to find
        
        return : Full EXL file path name
    """ 
    
    exlFiles = _get_EXL_files("All")
    
    for exlFile in exlFiles:
        dom = xml.dom.minidom.parse(exlFile)
        
        # skip file if service does not match
        fieldNames = ['SERVICE']
        result = _get_EXL_header_values(dom,fieldNames)
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

def get_REAL_Fids_in_icf_file(srcfile, count = 1):
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
#             print subnode.toprettyxml()
#             print 'DEBUG --------------'
#             print 'DEBUG subnode.nodeType %s, subnode.nodeName %s' %(subnode.nodeType,subnode.nodeName)
            for ssubnode in subnode.childNodes:
#                 print 'DEBUG ssubnode.nodeType %s, ssubnode.nodeName %s' %(ssubnode.nodeType,ssubnode.nodeName)
#                 if ssubnode.nodeType == node.ELEMENT_NODE and ssubnode.nodeName == 'it:outputFormat':
#                     print 'DEBUG nodeType %s, nodeName %s firstChildData %s' %(ssubnode.nodeType, ssubnode.nodeName, ssubnode.firstChild.data)
                if ssubnode.nodeType == node.ELEMENT_NODE and ssubnode.nodeName == 'it:outputFormat' and ssubnode.firstChild.data == 'TRWF_REAL_NOT_A_NUM':
                    tempList = subnode.nodeName.split(':') 
                    Fidlist.append(tempList[1])
                    fidCount = fidCount + 1
                    if fidCount >= int (count) :
                        return Fidlist
    
    raise AssertionError('*ERROR* not enough REAL type FIDs found in icf file %s'%(srcfile))   

def get_ric_fields_from_EXL(exlFile,ricName,*fieldnames):
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
    heanderDict = _get_EXL_header_values(dom,fieldnames)
    ObjDict = _get_EXL_object_values(dom,ricName,fieldnames)
    
    for fieldname in fieldnames:
        if (ObjDict[fieldname] != "Not Found"):
            retList.append(ObjDict[fieldname])
        elif (heanderDict[fieldname] != "Not Found"):
            retList.append(heanderDict[fieldname])
        else:
            raise AssertionError('*ERROR* %s not found for RIC(%s) in %s' %(fieldname, ricName, exlFile))

    return retList

def get_all_state_EXL_files():
    """ Get EXL file from given RIC, domain, and service:
        http://jirag.int.thomsonreuters.com/browse/CATF-2506

        fileType options: ['Closing Run', 'DST', 'Feed Time', 'Holiday', 'OTFC', 'Trade Time']
        
        return : Full path name of EXL file, if found. 
                 If multiple files or none found, will raise an error.
    """
    exlFiles_list = []
    fileType_list = ['closing run','dst', 'feed time', 'holiday', 'trade time']

    for fileType in fileType_list:
        exlFiles = _get_EXL_files(fileType)
        exlFiles_list.extend(exlFiles)
    return exlFiles_list

def get_SicDomain_in_AllExl_by_ContextID(service, contextID_List):
    """ Get sic, domain from EXL by contextID.
       Argument:
           service :  FMS service name             
           contextID_List : context id list from MTE config file 
       Return : a dictionary with contextID: set(sic|domain) 
       
    """    
    sicDomainByContxtID_Dir = {}
    exlFilesFullPath = _get_EXL_for_Service(service)
    fieldNames = ['CONTEXT_ID']
      
    for exlFile in exlFilesFullPath:
        dom = xml.dom.minidom.parse(exlFile)
        root = dom.documentElement
        result = _get_EXL_header_values(dom, fieldNames)
        exlFileName = root.getElementsByTagName('name')[0].firstChild.data
        if 'CONTEXT_ID' in result:
            context_id = result['CONTEXT_ID'].encode("utf-8")
            if result['CONTEXT_ID'] in contextID_List:
                iteratorlist = dom.getElementsByTagName('exlObject')
                for node_ExlObject in iteratorlist:  #signal exlObject
                    iterNum = 0
                    for subnode_ExlObject in node_ExlObject.childNodes:
                        if subnode_ExlObject.nodeType == node_ExlObject.ELEMENT_NODE and subnode_ExlObject.nodeName == 'it:RIC':
                            ric  = subnode_ExlObject.firstChild.data.encode("utf-8")
                        if subnode_ExlObject.nodeType == node_ExlObject.ELEMENT_NODE and subnode_ExlObject.nodeName == 'it:SYMBOL':
                            symbol = subnode_ExlObject.firstChild.data.encode("utf-8")
                            iterNum +=1
                        elif subnode_ExlObject.nodeType == node_ExlObject.ELEMENT_NODE and subnode_ExlObject.nodeName == 'it:DOMAIN':
                            domain = subnode_ExlObject.firstChild.data.encode("utf-8")
                            iterNum +=1
                        elif iterNum == 2:
                            break
                    
                    if iterNum != 2:
                        raise AssertionError("'*ERROR* The RIC %s is missing SYMBOL or DOMAIN node in the EXL %s'" %(ric, exlFileName))    
                    else:
                        newSicDomain_string = symbol+'|'+domain                            
                        if context_id not in sicDomainByContxtID_Dir:
                            sicDomainByContxtID_Dir[context_id] = {newSicDomain_string}
                        else:
                            sicDomainByContxtID_Dir[context_id].add(newSicDomain_string)            
    if len(sicDomainByContxtID_Dir) == 0:
        raise AssertionError("*ERROR* There are no RICs/SICs for context ids [%s] in the EXL files" %', '.join(map(str, contextID_List)))
    else:
        return sicDomainByContxtID_Dir

def get_state_EXL_file(ricName,domainName,service,fileType):
    """ Get EXL file from given RIC, domain, and service:
        http://www.iajira.amers.ime.reuters.com/browse/CATF-1737

        fileType options: ['Closing Run', 'DST', 'Feed Time', 'Holiday', 'OTFC', 'Trade Time', 'All']
        
        return : Full path name of EXL file, if found. 
                 If multiple files or none found, will raise an error.
    """ 
    
    exlFiles = _get_EXL_files(fileType)
    
    matchedExlFiles = []
    
    for exlFile in exlFiles:
        dom = xml.dom.minidom.parse(exlFile)
        
        # skip file if service does not match
        fieldNames = ['SERVICE']
        result = _get_EXL_header_values(dom,fieldNames)
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

def keep_specified_exlobject(exlfilefullpath, RIC, Domain, outputfile):
    """keep the specified ric,domain exl object and remove all other exl objects.

    exlfilefullpath is the exl absolute path on local machine.\n
    RIC is the ric name in exl. Domain is the domain name.\n
    
    Return the modified exl path.

    Examples:
    | ${result} = | keep specified exlobject | c:/temp/test.exl | CB.N | MARKET_PRICE | C:/TEMP/tmp.exl |
    """
    keep=True
    return _remove_exlobject(exlfilefullpath, RIC, Domain, keep, outputfile)

def modify_exl(srcfile, dstfile, ric, domain, *ModifyItem):
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

    return _modify_fm_file(srcfile, dstfile, 'exlObject', ric, domain, *ModifyItem)

def modify_exl_header(srcfile, dstfile, *ModifyItem):
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
    return _modify_fm_file(srcfile, dstfile, 'exlHeader', '', '', *ModifyItem)

def modify_icf(srcfile, dstfile, ric, domain, *ModifyItem):
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
    return _modify_fm_file(srcfile, dstfile, 'r', ric, domain, *ModifyItem)

def modify_REAL_items_in_icf(srcfile, dstfile, ric, domain, fidsAndValues={}):   
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
    
    modify_icf(srcfile, dstfile, ric, domain, *itemList)        
    
def remove_specified_exlobject(exlfilefullpath, RIC, Domain, outputfile):
    """remove the specified exl object and keep all other exl objects.

    exlfilefullpath is the exl absolute path on local machine.\n
    RIC is the ric name in exl. Domain is the domain name.\n
    
    Return the modified exl path.

    Examples:
    | ${result} = | remove specified exlobject | c:/temp/test.exl | CB.N | MARKET_PRICE | C:/TEMP/tmp.exl |
    """
    keep=False
    return _remove_exlobject(exlfilefullpath, RIC, Domain, keep, outputfile)
 
def _get_EXL_files(fileType):
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

def _get_EXL_for_Service(service):
    """ Find the EXL file with service
        Argument: 
            service: The service name        
        return :  a list of EXL file names.
    """ 
    exFiles_service = []
    exlFiles = _get_EXL_files("All")
    fieldNames = ['SERVICE']
    for exlFile in exlFiles:
        dom = xml.dom.minidom.parse(exlFile)     
        # skip file if service does not match
        result = _get_EXL_header_values(dom,fieldNames)
        if 'SERVICE' in result and result['SERVICE'] == service:
            exFiles_service.append(exlFile)
    if len(exFiles_service) == 0:
        raise AssertionError('*ERROR* service %s not found in any EXL file:' %(service))
    else:
        return exFiles_service

def _get_EXL_header_values(dom,fieldnames):
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

def _get_EXL_object_values(dom,ricName,fieldnames):
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

def _modify_fm_file(srcfile, dstfile, modifyType, ric, domain, *ModifyItem):
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

            if pat.search(value):
                # multiple layers
                # (KW does not currently support special XML chars in new value if multiple layers)
                tempdom = xml.dom.minidom.parseString('<%s xmlns:it="DbFieldsSchema">'%field + value + '</%s>'%field) 
#                 print tempdom.toprettyxml()
                tempnode = tempdom.documentElement
                modifyflag = setvalue(iteratoroot, field, tempnode, True)
                #print iteratoroot.childNodes.item(11).childNodes.item(1).childNodes
            else:
                # replace all XML special chars (&"'<>) in new value with the escaped equivalent
                escapedValue = value
                escapedValue = escapedValue.replace("&","&amp;")
                escapedValue = escapedValue.replace("\"","&quot;")
                escapedValue = escapedValue.replace("'","&apos;")
                escapedValue = escapedValue.replace("<","&lt;")
                escapedValue = escapedValue.replace(">","&gt;")
                
                # use the escaped value here, or parsing fails
                tempdom = xml.dom.minidom.parseString('<%s xmlns:it="DbFieldsSchema">'%field + escapedValue + '</%s>'%field) 
#                 print tempdom.toprettyxml()
                tempnode = tempdom.documentElement
                # use the orginal value here, not the escaped value
                modifyflag = setvalue(iteratoroot, field, value, False)
            if modifyflag == False:
                #raise AssertionError("*ERROR* not found field %s for %s and %s in exl" % (field, ric, domain))
                print '*INFO* requested field %s does not exist, adding new field'%field
                tempnode.removeAttribute('xmlns:it')
                if modifyType == 'r':                       
                    note = iteratoroot
                    note.appendChild(tempnode)
                else :
                    note = iteratoroot.getElementsByTagName('exlObjectFields') 
                    note[0].appendChild(tempnode)
        else:
            raise AssertionError("*ERROR* the format of modified item is incorrect")
    
    with codecs.open(dstfile,'w','utf-8') as out:
        dom.writexml(out,addindent='',newl='',encoding='utf-8')
    
    return dstfile

def _remove_exlobject(exlfilefullpath, RIC, Domain,keep, outputfile):
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
    
