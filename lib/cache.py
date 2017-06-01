from __future__ import with_statement
import os
import os.path
from sets import Set
import string

import CHEprocess
import configfiles
from LinuxCoreUtilities import LinuxCoreUtilities
from LinuxFSUtilities import LinuxFSUtilities
from utils.ssh import _exec_command, _delete_file

from VenueVariables import *

#############################################################################
# Keywords that use local copy of MTE cache file
#############################################################################
    
def get_context_ids_from_cachedump(cachedump_file_name):  
    """Returns a set of context_ids appeared in the cachedump.csv file.
     Argument : cache dump file full path
     Return: Returns a list context Ids

    Examples:
    | get context ids from cachedump | cachedump file name |     
    """    
    if not os.path.exists(cachedump_file_name):
        raise AssertionError('*ERROR*  %s is not available' %cachedump_file_name)
        
    context_id_val_set = Set()
    n = 0
    context_id_idx = -1
    try:
        with open(cachedump_file_name) as fileobj:
            for line in fileobj:
                n = n+1
                if n==1:
                    context_id_val = line.split(",")
                    context_id_idx = context_id_val.index("CONTEXT_ID")
                if n>1:
                    context_id_val = line.split(",")[context_id_idx]
                    if context_id_val:
                        context_id_val_set.add(context_id_val)
                        
    except IOError:
        raise AssertionError('*ERROR* failed to open file %s' %cachedump_file_name) 
    except IndexError:
        raise AssertionError('*ERROR* [CONTEXT_ID] column not found in cachedump file')
                
    return context_id_val_set   

def verify_cache_contains_only_configured_context_ids(cachedump_file_name_full_path,venueConfigFile): 
    """Get set of context ID from cache dump file and venue xml_config file
    and verify the context id set from cache dump is subset of context id set defined in Transforms section
    Argument : cachedump file, venue configuration file
    Returns : true if dumpcache_context_ids_set <= venueConfig_context_id_set
    
    Examples:
    | verify cache contains only configured context ids | cache dump file |venue configuration file   
    """       

    venueConfig_context_id_set = configfiles.get_context_ids_from_config_file(venueConfigFile)
    if len(venueConfig_context_id_set) == 0:
        raise AssertionError('*ERROR* cannot find venue config context ids in %s' %venueConfigFile)

    dumpcache_context_ids_set = get_context_ids_from_cachedump(cachedump_file_name_full_path)
    if len(dumpcache_context_ids_set) == 0:
        raise AssertionError('*ERROR* cannot found dumpcache context ids in %s' %cachedump_file_name_full_path)
    
    if dumpcache_context_ids_set <= venueConfig_context_id_set:
        return True
    else:
        raise AssertionError('*ERROR* dumpcache context ids %s are not all in configured context ids %s' %(dumpcache_context_ids_set, venueConfig_context_id_set))

def verify_csv_files_match(file1, file2, ignorefids):
    """Verify two .csv files match.

    Argument ignorefids is a comma separated list of fields to ignore.
    If it is used, the first line of file must contain the field names.
    Those columns will be excluded during the comparision.
    
    Does not return a value; raises an error if any differences are found.

    Examples:
    | Verify csv Files Match  | file1  | file2  | ignorefids=CURR_SEQ_NUM,LAST_UPDATED  |
    | Verify csv Files Match  | file1  | file2  | CURR_SEQ_NUM,LAST_UPDATED             |
    """
    fileobj1= open(file1,'r')
    lines1 = fileobj1.readlines()
    fileobj1.close()
    fileobj2= open(file2,'r')
    lines2 = fileobj2.readlines()
    fileobj2.close()
    ignorelist = ignorefids.split(',')
    ignorepositions = []
    if lines1[0].find(ignorelist[0])!=-1:
        # rstrip to remove newline
        itemslist = lines1[0].rstrip().split(',')
        for item in itemslist:
            if item in ignorelist:
                ignorepositions.append(itemslist.index(item))
    else:
        ignorepositions = ignorelist
    print '*INFO* ignoring columns %s' %ignorepositions
    
    count = 0
    NotMatchlines =[]
    if len(lines1) != len(lines2):
        raise AssertionError('*ERROR* line count differs %s:%s' %(len(lines1),len(lines2)))
    
    while count < len(lines1) and count < len(lines2):
        items1 = lines1[count].split(',')
        items2 = lines2[count].split(',')
        if len(items1) != len(items2):
            NotMatchlines.append([lines1[count],lines2[count]])
        else:
            for idx in range(len(items1)):
                if idx not in ignorepositions and items1[idx] != items2[idx]:
                    NotMatchlines.append([lines1[count],lines2[count]])
                    break
        count = count+1
    
    if len(NotMatchlines)!=0:
        raise AssertionError('*ERROR* %s lines are different' %len(NotMatchlines))
    else:
        print '*INFO* the files are identical'

