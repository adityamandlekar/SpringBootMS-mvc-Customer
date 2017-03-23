from __future__ import with_statement
import json
import os
import os.path
import re
from sets import Set
import string
import xml
import xml.etree.ElementTree as ET
from LinuxFSUtilities import LinuxFSUtilities
from utils.ssh import _exec_command, _search_file
import xmlutilities

from VenueVariables import *

MANGLINGRULE = {'SOU': '3', 'BETA': '2', 'RRG': '1', 'UNMANGLED' : '0'};

#############################################################################
# Keywords that use local copy of configuration files
#############################################################################

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
        partitions.append(ET.fromstring('<Partition rule="%s" value="%s" />\n' %(MANGLINGRULE[rule.upper()], contextID)))
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

def get_context_ids_from_config_file(venueConfigFile):
    """get the context ids from venue config file
    Argument: 
    venueConfigFile : local path of venue config file

    Returns : a set of context ids

    Examples:
    | get_context_ids_from_config_file | E:\\temp\\hkf02m.xml |
    """

    context_id_set = Set()

    match = []
    match = get_MTE_config_key_list(venueConfigFile,'Transforms')

    for m in match:
        if m[0].lower() == 'c':
            context_id_set.add(m[1:])

    return context_id_set

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

def Get_future_config_times(configNameList,configValueList, GMTOffset, currentDateTime):
    """Convert all event times to future GMT time and return one dictionary
    
    Argument : 
    configNameList  : config names list
    configValueList : config values list which get from MTE config file
    GMTOffset :  GMT offset in second like -18000(GMT-5)
    currentDateTime : date time get from TD box (GMT)
        
    Returns : Dictionary which the time is the key, value is list of the config names like
    {'2016-12-06 12:00:00': [u'StartOfDayTime'], '2016-12-07 03:30:00': [u'EndOfDayTime'], '2016-12-06 05:00:00': [u'RolloverTime', u'CacheRolloverTime', u'JnlRollTime', u'CacheRollover']}
    Examples :
          | get future config times | ${configNameList} | ${configValueList} | 28800 | ${currentDateTime}
    """
    configValueOrginList = configValueList
    retDict = {}
    currentDateTimeStr = '%4d-%02d-%02d %02d:%02d:00'%(int(currentDateTime[0]),int(currentDateTime[1]),int(currentDateTime[2]),int(currentDateTime[3]),int(currentDateTime[4]))

    index = 0
    from robot.libraries.DateTime import subtract_time_from_date,add_time_to_date
    for timepoint in configValueList:
        if timepoint.lower() == 'not found':
            index += 1
            continue
        timestr = '%4d-%02d-%02d %s:00'%(int(currentDateTime[0]),int(currentDateTime[1]),int(currentDateTime[2]),timepoint)
        # local--> GMT time, should minus GMToffset
        timeGMT = subtract_time_from_date(timestr,'%s seconds'%GMTOffset)
        #if the GMT time is previous currentDateTime, add one day
        count = 0
        while timeGMT < currentDateTimeStr and count < 2:
            timeGMT = add_time_to_date(timeGMT,'%s seconds'%str(3600*24))
            count += 1

        if timeGMT not in retDict.keys():
            retDict[timeGMT] = []
        retDict[timeGMT].append(configNameList[index])
        index += 1

    return retDict

def modify_GRS_config_feed_item_value(grs_config_file, itemName, newValue):
    """update the item value from grs config files
    Argument : 
    grs_config_file  : local path of grs config file
    itemName :  item name (key)
    newValue : value for the item 

    Examples:
    | modify GRS feed item value from config file | E:\\temp\\hkf_grs.json|  maxstreambuffer | 100
    """  
    with open(grs_config_file) as data_file:   
        data = json.load(data_file)
        if (data.has_key('inputs')):
            for item in (data['inputs']):
                data['inputs'][item][itemName] = newValue
                    
    tmpFile =  grs_config_file + "_modified"
    with open(tmpFile, 'w') as f:      
        json.dump(data, f, sort_keys = True, indent = 2, ensure_ascii=True)
               
    return tmpFile        
                
                
