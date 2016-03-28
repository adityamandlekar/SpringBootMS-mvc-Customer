from __future__ import with_statement
import os
import os.path
import re
from sets import Set
import string
import xml
import xml.etree.ElementTree as ET

from LinuxToolUtilities import LinuxToolUtilities
import xmlutilities

def add_mangling_rule_partition_node(rule, contextID, configFileLocalFullPath):
    """Add mangling rule of specific context ID in manglingConfiguration.xml
       add <Partition rule ... /> into <Partitions> if it does not exist, ignore if it has already exisited.
    
    rule : SOU (rule="3"), BETA (rule="2"), RRG (rule="1") or UNMANGLED (rule="0") [Case-insensitive]
    contextID : the context ID you want to add to <Partitions>
    configFileLocalFullPath : full path of mangling config file xml
    Returns : Nil

    Examples:
    | add_mangling_rule_partition_node | RRG | "1234" | C:/tmp/manglingConfiguration.xml |
    
    Call this KW, The partitions section of the manglingConfiguration file should look something like this:
     <Partitions type="FID" value="CONTEXT_ID" defaultRule="3">
      <!-- Items with CONTEXT_ID 1234 or 2345 use Elektron RRG rule. All other Items use SOU rule. -->
        <Partition value="1234" rule="1" />   <!-- KW will add this line if it does not exist -->
        <Partition value="2345" rule="1" />
     </Partitions>
    """
    root = xmlutilities.load_xml_file(configFileLocalFullPath,False)
    partitions = root.find(".//Partitions")
    foundMatch = False
    for node in partitions:
        if (node.get('value') == contextID):
            foundMatch = True
    if (foundMatch == False):
        partitions.append(ET.fromstring('<Partition rule="%s" value="%s" />\n' %(LinuxToolUtilities().MANGLINGRULE[rule.upper()], contextID)))
    xmlutilities.save_to_xml_file(root,configFileLocalFullPath,False)

def delete_mangling_rule_partition_node(contextIDs, configFileLocalFullPath):
    """delete the mangling rule for specficied contextIDs in manglingConfiguration.xml

       contextIDs: the context ids you want to deleted
       configFileLocalFullPath: full path of mangling config file xml

       Examples:
       | delete_mangling_rule_partition_node | ["1234","2345"] | C:/tmp/manglingConfiguration.xml |
       
       <Partitions type="FID" value="CONTEXT_ID" defaultRule="3">
            <Partition value="1234" rule="1" />   <!-- KW will delete this line -->
            <Partition value="2345" rule="1" />   <!-- KW will delete this line -->
     </Partitions>
    """
    root = xmlutilities.load_xml_file(configFileLocalFullPath,False)
    partitions = root.find(".//Partitions")
    for contextID in contextIDs:
        foundNode = None
        for node in partitions:
            if (node.get('value') == contextID):
                foundNode = node
        if (foundNode != None):
            partitions.remove(foundNode)
    xmlutilities.save_to_xml_file(root,configFileLocalFullPath,False)

def get_context_ids_from_fms_filter_string(fms_filter_string): 
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

def get_MTE_config_list_by_path(venueConfigFile,*xmlPath):
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
    
    foundConfigValues = _search_MTE_config_file(venueConfigFile,*xmlPath)
    
    if len(foundConfigValues) == 0:
        return []
    else:
        return foundConfigValues

def get_MTE_config_list_by_section(venueConfigFile, section, tag):
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

def get_MTE_config_value(venueConfigFile,*xmlPath):
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
    
    foundConfigValues = _search_MTE_config_file(venueConfigFile,*xmlPath)
    
    if len(foundConfigValues) == 0:
        return "NOT FOUND"
    elif len(foundConfigValues) > 1:
        raise AssertionError('*ERROR*  Found more than 1 value [%s] in venue config file: %s' %(', '.join(foundConfigValues), venueConfigFile))
    else:
        return foundConfigValues[0]

def get_multicast_address_from_label_file(ddnLabels_file, labelID, mteName=""):
    ''' Extract multicast IP and port from label file based on the labelID
    
        Argument : ddnLabels_file:  ddnLabels or ddnReqLabels file or ddnPublishers (if mteName is not empty)
                   labelID : labelID defined in venue config file
                   mteName : MTE instance name 
        Return : list contains multicast ip and port
    '''     
    tree = ET.parse(ddnLabels_file)
    root = tree.getroot()
    
    labelNode = root.findall('.//label')
    if not labelNode: 
        raise AssertionError('*ERROR* label element does not exist in %s' % ddnLabels_file)
    
    multTagText = ""
    multicast_port_tag = ""
    multicast_ip = ""
    multicast_port = ""
    for node in labelNode:
        if node.get('ID') == labelID:
            if (mteName != ""): #indicate checking ddnPublishers.xml
                providers = node.findall('provider')
                found = False
                for provider in providers:
                   if provider.get('NAME') == mteName:
                    multTagText = provider.find('cvaMultTag').text
                    found = True
                if not (found):
                    raise AssertionError('*ERROR* could not find provider NAME = %s text for labelID %s' %(mteName, labelID))
            else:
                multTagText = node.find('multTag').text
            break
    
    if (multTagText == None):
        raise AssertionError('*ERROR* could not find multTag text for labelID %s' % labelID)
    
    multAddrNode = root.findall('.//multAddr')    
    for node in multAddrNode:
        if node.get('TAG') == multTagText:
            multicast_ip = node.get('ADDR')
            multicast_port_tag = node.get('PORT')
            break;
        
    if (multicast_port_tag == None):
        raise AssertionError('*ERROR* could not find port for multAddr node %s' % multTagText)
    
    for node in root.findall('.//port'):
        if node.get('ID') == multicast_port_tag:
            multicast_port = node.text
            
    if (multicast_ip == None) or (multicast_port == ""): 
        raise AssertionError('*ERROR* failed to get multicast address for LabelID %s' % labelID)
    
    multicast_address = []        
    multicast_address.append(multicast_ip)
    multicast_address.append(multicast_port)
    
    return multicast_address