#############################################################################
# Keywords that use remote MTE cache file
#############################################################################

def dump_cache(waittime=2, timeout=60):
    """Dump the MTE cache to a file (on the MTE machine).
    
    Returns the full path name to the dumped file.

    Examples:
    | Dump Cache  | 
    | Dump Cache  | 10 | 60 |
    """
    stdout = CHEprocess.run_commander('linehandler', 'lhcommand %s dumpcache' %MTE)
    if stdout.lower().find('successfully processed command:') == -1:
        raise AssertionError('*ERROR* dumpcache %s failed, %s' %(MTE,stdout))
    
    # get path to the cache file
    today = LinuxCoreUtilities().get_date_and_time()
    filename = '%s_%s%s%s.csv' %(MTE, today[0], today[1], today[2])
    foundfiles = LinuxFSUtilities().wait_for_search_file(VENUE_DIR,filename,waittime,timeout)
    if len(foundfiles) > 1:
        raise AssertionError('*ERROR* Found more than one cache file: %s' %foundfiles)
    print '*INFO* cache file is %s' %foundfiles[0]
    LinuxFSUtilities().wait_for_file_write(foundfiles[0],waittime,timeout)
    return foundfiles[0]

def get_all_fields_for_ric_from_cache(ric,domain):
    """Get the field values from the MTE cache for the specifed RIC.

    Arguments:
        ric:   RIC name
        domain: domain of RIC
     
    Returns a dictionary containing all fields for the RIC.  Returns empty dictionary if RIC not found.

    Example:
    | get random RICs from cache  | TESTRIC |
    """
    cacheFile = dump_cache()
     
    # create hash of header values
    cmd = "head -1 %s | tr ',' '\n'" %cacheFile
    stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, stdout=%s stderr=%s' %(cmd,rc,stdout,stderr)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    ricCol      = 0
    domainCol   = 0
    header = stdout.strip().split()
    for i in range(0, len(header)):
        if header[i] == 'RIC':
            ricCol = i+1 # for awk, col numbers start at 1, so add 1 to index
            if (domainCol > 0):
                break
        if header[i] == 'DOMAIN':
            domainCol = i+1 # for awk, col numbers start at 1, so add 1 to index
            if (ricCol > 0):
                break

    if not ricCol:
        raise AssertionError('*ERROR* Did not find required column name in cache file (RIC)')

    if not domainCol:
        raise AssertionError('*ERROR* Did not find required column name in cache file (DOMAIN)')
     
    # get all fields for the RIC
    if (domain == ''):
        cmd = "awk -F',' '$%d == \"%s\" {print}' %s" %(ricCol, ric, cacheFile)
    else:
        domainConverted = _convert_domain_to_cache_format(domain)
        cmd = "awk -F',' '$%d == \"%s\" && $%d == \"%s\" {print}' %s" %(ricCol, ric, domainCol, domainConverted, cacheFile)
    print '*INFO* cmd=%s' %cmd
    stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, stdout=%s stderr=%s' %(cmd,rc,stdout,stderr)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    rows = stdout.strip().split('\n')
    if len(rows) > 1:
        raise AssertionError('*ERROR* Multiple rows found for RIC %s rows.  %s' %(ric,rows))
    
    # put fields into dictionary
    values = rows[0].split(',')
    if len(values) <= 1:
        return {}
    if len(values) != len(header):
        raise AssertionError('*ERROR* Number of values (%d) does not match number of headers (%d)' %(len(values), len(header)))
    valuesToReturn = {}
    for i in range(0, len(values)):
            valuesToReturn[header[i]] = values[i]
     
    _delete_file(cacheFile,'',False)
    return valuesToReturn