def get_GRS_stream_names_from_config_file(grs_config_file):
    """get the stream names from grs config files
    Argument : 
    grs_config_file  : local path of grs config file
        
    Returns : a list of stream names

    Examples:
    | get GRS stream names from config file | E:\\temp\\hkf_grs.json|  
    """  
    streamNames = []

    if (grs_config_file.find("configure_grs") != -1):
        return streamNames

    with open(grs_config_file) as data_file:   
        data = json.load(data_file)
        if (data.has_key('inputs')):
            
            for mte, item in (data['inputs']).iteritems():
                streamNames += item['lines'].keys()

    return streamNames

def get_Label_ID_For_Context_ID(venueConfigFile, contextId):
    """ Get Label ID For Context ID from venue config file
    Get the Label ID by search for node <CXXXX> in <Transforms> section, which XXXX is the Context ID. 
    Its child node <OutputLabel> value is the corresponding Label ID. 

    Argument : venueConfigFile : local path of venue config file
               contextId : the target Context ID which you want to found its Label ID

    Return : Label ID of the input Context ID

    Examples :
    | ${labelID}= | Get Label ID For Context ID | venue_config_file | 1577 |

    Venue config file example:
   "Transforms": {
       "C1577": {
          "OutputLabel": "7092",
             ...
        }
       "C1578": {
          "OutputLabel": "7092",
             ...
         }
    }
    """

    foundLabelId = get_MTE_config_value(venueConfigFile, 'Transforms', 'C'+contextId, 'OutputLabel')
    if foundLabelId == 'NOT FOUND':
        raise AssertionError('*ERROR*  Fail to find Label ID for Context ID %s from venue config file: %s' %(contextId, venueConfigFile))
    return foundLabelId

def get_MTE_config_key_list(venueConfigFile, *path):
    """ Get the list of key values under the specified path from venue config file

    Argument : venueConfigFile : local path of venue config file
               path : one or more node names that identify the path to use

    Return : list of keys

    Examples :
    | ${keyList}= | get MTE config key list | venue_config_file | Transforms |
    """

    if len(path) < 1:
        raise AssertionError('*ERROR*  Need to provide path to look up.')
        
    if not os.path.exists(venueConfigFile):
        raise AssertionError('*ERROR*  %s is not available' %venueConfigFile)
    
    with open (venueConfigFile, "r") as myfile:
        node = json.load(myfile)
    
    for p in path:
        if p in node:
            node = node[p]
        else:
            raise AssertionError('*ERROR*  Missing [%s] element from venue config file: %s' %(p, venueConfigFile))
        
    if isinstance(node, dict):
        return node.keys()
    else:
        return []
    
def get_MTE_config_list_by_path(venueConfigFile,*path):
    """ Gets value(s) from venue config file
        http://www.iajira.amers.ime.reuters.com/browse/CATF-1798
        
        params : venueConfigFile - full path to local copy of venue configuration file
                 path - one or more node names that identify the node path

        return : list containing value(s) of given path, if found. Otherwise, returns empty list
        
        Examples :
        | ${domainList}= | get MTE config list | ${LOCAL_TMP_DIR}/venue_config.xml | FMS | MFDS | Domain |

        Venue config file example:
           "FMS": {
              "Enabled": 1,
              "EnableInboundJournaling": 0,
              "EnableOutboundJournaling": 0,
              "ReorgTimeoutInSeconds": 1200,
              "ReorgTimeoutMode": "None",
              "ResendFM": 1,
              "SendRefreshForFullReorg": 0,
              "Services": ["HK-HKF"],
              "HK-HKF": {
                 "Domain": ["MARKET_PRICE","MARKET_BY_PRICE", "MARKET_BY_ORDER"],
                 "FilterString": "CONTEXT_ID = 1577 OR CONTEXT_ID = 1578 OR CONTEXT_ID = 2299 OR CONTEXT_ID = 2861 OR CONTEXT_ID = 2862 OR CONTEXT_ID = 2863 OR CONTEXT_ID = 2865 OR CONTEXT_ID =     3213 OR CONTEXT_ID = 1662 OR CONTEXT_ID = 3200",
                 "NDAFilterValue": 1
              }
           }
    """ 
    
    return _search_MTE_config_file(venueConfigFile,*path)