def get_sps_ric_name_from_label_file(ddnLabelFile, labelID):
    ''' Extract multicast IP and port from label file based on the labelID
    
        Argument : ddnLabelsFile - the local ddnLabels file name e.g. c:\temp\ddnLabel.xml
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
                if providerNode.get('NAME') == MTE:
                    spsText = providerNode.find('sps').text
                    return spsText
            break
    
    if not spsText:
        raise AssertionError('*ERROR* could not find sps ric text for labelID %s' % labelID)

def remove_xinclude_from_labelfile(ddnLabels_file, updated_ddnLabels_file):
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
 
def set_mangling_rule_default_value(rule,configFileLocalFullPath):
    """set the mangling rule <Partition defaultRule=""> in manglingConfiguration.xml
    
    rule : SOU (rule="3"), BETA (rule="2"), RRG (rule="1") or UNMANGLED (rule="0") [Case-insensitive]
    cfgfile : full path of mangling config file xml
    Returns : Nil

    Examples:
    | set mangling rule default value | SOU | C:/tmp/manglingConfiguration.xml |
    
    The partitions section of the manglingConfiguration file should look something like this:
    e.g <Partitions type="FID" value="CONTEXT_ID" defaultRule="3"> 
        </Partitions>
    """
    
    #safe check for rule value
    if (LinuxToolUtilities().MANGLINGRULE.has_key(rule.upper()) == False):
        raise AssertionError('*ERROR* (%s) is not a standard name' %rule)
    
    xPath = ['Partitions']
    attribute = {'defaultRule' : LinuxToolUtilities().MANGLINGRULE[rule.upper()]}
    xmlutilities.set_xml_tag_attributes_value(configFileLocalFullPath,attribute,False,xPath)
    
def set_mangling_rule_parition_value(rule,contextIDs,configFileLocalFullPath):
    """set the mangling rule of "ALL" <Partitions rule=""> in manglingConfiguration.xml
    
    rule : SOU (rule="3"), BETA (rule="2"), RRG (rule="1") or UNMANGLED (rule="0") [Case-insensitive]
    contextIDs : empty list = replace all  <Partition> with given rule or only attribute 'value' of <Partition> that found in list will change to given rule
    configFileLocalFullPath : full path of mangling config file xml
    Returns : Nil

    Examples:
    | set mangling rule parition value | RRG | C:/tmp/manglingConfiguration.xml |
    
    The partitions section of the manglingConfiguration file should look something like this:
     <Partitions type="FID" value="CONTEXT_ID" defaultRule="3">
      <!-- Items with CONTEXT_ID 1234 or 2345 use Elektron RRG rule. All other Items use SOU rule. -->
        <Partition value="1234" rule="1" />
        <Partition value="2345" rule="1" />
     </Partitions>
    """
    
    #safe check for rule value
    if (LinuxToolUtilities().MANGLINGRULE.has_key(rule.upper()) == False):
        raise AssertionError('*ERROR* (%s) is not a standard name' %rule)
    
    xPath = ['Partitions','Partition']
    attribute = {'rule' : LinuxToolUtilities().MANGLINGRULE[rule.upper()]}
    if (len(contextIDs) == 0):
        xmlutilities.set_xml_tag_attributes_value(configFileLocalFullPath,attribute,False,xPath)
    else:
        for contextID in contextIDs:
            add_mangling_rule_partition_node(rule, contextID, configFileLocalFullPath)
            conditions = {'value' : contextID}
            xmlutilities.set_xml_tag_attributes_value_with_conditions(configFileLocalFullPath,conditions,attribute,False,xPath)
            conditions.clear()

def set_MTE_config_tag_value(xmlFileLocalFullPath,value,*xPath):
    """set tag value in venue config xml file
    
    xmlFileLocalFullPath : full path of xml file
    value : target tag value
    xPath : xPath for the node
    Returns : Nil

    Examples:
    | set MTE config tag value | C:/tmp/venue_config.xml | 13:00 | EndOfDayTime
    """
                    
    xmlutilities.set_xml_tag_value(xmlFileLocalFullPath,value,True,xPath)

def _search_MTE_config_file(venueConfigFile,*xmlPath):
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