def get_count_of_SHELL_RICs():
    """Returns a dictionary with Key : Context IDs and Values: the number of SHELL_RICs
    Examples:
    | get_count_of_SHELL_RICs |
    """
    cacheFile = dump_cache()
    fieldDict ={}
    
    # create hash of header values
    cmd = "head -1 %s | tr ',' '\n'" %cacheFile
    stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, stdout=%s stderr=%s' %(cmd,rc,stdout,stderr)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))    

    headerList = stdout.strip().split()
    index = 1;
    headerDict = {}
    for fieldName in headerList:
        headerDict[fieldName] = index
        index += 1
    if not headerDict.has_key('HAS_SHELL_DATA'):
        raise AssertionError('*ERROR* Did not find HAS_SHELL_DATA column in cache file')
    
    #Verify if HAS_SHELL_DATA column has 'True' values
    ShellCol = headerDict['HAS_SHELL_DATA']
    contextIdCol = headerDict['CONTEXT_ID'] - 1
    cmd = "grep -v TEST %s | awk -F',' '($%s == \"TRUE\") {print}' " %(cacheFile, ShellCol)
    print '*INFO* cmd=%s' %cmd
    stdout, stderr, rc = _exec_command(cmd)
    if rc == 1:
        print '*INFO* HAS NO SHELL DATA'
        return fieldDict
    if rc > 1 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    rows = stdout.splitlines()
	 
    # get the requested fields    
    for row in rows:
        values = row.split(',')
        if len(values) != len(headerList):
            raise AssertionError('*ERROR* Number of values (%d) does not match number of headers (%d)' %(len(values), len(headerList)))
        cid = values[contextIdCol]
        fieldDict[cid] = fieldDict.get(cid,0) + 1       
    _delete_file(cacheFile,'',False)
    return fieldDict
	
def get_otf_rics_from_cahce(domain):
    """Checking how many otf item found in MTE cache dump
    
    Returns a list of dictionaries for OTF items (within each dictionary, it has RIC, DOMAIN, PUBLISH_KEY, OTF_STATUS fields)

    Examples:
    | get otf rics from cache  | MARKET_BY_PRICE 
    """

    if domain:
        newDomain = _convert_domain_to_cache_format(domain)
        
    cacheFile = dump_cache()
    # create hash of header values
    cmd = "head -1 %s | tr ',' '\n'" %cacheFile
    stdout, stderr, rc = _exec_command(cmd)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))

    headerList = stdout.strip().split()
    index = 1;
    headerDict = {}
    for fieldName in headerList:
        headerDict[fieldName] = index
        index += 1
    if not headerDict.has_key('DOMAIN'):
        raise AssertionError('*ERROR* Did not find required column names in cache file (DOMAIN)')

    # get all fields for selected RICs
    domainCol = headerDict['DOMAIN']
    otfCol = headerDict['OTF_STATUS']
    
    cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && ($%d == \"FULL_OTF\" || $%d == \"PARTIAL_OTF\") {print}' " %(cacheFile, domainCol, newDomain, otfCol, otfCol)
    print '*INFO* cmd=%s' %cmd
    stdout, stderr, rc = _exec_command(cmd)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))

    rows = stdout.splitlines()
            
    # get the requested fields
    result = []
    for row in rows:
        values = row.split(',')
        
        if len(values) != len(headerList):
            raise AssertionError('*ERROR* Number of values (%d) does not match number of headers (%d)' %(len(values), len(headerList)))
        
        fieldDict = {}
        for i in range(0, len(values)):
            if headerList[i] == 'DOMAIN':
                newdomain = _convert_cachedomain_to_normal_format(values[i]) 
                fieldDict[headerList[i]] = newdomain
            elif (headerList[i] == 'RIC' or headerList[i] == 'PUBLISH_KEY' or headerList[i] == 'OTF_STATUS'):
                fieldDict[headerList[i]] = values[i]
           
        result.append(fieldDict)
              
    _delete_file(cacheFile,'',False)

    return result       

def get_ric_fields_from_cache(numrows, domain, contextID):
    """Get the first n rows' ric fields data for the specified domain or/and contextID from MTE cache.
    Ignore RICs that contain 'TEST' and non-publishable RICs.
    Returns an array of dictionary containing all fields for the match.  Returns empty dictionary if match are not found

    Arguments:
        numrows:   number of rows to return
        domain:    RIC must belong to this domain if domain is not NONE
        contextID: RIC must belong to this contextID if contextID is not NONE
                   If domain and contextID are NONE, first PUBLISHABLE=TRUE will be checked
                
    Returns an array of dictionaries containing fields for each RICs.
    E.g. [ {RIC : ric1, SIC sic1, DOMAIN MarketPrice, CONTEXT_ID : 1052 ...}, {RIC : ric2, SIC sic2, DOMAIN MarketPrice, CONTEXT_ID : 1052 ...} ]

    Example:
    | get_ric_fields_from_cache  | 1 | MARKET_PRICE |
    | get_ric_fields_from_cache  | 1 | ${EMPTY} | 1052 |
    | get_ric_fields_from_cache  | 2 | MARKET_PRICE | 1052 |
    | get_ric_fields_from_cache  | 2 |
    """
    if numrows != 'all':
        numrows = int(numrows)
        
    if domain:
        newDomain = _convert_domain_to_cache_format(domain)
        
    cacheFile = dump_cache()
    # create hash of header values
    cmd = "head -1 %s | tr ',' '\n'" %cacheFile
    stdout, stderr, rc = _exec_command(cmd)