def get_MTE_config_list_by_section(venueConfigFile, section, tag):
    """ Gets value(s) from venue config file based on the venue config file section node name and subelement node name (tag).
        There may be one or more nodes between the specified section name and the subelement name.  All intermediate nodes are searched.
        Argument : venueConfigFile : full path to local copy of venue configuration file
                 section : top section node in venueConfigFile
                 tag : subelement node name under section appeared in venueConfigFile
        Return : value list of given node name, if found. Otherwise, returns empty list.
        Examples :
        | ${labelIDs}= | get MTE config value list| venue_config_file| Publishing | LabelID |
         
    """ 
    if not os.path.exists(venueConfigFile):
        raise AssertionError('*ERROR*  %s is not available' %venueConfigFile)
    
    with open (venueConfigFile, "r") as myfile:
        node = json.load(myfile)
        
    if section not in node:
        raise AssertionError('*ERROR*  Missing [%s] element from venue config file: %s' %(section, venueConfigFile))
        
    values = []
    values += _get_matching_values_from_dict(node[section], tag)
    return values

def get_MTE_config_value(venueConfigFile,*path):
    """ Gets value from venue config file
        http://www.iajira.amers.ime.reuters.com/browse/CATF-1736
        
        params : venueConfigFile - full path to local copy of venue configuration file
                 path - one or more node names that identify the XML path

        return : value of given field, if found. If multiple values found, will assert an error. Otherwise, returns "NOT FOUND" if nothing found.
        
        Example :
        | ${filterString}= | get MTE config value | FMS | HK-HKF | FilterString |
        
        Venue config file example:
           "FMS": {
              "Enabled": 1,
              "EnableInboundJournaling": 0,
              "EnableOutboundJournaling": 0,
              "ReorgTimeoutInSeconds": 1200,
              "ReorgTimeoutMode": "None",
              "ResendFM": 1,
              "SendRefreshForFullReorg": 0,
              "Services": ["HK-HKF"],
              "HK-HKF": {
                 "Domain": ["MARKET_PRICE","MARKET_BY_PRICE", "MARKET_BY_ORDER"],
                 "FilterString": "CONTEXT_ID = 1577 OR CONTEXT_ID = 1578 OR CONTEXT_ID = 2299 OR CONTEXT_ID = 2861 OR CONTEXT_ID = 2862 OR CONTEXT_ID = 2863 OR CONTEXT_ID = 2865 OR CONTEXT_ID =     3213 OR CONTEXT_ID = 1662 OR CONTEXT_ID = 3200",
                 "NDAFilterValue": 1
              }
           }
    """ 
    
    foundConfigValues = _search_MTE_config_file(venueConfigFile,*path)
    
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
    
    multTagText = None
    multicast_port_tag = None
    multicast_ip = None
    multicast_port = None
    for node in labelNode:
        if str(node.get('ID')) == str(labelID):
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
            
    if (multicast_ip == None or multicast_port == None): 
        raise AssertionError('*ERROR* failed to get multicast address for LabelID %s' % labelID)
    
    return [multicast_ip, multicast_port]        

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
    
    spsText = None
    for labelNode in labelNodes:
        if str(labelNode.get('ID')) == str(labelID):
            providerNodes = labelNode.findall('provider')
            for providerNode in providerNodes:
                if providerNode.get('NAME') == MTE:
                    spsText = providerNode.find('sps').text
                    return spsText
            break
    
    if spsText == None:
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
    if (MANGLINGRULE.has_key(rule.upper()) == False):
        raise AssertionError('*ERROR* (%s) is not a standard name' %rule)
    
    xPath = ['Partitions']
    attribute = {'defaultRule' : MANGLINGRULE[rule.upper()]}
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
    if (MANGLINGRULE.has_key(rule.upper()) == False):
        raise AssertionError('*ERROR* (%s) is not a standard name' %rule)
    
    xPath = ['Partitions','Partition']
    attribute = {'rule' : MANGLINGRULE[rule.upper()]}
    if (len(contextIDs) == 0):
        xmlutilities.set_xml_tag_attributes_value(configFileLocalFullPath,attribute,False,xPath)
    else:
        for contextID in contextIDs:
            add_mangling_rule_partition_node(rule, contextID, configFileLocalFullPath)
            conditions = {'value' : contextID}
            xmlutilities.set_xml_tag_attributes_value_with_conditions(configFileLocalFullPath,conditions,attribute,False,xPath)
            conditions.clear()

