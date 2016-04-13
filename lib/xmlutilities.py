from __future__ import with_statement
import os
import os.path
from sets import Set
import string
import xml
import xml.etree.ElementTree as ET

def get_all_fid_names_from_xml(xmlfile):
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

def load_xml_file(xmlFileLocalFullPath,isNonStandardXml):
    """load xml file into cache and get the iterator point to first element
    
    xmlFileLocalFullPath : full path of xml file
    isNonStandardXml : indicate if the xml file is non-standard one or not
    Returns : iterator point to the first element of the xml file
    """                
    if not os.path.exists(xmlFileLocalFullPath):
        raise AssertionError('*ERROR* File does not exist: %s' %xmlFileLocalFullPath)
    
    if (isNonStandardXml):
        with open(xmlFileLocalFullPath, "r") as myfile:
            linesRead = myfile.readlines()

        # Note that the following workaround is needed to make the venue config file a valid XML file.
        linesRead = "<GATS>" + ''.join(linesRead) + "</GATS>"
    
        root = ET.fromstring(linesRead)
    else:
        tree = ET.parse(xmlFileLocalFullPath)
        root = tree.getroot()                    
    return root

def save_to_xml_file(root,xmlFileLocalFullPath,isNonStandardXml):
    """Save xml content from cache to file
    
    xmlFileLocalFullPath : full path of xml file
    isNonStandardXml : indicate if the xml file is non-standard one or not
    Returns : Nil
    """         
    if (isNonStandardXml):
        with open(xmlFileLocalFullPath, "w") as myfile:
            for child in root:
                myfile.write(ET.tostring(child))                                            
    else:
        ET.ElementTree(root).write(xmlFileLocalFullPath)

def set_xml_tag_attributes_value(xmlFileLocalFullPath,attributes,isNonStandardXml,xPath):
    """set attribute of a tag in xml file specficied by xPath
    
    xmlFileLocalFullPath : full path of xml file
    attributes : a map specific the attributes(key) and correpsonding value
    isNonStandardXml : indicate if xml file is non-starndard (e.g. MTE venue config xml file)
    xPath : a list contain the xPath for the node
    Returns : Nil
    """        
    root = load_xml_file(xmlFileLocalFullPath,isNonStandardXml)        
    nodes = _get_xml_node_by_xPath(root, xPath)
    
    for node in nodes:
        for key in attributes.keys():
            node.set(key,attributes[key])
            
    save_to_xml_file(root,xmlFileLocalFullPath,isNonStandardXml)

def set_xml_tag_attributes_value_with_conditions(xmlFileLocalFullPath,conditions,attributes,isNonStandardXml,xPath):
    """set attribute of a tag in xml file specficied by xPath and tag matching conditions
    
    xmlFileLocalFullPath : full path of xml file
    conditions : a map specific the attributes(key) and correpsonding value that need to be matched before carried out "set" action
    attributes : a map specific the attributes(key) and correpsonding value
    isNonStandardXml : indicate if xml file is non-starndard (e.g. MTE venue config xml file)
    xPath : a list contain the xPath for the node
    Returns : Nil
    """        
    root = load_xml_file(xmlFileLocalFullPath,isNonStandardXml)        
    nodes = _get_xml_node_by_xPath(root, xPath)
    
    foundMatch = False
    for node in nodes:
        isMatched = True
        for key in conditions.keys():
            attrib_val = node.get(key)
            if (attrib_val == None or attrib_val != conditions[key]):
                isMatched = False
                break
        
        if (isMatched):
            foundMatch = True
            for key in attributes.keys():
                node.set(key,attributes[key])
    
    if not (foundMatch):
        raise AssertionError('*ERROR*  No match found for given xPath (%s) and conditions (%s) in %s'%(xPath,conditions,xmlFileLocalFullPath))
            
    save_to_xml_file(root,xmlFileLocalFullPath,isNonStandardXml)

def set_xml_tag_value(xmlFileLocalFullPath,tagValue,isNonStandardXml,xPath):
    """set tag value in xml file specficied by xPath
    
    xmlFileLocalFullPath : full path of xml file
    tagValue : target tag value
    isNonStandardXml : indicate if xml file is non-starndard (e.g. MTE venue config xml file)
    xPath : a list contain the xPath for the node
    Returns : Nil
    """
    root = load_xml_file(xmlFileLocalFullPath,isNonStandardXml)
    nodes = _get_xml_node_by_xPath(root, xPath)
    for node in nodes:
        node.text=str(tagValue)
    
    save_to_xml_file(root,xmlFileLocalFullPath,isNonStandardXml)

def xml_parse_get_all_elements_by_name (xmlfile,tagName):
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

def xml_parse_get_fidsAndValues_for_messageNode (messageNode):
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

def xml_parse_get_field_for_messageNode (messageNode,fieldName):
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

def xml_parse_get_field_from_MsgKey(messageNode, fieldName):
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

def xml_parse_get_HeaderTag_Value_for_messageNode (messageNode,headerTag,fieldName):
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
        |xml_parse_get_HeaderTag_Value_for_messageNode | Message[0] | MsgBase | ContainerType |
    """           
    for fieldEntry in messageNode.getiterator(headerTag):
        foundfield = fieldEntry.find(fieldName)
        if (foundfield != None):                   
            return foundfield.attrib['value']

    raise AssertionError('*ERROR* Missing %s'%(headerTag))

def _get_xml_node_by_xPath(root,xPath):
    """get xml node by xPath
    
    root : object return from calling tree.getroot() while tree = ET.parse(file.xml)
    xPath : a list contain the xPath for the node
    Returns : iterator for 'ALL' elements that matched with xPath
    """
    xmlPathLength = len(xPath)
    if xmlPathLength < 1:
        raise AssertionError('*ERROR*  Need to provide xPath to look up.')
    elif xmlPathLength > 1:
        xmlPathString = '/'.join(map(str, xPath))
    else:
        xmlPathString = str(xPath[0])
    
    return root.iterfind(".//" + xmlPathString) 
