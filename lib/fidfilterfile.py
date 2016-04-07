import re

import fidfilterfile
from utils.ssh import _exec_command

from VenueVariables import *
        
def get_constituents_from_FidFilter(context_id):
    """ 
        Return : constituent list which contains unique constituents defined in venue FidFilter.txt file for the context_id
    """ 
    fidfilter = fidfilterfile.get_contextId_fids_constit_from_fidfiltertxt()
    if (fidfilter.has_key(context_id) == False):
        raise AssertionError('*ERROR* Context ID %s does not exist in FIDFilter.txt file' %(context_id))  
    
    fidDic = fidfilter[context_id]
    if len(fidDic.keys()) == 0:
        raise AssertionError('*ERROR* No FID dictionary exists in FIDFilter.txt file for Context ID %s' %(context_id))  
    
    return fidDic.keys()
    
def get_contextId_fids_constit_from_fidfiltertxt():
    """Get context ID, FIDs and Constituent from FIDFilter.txt
    Argument : NIL
    Returns : Dictionary of FIDFilter [contextID][constituent][fid]='1'

    Examples:
    | get contextId fids constit from fidfiltertxt
     """    
                    
    constitWithFIDs = {} #dictionary with key=contituent number and content=array of FIDs
    contextIdsMap = {} #dictionary with key=contextID and content=map of constit with FIDs
    
    cmd = 'cat `find ' + VENUE_DIR + ' -name FIDFilter.txt`'
    stdout, stderr, rc = _exec_command(cmd)
    
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))  
    
    lines = stdout.split('\n')
    
    contextID = ""
    for line in lines:
        if (len(line.strip()) > 0 and line.strip()[0] != '!'):
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
                if (len(content) == 2):
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
    fidfilter = get_contextId_fids_constit_from_fidfiltertxt()
    return fidfilter.keys()