def set_value_in_MTE_cfg(mtecfgfile, tagName, value, actionIfNotPresent='add', *tagPath):
    """change tag value in MTE config file
    
        params : mtecfgfile         - full path to local mte config file
                 tagName            - target tagName
                 value              - required value
                 actionIfNotPresent - "skip" : only INFO indicate the tagName not found in config file
                                      "fail" : raise assertion if tagName not found
                                      "add"  " added the tagName to config file (default)
                 tagPath            - path of the section where the tag is located (excluding the tagName)
                                      '*' as last entry in tagPath will search the current node and all subnodes, recursively
                                      only the first tag found will be updated
                
        return : N/A
        
        Examples :
          | set value in_MTE cfg | jsda01.json | NumberOfDailyBackupsToKeep | 5 |
          Would change a config file containing:
            { "Persistence": {
                "DDS": {
                  "NumberOfDailyBackupsToKeep": 3,
                  "MutexNameForStaggering": "HKF_Persistence_Mutex"
                } } }
          To
            { "Persistence": {
                "DDS": {
                  "NumberOfDailyBackupsToKeep": 5,
                  "MutexNameForStaggering": "HKF_Persistence_Mutex"
                } } }
    """
    with open(mtecfgfile) as f:   
        jsonDict = json.load(f)
    _update_config_dict(jsonDict, tagName, value, actionIfNotPresent, *tagPath)
    with open(mtecfgfile, 'w') as f:      
        json.dump(jsonDict, f, sort_keys=True, indent=2, ensure_ascii=True)

def verify_filterString_contains_configured_context_ids(filter_string,venueConfigFile):
    """Get set of context id from FilterString and venue xml_config file
    and verify the context id set defined in Transforms section is equal to the context id set from fms FilterString
    Argument : fms FilterString, venue configuration file
    Returns : true if venueConfig_context_id_set == filterString_context_id_set
    
    Examples:
    | verify filterString contains configured context ids | <FilterString>CONTEXT_ID = 1052 OR CONTEXT_ID = 1053</FilterString> | venue configuration file | 
    """  

    venueConfig_context_id_set = get_context_ids_from_config_file(venueConfigFile)
    if len(venueConfig_context_id_set) == 0:
        raise AssertionError('*ERROR* cannot find venue config context ids define in Transforms section %s' %venueConfigFile)

    filterString_context_id_set = get_context_ids_from_fms_filter_string(filter_string)
    if len(filterString_context_id_set) == 0:
        raise AssertionError('*ERROR* cannot find venue config context ids from fms FilterString %s' %filter_string)

    if venueConfig_context_id_set == filterString_context_id_set:
        return True
    else:
        raise AssertionError('*ERROR* venue context ids define in Transforms section %s is not equal to the context ids from fms FilterString %s' %(venueConfig_context_id_set, filterString_context_id_set))

def _get_matching_values_from_dict(node, tag):
    values = []
    for key,val in node.items():
        if isinstance(val, dict):
            values += _get_matching_values_from_dict(val,tag)
        if key == tag:
            if isinstance(val, list):
                values += val
            else:
                values.append(val)
    return values

def _search_MTE_config_file(venueConfigFile,*path):
    if len(path) < 1:
        raise AssertionError('*ERROR*  Need to provide path to look up.')
        
    if not os.path.exists(venueConfigFile):
        raise AssertionError('*ERROR*  %s is not available' %venueConfigFile)
    
    with open (venueConfigFile, "r") as myfile:
        node = json.load(myfile)
        
    for p in path:
        if p in node:
            node = node[p]
        else:
            return []
    if isinstance(node, list):
         return node
    elif isinstance(node, dict):
        return keys(node)
    else:
        return [node]
    