#         print 'DEBUG cmd=%s, rc=%s, stdout=%s stderr=%s' %(cmd,rc,stdout,stderr)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    
    headerList = stdout.strip().split()
    index = 1;
    headerDict = {}
    for fieldName in headerList:
        headerDict[fieldName] = index
        index += 1
    if not headerDict.has_key('DOMAIN') or not headerDict.has_key('PUBLISHABLE') or not headerDict.has_key('CONTEXT_ID'):
        raise AssertionError('*ERROR* Did not find required column names in cache file (DOMAIN, PUBLISHABLE, CONTEXT_ID') 
    
    # get all fields for selected RICs
    domainCol = headerDict['DOMAIN']
    publishableCol = headerDict['PUBLISHABLE']
    contextIDCol = headerDict['CONTEXT_ID']
    
    if contextID and domain:
        if numrows == 'all':
            cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && $%d == \"TRUE\" && $%d == \"%s\" {print}'" %(cacheFile, domainCol, newDomain, publishableCol, contextIDCol, contextID)
        else:
            cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && $%d == \"TRUE\" && $%d == \"%s\" {print}' | head -%d" %(cacheFile, domainCol, newDomain, publishableCol, contextIDCol,contextID, numrows)
            
    elif  domain: 
        if numrows == 'all':
            cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && $%d == \"TRUE\" {print}'" %(cacheFile, domainCol, newDomain, publishableCol)
        else:
            cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && $%d == \"TRUE\" {print}' | head -%d" %(cacheFile, domainCol, newDomain, publishableCol, numrows)
            
    elif  contextID:
        if numrows == 'all':
            cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && $%d == \"TRUE\" {print}'" %(cacheFile, contextIDCol, contextID, publishableCol)
        else:
            cmd = "grep -v TEST %s | awk -F',' '$%d == \"%s\" && $%d == \"TRUE\" {print}' | head -%d" %(cacheFile, contextIDCol, contextID, publishableCol, numrows)
            
    else:
        if numrows == 'all':
            cmd = "grep -v TEST %s | awk -F',' '$%d == \"TRUE\" {print}'" %(cacheFile, publishableCol)
        else:
            cmd = "grep -v TEST %s | awk -F',' '$%d == \"TRUE\" {print}' | head -%d" %(cacheFile, publishableCol, numrows)
            
    print '*INFO* cmd=%s' %cmd
    stdout, stderr, rc = _exec_command(cmd)
#     print 'DEBUG cmd=%s, rc=%s, stdout=%s stderr=%s' %(cmd,rc,stdout,stderr)
    if rc !=0 or stderr !='':
        raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))
    rows = stdout.splitlines()
    if numrows != 'all' and len(rows) != numrows:
        raise AssertionError('*ERROR* Requested %d rows, Found %d rows' %(numrows,len(rows)))
    
    # get the requested fields
    result = []
    for row in rows:
        values = row.split(',')
        
        if len(values) != len(headerList):
            raise AssertionError('*ERROR* Number of values (%d) does not match number of headers (%d)' %(len(values), len(headerList)))
        
        fieldDict = {}
        for i in range(0, len(values)):
            if headerList[i] == 'DOMAIN':
                newdomain = _convert_cachedomain_to_normal_format(values[i]) 
                fieldDict[headerList[i]] = newdomain
            else:    
                fieldDict[headerList[i]] = values[i]
           
        result.append(fieldDict)
              
    _delete_file(cacheFile,'',False)
    return result 

def _convert_cachedomain_to_normal_format(domain):
    if domain.lower() == 'marketprice':
        newDomain = 'MARKET_PRICE'
    elif domain.lower() == 'marketbyprice':
        newDomain = 'MARKET_BY_PRICE'
    elif domain.lower() == 'marketbyorder':
        newDomain = 'MARKET_BY_ORDER'
    elif domain.lower() == 'marketmaker':
        newDomain = 'MARKET_MAKER'
    else:
        raise AssertionError('*ERROR* Unsupported domain %d' %domain)
    return newDomain

def _convert_domain_to_cache_format(domain):
    newDomain = domain.replace('_','')
    if newDomain.lower() == 'marketprice':
        newDomain = 'MarketPrice'
    elif newDomain.lower() == 'marketbyprice':
        newDomain = 'MarketByPrice'
    elif newDomain.lower() == 'marketbyorder':
        newDomain = 'MarketByOrder'
    elif newDomain.lower() == 'marketmaker':
        newDomain = 'MarketMaker'
    else:
        raise AssertionError('*ERROR* Unsupported domain %d' %domain)
    return newDomain	