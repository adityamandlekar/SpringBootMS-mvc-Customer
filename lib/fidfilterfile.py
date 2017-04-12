from __future__ import with_statement
import os
import os.path
import re

from VenueVariables import *
        
def get_constituents_from_FidFilter(context_id):
    """ 
    Argument : 
        context_id : Context ID
    Return : constituent list which contains unique constituents defined in venue FidFilter.txt file for the context_id
    """ 
    fidfilter = parse_local_fidfilter_file()
    if (fidfilter.has_key(context_id) == False):
        raise AssertionError('*ERROR* Context ID %s does not exist in FIDFilter.txt file' %(context_id))  
    
    fidDic = fidfilter[context_id]
    if len(fidDic.keys()) == 0:
        raise AssertionError('*ERROR* No FID dictionary exists in FIDFilter.txt file for Context ID %s' %(context_id))  
    
    return fidDic.keys()
 
def parse_local_fidfilter_file():
    """Get context ID, FIDs and Constituent from the local copy of FIDFilter.txt.
    FIDFilter.txt must be copied to LOCAL_TMP_DIR before calling this Keyword.
    Argument : NIL
    Returns : Dictionary of FIDFilter [contextID][constituent][fid]='1'

    Examples:
    | parse local fidfilter file |
     """    
                    
    constitWithFIDs = {} #dictionary with key=contituent number and content=array of FIDs
    contextIdsMap = {} #dictionary with key=contextID and content=map of constit with FIDs
    
    localFidFilterFile = LOCAL_TMP_DIR + '\\FIDFilter.txt'
    if not os.path.exists(localFidFilterFile):
        raise AssertionError('*ERROR* File does not exist: %s' %localFidFilterFile)
    
    with open(localFidFilterFile, "r") as myfile:
        linesRead = myfile.readlines()
    
    contextID = ""
    for line in linesRead:
        line = line.strip()
        if (len(line) > 0 and line[0] != '!'):
            content = line.split(':')
            if (len(content) == 2):
                if (content[0].find('LIST NUMBER') != -1):
                    
                    #Before roll to next context ID, save the FID List to previous found context ID
                    if (len(constitWithFIDs) > 0):
                        contextIdsMap[contextID] = dict(constitWithFIDs)
                    
                    #Get the new context ID
                    contextID = content[1].strip()
                    
                    #Prepare a new FID list Map for context ID
                    contextIdsMap[contextID] = {}
                    
                    #clear constitWithFIDs Map
                    constitWithFIDs.clear()
                    
            else:
                content = line.split()
                if (len(content) >= 2):
                    fid = content[0]
                    constit = content[1]
                    if re.match(r'-?\d+$',fid) and re.match(r'-?\d+$',constit):
                        if (constitWithFIDs.has_key(constit) == False):
                            constitWithFIDs[constit] = {}
                        constitWithFIDs[constit][fid]='1'
                    else:
                        if (len(contextID) > 0):
                            raise AssertionError('*ERROR* %s has non-integer value found'%line)
                        else:
                            raise AssertionError('*ERROR* empty context ID found in FIDFilter.txt')
       
    if (len(constitWithFIDs) > 0):
        contextIdsMap[contextID] = dict(constitWithFIDs)
    
    #post checking
    if (len(contextIdsMap) == 0):
        raise AssertionError('*ERROR* Fail to retrieve FIDFilter.txt information') 

    return contextIdsMap

def get_contextID_from_FidFilter():
    fidfilter = parse_local_fidfilter_file()
    return fidfilter.keys()	
	
def verify_fidfilter_contains_SHELL_MDAT(contextIdsWithSHELL):
    """ Check if the SHELL RIC for the contextIDs has a contstituent of 0
    Argument : The Dictionary that contains the context ID, FIDs and Constituents
    Returns : Nil
    
    Examples:
    | verify_fidfilter_contains_SHELL_MDAT | ${shellCount} |
    """
    ret=parse_local_fidfilter_file()
    for contextID in ret.keys():
        if contextID in contextIdsWithSHELL:
            for constit in ret[contextID]:
                if constit == "0":
                    if '6632' not in ret[contextID][constit]:
                        raise AssertionError('*ERROR* "SHELL_MDAT FID (6632) does not exist in FIDFilter for contextID %s"',contextID)
                else:
                    if '6632' in ret[contextID][constit]:
                        raise AssertionError('*ERROR* "SHELL_MDAT FID (6632) exists for constituent %s in FIDFilter for contextID %s.  It should be in constituent 0.', contextID)