def _update_config_dict(node, tagName, value, actionIfNotPresent, *tagPath):
    """ Recursive function to update tag values in a JSON dictionary
    """
    if actionIfNotPresent != 'skip' and actionIfNotPresent != 'fail' and actionIfNotPresent != 'add':
        raise AssertionError("*ERROR* Invalid value %s for actionIfNotPresent, valid values are 'skip', 'fail', and 'add'" %actionIfNotPresent)
                       
    tagPath = list(tagPath)
    while len(tagPath):
        t = tagPath.pop(0)
        if t == '*':
            # '*' can mean 0 levels, so check for tag at current level
            if len(tagPath) == 0 and tagName in node:
                break
            if actionIfNotPresent == 'add':
                raise AssertionError('actionIfNotPresent=add is not supported for wildcard nodes (*)')
            foundSubDict = False
            for key,val in node.items():
                # update each sub-node that is a dictionary
                 # '*' at end of tagPath can match any number of levels, so process sub-dictionaries
                if isinstance(val, dict):
                    foundSubDict = True
                    if len(tagPath) == 0:
                        _update_config_dict(val, tagName, value, actionIfNotPresent, '*')
                    else:
                        _update_config_dict(val, tagName, value, actionIfNotPresent, *tagPath)
            if foundSubDict:
                return
            else:
                # at bottom of the tree and tag not found
                break
        elif t in node:
            node = node[t]
        elif actionIfNotPresent == "fail":
            raise AssertionError('Intermediate node %s is missing' %t)
        elif actionIfNotPresent == "skip":
            print '*INFO* Intermediate node %s is missing, tag %s will not be added' %(t, tagName)
            return
        else: # actionIfNotPresent == "add"
            print '*INFO* adding intermediate node %s' %t
            node[t] = {}
            node = node[t]
    
    if tagName in node:
        print '*INFO* updating tag %s with value %s' %(tagName, value)
        node[tagName] = value
    elif actionIfNotPresent == "fail":
        raise AssertionError('Tag %s is missing from node %s' %(tagName, '->'.join(tagPath)))
    elif actionIfNotPresent == "skip":
        print '*INFO* Tag %s is missing from node %s, will not be added'%(tagName, '->'.join(tagPath))
        return
    else: # actionIfNotPresent == "add"
        print '*INFO* adding tag %s with value %s' %(tagName, value)
        node[tagName] = value

#############################################################################
# Keywords that use remote configuration files
#############################################################################

def backup_remote_cfg_file(searchdir,cfgfile,suffix='.backup'):
    """backup config file by create a new copy with filename append with suffix
    Argument : 
    searchdir  : directary where we search for the configuration file
    cfgfile    : configuration filename
    suffix     : suffix used to create the backup filename 
        
    Returns : a list with 1st item = full path config filename and 2nd itme = full path backup filename

    Examples:
    | backup remote cfg file | /ThomsonReuters/Venues | manglingConfiguration.xml |  
    """         
    
    #Find configuration file
    foundfiles = _search_file(searchdir,cfgfile,True)        
    if len(foundfiles) < 1:
        raise AssertionError('*ERROR* %s not found' %cfgfile)
    """elif len(foundfiles) > 1:
        raise AssertionError('*ERROR* Found more than one file: %s' %cfgfile)   """  
            
    #backup config file
    backupfile = foundfiles[0] + suffix
    cmd = "cp -a %s %s"%(foundfiles[0], backupfile)
    stdout, stderr, rc = _exec_command(cmd)
    
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    
    return [foundfiles[0], backupfile]


