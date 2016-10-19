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

def get_xml_text_for_node(xmlFile,*xmlPath):
    """Get the text values for the specified XML node
    
    xmlFile: full path to the local xml file
    xmlPath: a list defining the XML path for the node to use
    Returns a list of values associated with the node
    
    Example:
    | Get XML Text For Node | ${LOCAL_TMP_DIR}${/}CritProcMon.xml | CriticalProcessses |
    """
    foundValues = []
    
    xmlPathLength = len(xmlPath)
    if xmlPathLength < 1:
        raise AssertionError('*ERROR*  Need to provide xmlPath to look up.')
    elif xmlPathLength > 1:
        xmlPathString = '/'.join(map(str, xmlPath))
    else:
        xmlPathString = str(xmlPath[0])
        
    if not os.path.exists(xmlFile):
        raise AssertionError('*ERROR*  %s is not available' %xmlFile)
    
    with open (xmlFile, "r") as myfile:
        linesRead = myfile.readlines()

    # Note that the following workaround is needed to make the venue config file a valid XML file.
    if linesRead[0].startswith('<?xml'):
        linesReadString = ''.join(linesRead)
    else:
        linesReadString = "<GATS>" + ''.join(linesRead) + "</GATS>"
    
    root = ET.fromstring(linesReadString)
    
    for foundNode in root.iterfind(".//" + xmlPathString):
        for text in foundNode.itertext():
            strippedText = text.strip()
            if strippedText:
                    foundValues.append(strippedText)
        
    return foundValues

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

def set_xml_tag_value(xmlFileLocalFullPath, xPath, tagValue, tagAttributes=None,  isNonStandardXml=False, addTagIfNotExist=True):
    """set tag value in xml file specified by xPath
    
    xmlFileLocalFullPath : full path of xml file
    xPath : a list contain the xPath for the node
    tagValue : target tag value
    tagAttributes : target tag attributes string value (e.g. "type=\"ul\""). 
                    This is only use if addTagIfNotExist is True, and for node creation in the leaf node if the xPath not exist, not for searching. 
    isNonStandardXml : indicate if xml file is non-standard (e.g. MTE venue config xml file)
    addTagIfNotExist: If addTagIfNotExist is True, add the non-exists nodes; else assert if the tag is not found. 

    Returns : Nil
    """
    if (tagAttributes == None):
        tagAttributes = ""

    lenOfxPathList = len(xPath)
    if (lenOfxPathList <= 0):
         raise AssertionError('*ERROR* the input paramater xPath list is empty')

    root = load_xml_file(xmlFileLocalFullPath,isNonStandardXml)
    currentNode = root
    insertedNodePos = None
    foundLeafNode = False
    insertPrefixNodeStr = ""
    insertSuffixNodeStr = ""
    i = -1

    for tag in xPath:
        i += 1
        if (insertedNodePos == None):
            nodes = currentNode.find("./" + tag)
        
        if (nodes == None):
            if (not addTagIfNotExist):
                break

            if (insertedNodePos == None):
                insertedNodePos = currentNode
            if (i == lenOfxPathList - 1):
                insertPrefixNodeStr = insertPrefixNodeStr + "<" + tag + " " + tagAttributes + " >" + tagValue
            else:
                insertPrefixNodeStr = insertPrefixNodeStr + "<" + tag + ">"
            insertSuffixNodeStr = "</" + tag + ">\n" + insertSuffixNodeStr
        else:
            if (i == lenOfxPathList - 1):
                #found the leaf node and change the value
                nodes.text = str(tagValue)
                foundLeafNode = True
            else:
                #continue loop for next node
                currentNode = nodes

    if (insertedNodePos != None):
            insertedNodePos.append(ET.fromstring(insertPrefixNodeStr + insertSuffixNodeStr))
    elif (not foundLeafNode):
        raise AssertionError('*ERROR* The node of xPath=%s is not found in %s' %(xPath,xmlFileLocalFullPath))

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

def xml_parse_get_fidsAndTypeAndValues_for_messageNode (messageNode):
    """ get FIDs and corresponding data type and value from a message node
        messageNode : iterator pointing to one message node
        return : dictionary of FIDs and corresponding list of data type and value (key=FID no.; value=list of [dataType, value])
        Assertion : NIL
    """

    fidsDictTypeAndValueList= {}
    for fieldEntry in messageNode.getiterator('FieldEntry'):
        fieldId = fieldEntry.find('FieldID')
        fieldType = fieldEntry.find('DataType')
        fieldValue = fieldEntry.find('Data')
        
        if (fieldId != None):
            fieldIdNum = fieldId.attrib['value']
            fidsDictTypeAndValueList[fieldIdNum] = []

            fieldType = 'NoData' if fieldType == None else fieldType.attrib['value']
            fieldValue = 'NoData' if fieldValue == None else fieldValue.attrib['value']
            fidsDictTypeAndValueList[fieldIdNum].append(fieldType)
            fidsDictTypeAndValueList[fieldIdNum].append(fieldValue)
        
    return fidsDictTypeAndValueList

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
