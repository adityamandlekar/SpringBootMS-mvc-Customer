import string

from utils.local import _run_local_command
from VenueVariables import *
    
def map_to_PMAT_numeric_domain(domain):
    ''' Map string domain to PMAT numeric domain
        Argument : domain : Data domain in following format
                            MarketByOrder, MarketByPrice, MarketMaker, MarketPrice, symbolList.
        Return : 0 for MarketByOrder, 1 for MarketByPrice, 2 for MarketMaker, 3 for MarketPrice, 4 for symbolList.
    ''' 
    domainDict = {'MARKETBYORDER': 0, 'MARKETBYPRICE': 1, 'MARKETMAKER': 2, 'MARKETPRICE': 3, 'SYMBOLList':4}
    domainUpper = domain.upper()
    ret = domainDict[domainUpper]
    if not (ret >= 0 and ret <=4):
        raise AssertionError('*ERROR* invalid domain %s for PMAT' %domain)
    
    return ret
    
    
def run_PMAT(action,*params):    
    ''' Call PMAT.exe  
        PMAT doc is available at https://thehub.thomsonreuters.com/docs/DOC-110727
        Argument : action : possible values are Dump, Drop, Modify, Upgrade, Insert
                   params : a variable list of  arguments based on action.
        Return : rc should be 0.  
        examples : | ${ret}= | run PMAT| dump | --dll Schema_v6.dll | --db local_persist_file.DAT | --ric AAAAX.O | --domain 3 | --outf c:/tmp/pmat_dump.xml |
                   | ${ret}= | run PMAT| drop | --dll Schema_v5.dll | --db local_persist_file.DAT | --id 2 |
                   | ${ret}= | run PMAT| upgrade | --dll upgrade_Schema_v5.Schema_v6.dll | --db c:\PERSIST_CXA_V5.DAT | --newdb c:\PERSIST_CXA_V6.DAT
                   | ${ret}= | run PMAT| modify | --dll <modify dll> | --db <database file> | --xml <xml command file>
    '''
    #output_file = 'pmat_dump.txt'
    #cmdstr = 'pmat dump --dll Schema_v6.dll --db %s --ric %s --domain %d --outf %s'%(local_persist_file, ric, domain_no, output_file)
    
    cmd = 'PMAT %s' %action
    cmd = cmd + ' ' + ' '.join(map(str, params))

    rc,stdout,stderr  = _run_local_command(cmd, True, LOCAL_PMAT_DIR)
    if rc != 0:
        raise AssertionError('*ERROR* in running PMAT %s' %stderr)  
    
    return rc