def Get_CHE_Config_Filepaths(filename, *ignorePathFile):
    """Get file path for specific filename from TD Box.
       Ignore files that contain any of the strings in list variable ignorePathFile
       if ignorePathFile is empty, then SCWatchdog and puppet directories will be ignored during search
     
    Argument: 
        filename : config filename
        ignorePathFile: list of strings to ignore
                 
    Returns: a list of full path of remote configuration files 
 
    Examples:
    | Get CHE Config Filepath | ddnPublishers.xml 
    | Get CHE Config Filepath | *_grs.json | config_grs.json | SCWatchdog
    """  
    if len(ignorePathFile) == 0:
        ignorePathFile = ['/SCWatchdog/', '/puppet/']
    
    ignoreString = ' | grep -v '.join(map(str, ignorePathFile))
    ignoreString = ' | grep -v ' + ignoreString
                       
    cmd = "find " + BASE_DIR + " -type f -name " + filename + "  " + ignoreString
    
    stdout, stderr, rc = _exec_command(cmd)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
     
    return stdout.strip().split()


def get_FID_ID_by_FIDName(fieldName):
    """get FID ID from TRWF2.DAT based on fidName
    
    fieldName is the FID Name. For example BID, ASK
    return the corresponding FID ID

    Examples:
    |get FID ID by FIDName | ASK |     
    """
    
    filelist = LinuxFSUtilities().search_remote_files(BASE_DIR, 'TRWF2.DAT',True)
    if (len(filelist) == 0):
        raise AssertionError('no file is found, can not located the field ID')
    
    #sed 's/\"[^\"]*\"/ /' %s remove the string which begins with symbol " and end with symbol ", 
    #for example in file /reuters/Config/TRWF2.DAT, remove the 2nd column
    #tr -s ' ' remove repeat symbol ' '(space)
    cmd = "sed 's/\"[^\"]*\"/ /' %s | grep \"^%s \" | tr -s ' '" %(filelist[0],fieldName)
    
    stdout, stderr, rc = _exec_command(cmd)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))  
    
    elements = stdout.split()
    
    if (len(elements) > 2 ):
        return elements[1]
    else:
        raise AssertionError('*ERROR* The FID can not be found')        

def get_FID_Name_by_FIDId(FidId):
    """get FID Name from TRWF2.DAT based on fidID
    
    fidID is the FID ID number. For example 22
    return the corresponding FID Name

    Examples:
    |get FID Name by FIDId | 22 |     
    """
    
    filelist = LinuxFSUtilities().search_remote_files(BASE_DIR, 'TRWF2.DAT',True)
    if (len(filelist) == 0):
        raise AssertionError('no file is found, can not located the field ID')
    
    
    #sed -e '/^!/d' %s | sed 's/\"[^\"]*\"/ /'    the command is to remove the comments which begins with symbol ! 
    #and remove the string beginning with " and ending with ", for example in file /reuters/Config/TRWF2.DAT, the 2nd column
        #tr -s ' '  it is to remove repeat symbol ' '(space)
        #cut -d ' ' f1,2  Use symbol ' '(space) as delimiter to split the line and delete the filed f1 and f2
        cmd = "sed -e '/^!/d' %s | sed 's/\"[^\"]*\"/ /' | grep \" %s \" | tr -s ' ' | cut -d ' ' -f1,2 | grep \" %s$\""%(filelist[0],FidId,FidId)
    
        stdout, stderr, rc = _exec_command(cmd)
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))  
        
        elements = stdout.split()
        
        if (len(elements) == 2 ):
            return elements[0]
        else:
            raise AssertionError('*ERROR* The FID can not be found')

def restore_remote_cfg_file(cfgfile,backupfile):
    """restore config file by rename backupfile to cfgfile
    Argument : 
    cfgfile    : full path of configuration file
    backupfile : full path of backup file
        
    Returns : Nil

    Examples:
    | restore remote cfg file | /reuters/Venues/HKF/MTE/manglingConfiguration.xml | /reuters/Venues/HKF/MTE/manglingConfiguration.xml.backup |  
    """       
    
    LinuxFSUtilities().remote_file_should_exist(cfgfile)
    LinuxFSUtilities().remote_file_should_exist(backupfile)
    
    #restore config file
    cmd = "mv -f %s %s"%(backupfile,cfgfile)
    stdout, stderr, rc = _exec_command(cmd)
    
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))                

