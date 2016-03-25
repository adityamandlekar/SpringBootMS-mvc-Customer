from LinuxToolUtilities import LinuxToolUtilities   
        
def get_constituents_from_FidFilter(context_id):
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
