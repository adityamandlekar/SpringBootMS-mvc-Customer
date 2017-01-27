﻿from __future__ import with_statement
from datetime import datetime, timedelta
import os
import os.path
from sets import Set
import string
import xml
import xml.etree.ElementTree as ET
from cache import _convert_cachedomain_to_normal_format
from LinuxFSUtilities import LinuxFSUtilities
from LinuxCoreUtilities import LinuxCoreUtilities
from utils.ssh import _exec_command

from VenueVariables import *

#############################################################################
# Keywords that use local copy of PERSIST file
#############################################################################

def get_all_fids_from_PersistXml(xmlfile):
    """get all fids from PMAT extactor's xml output file
     Returns a list of fids appeared in the file.
     Argument : PMAT extractor's xml output file name    
    """ 
    treeRoot = ET.parse(xmlfile).getroot()
    fidsSet = [];
    for atype in treeRoot.findall('.//FIELD'):
        fid = atype.get('id')
        fidsSet.append(fid)
    
    return fidsSet

def get_SicDomain_in_DumpPersistFile_Txt(PersistFile_TXT):
    """ A dump of the persist file with columns RIC, SIC, META, DOMAIN, CONTEXT_ID.
          (e.g produced by 'Dump Persist File To Text    --domain ${domain}    --fids 5357')
       Argument:
           PersistFile_TXT :  Dump cache Persist file             
       Return : a dictionary with contextID: set(sic|domain) 
    """    
    sicDomainByContxtID_Dir = {}
    with open(PersistFile_TXT) as dumPersistFile:
        line = dumPersistFile.readline() #ignore title line
        for line in dumPersistFile:
            list_line = line.strip().split('|')
            newDomain = _convert_cachedomain_to_normal_format(list_line[3])
            contextID = list_line[8]
            newSicDomain = list_line[1] + '|' + newDomain
            if contextID !=  "":  #there is contextID value is empty
                if contextID in sicDomainByContxtID_Dir: 
                    sicDomainByContxtID_Dir[contextID].add(newSicDomain)
                else:
                    sicDomainByContxtID_Dir[contextID] = {newSicDomain}
                
    if len(sicDomainByContxtID_Dir) == 0:
        raise AssertionError("'*ERROR* The dump cache persist file is null")
    else:
        return sicDomainByContxtID_Dir
    
def verify_item_in_persist_dump_file(persist_dump_file, ric, sic, domain):
    ''' Check if ric, sic and/or domain appeared in the persist_dump_file. 
        persist_dump_file usually contains RIC, SIC and/or Domain if user applies RIC, SIC and/or Domain filter in running PMAT dump.
        Argument : persist_dump_file:  the output file generated by runing PMAT with dump option
                   ric :  ric that need to be checked
                   sic :  sic that need to be checked
                   domain : data domain for the ric in PMAT domain format: MarketPrice, MarketByOrder, MarketByPrice, MarketMaker etc
        Return : Nil
    '''     
    if not os.path.exists(persist_dump_file):
        raise AssertionError('*ERROR*  %s is not available' %persist_dump_file) 
    
    tree = ET.parse(persist_dump_file)
    root = tree.getroot() 
    
    ric_path = './/DatabaseEntry/RIC'
    sic_path = './/DatabaseEntry/SIC'
    domain_path = './/DatabaseEntry/DOMAIN'

    if ric != '' and ric != None:
        ric_exist = False
        ric_nodes = root.findall(ric_path)
        if ric_nodes is None:
            raise AssertionError('*ERROR*  Missing RIC element under %s from file: %s' %(ric_path, persist_dump_file))

        for val in ric_nodes:
            if val.text == ric:
                ric_exist = True
                break
            
        if not ric_exist:  
            raise AssertionError('*ERROR* ric %s is not found in persist file %s' %(ric, persist_dump_file))  

        print '*INFO* RIC %s is found in persist file %s' %(ric, persist_dump_file)

    if sic != '' and sic != None:
        sic_exist = False
        sic_nodes = root.findall(sic_path)
        if sic_nodes is None:
            raise AssertionError('*ERROR*  Missing SIC element under %s from file: %s' %(sic_path, persist_dump_file))

        for val in sic_nodes:
            if val.text == sic:
                sic_exist = True
                break
            
        if not sic_exist:  
            raise AssertionError('*ERROR* sic %s is not found in persist file %s' %(sic, persist_dump_file))  

        print '*INFO* SIC %s is found in persist file %s' %(sic, persist_dump_file)
    
    if domain != '' and domain != None:
        domain_exist = False
        domain_nodes = root.findall(domain_path)
        if domain_nodes is None:
            raise AssertionError('*ERROR*  Missing DOMAIN element under %s from file: %s' %(domain_path, persist_dump_file))
    
        for val in domain_nodes:
            if val.text.upper() == domain.upper():
                domain_exist = True
                break
            
        if not domain_exist:  
            raise AssertionError('*ERROR* domain %s is not found in persist file %s' %(domain, persist_dump_file))  

        print '*INFO* Domain %s is found in persist file %s' %(domain, persist_dump_file)

def verify_item_not_in_persist_dump_file(persist_dump_file, ric, sic):
    ''' Check if ric, sic and/or domain appeared not in the persist_dump_file. 
        persist_dump_file does not contain RIC, SIC if user remove a RIC, SIC in running PMAT dump.
        Argument : persist_dump_file:  the output file generated by runing PMAT with dump option
                                              ric :  ric that need to be checked
                                              sic :  sic that need to be checked
        Return : Nil
    '''     
    if not os.path.exists(persist_dump_file):
        raise AssertionError('*ERROR*  %s is not available' %persist_dump_file) 
    
    tree = ET.parse(persist_dump_file)
    root = tree.getroot() 
    
    ric_path = './/DatabaseEntry/RIC'
    sic_path = './/DatabaseEntry/SIC'

    if ric != '' and ric != None:
        ric_exist = False
        ric_nodes = root.findall(ric_path)
        if ric_nodes is None:
            raise AssertionError('*ERROR*  Missing RIC element under %s from file: %s' %(ric_path, persist_dump_file))

        for val in ric_nodes:
            if val.text == ric:
                ric_exist = True
                break
            
        if ric_exist:  
            raise AssertionError('*ERROR* ric %s is found in persist file %s' %(ric, persist_dump_file))  

        print '*INFO* RIC %s is not found in persist file %s' %(ric, persist_dump_file)

    if sic != '' and sic != None:
        sic_exist = False
        sic_nodes = root.findall(sic_path)
        if sic_nodes is None:
            raise AssertionError('*ERROR*  Missing SIC element under %s from file: %s' %(sic_path, persist_dump_file))

        for val in sic_nodes:
            if val.text != sic:
                sic_exist = True
                break
            
        if sic_exist:  
            raise AssertionError('*ERROR* sic %s is found in persist file %s' %(sic, persist_dump_file))  

        print '*INFO* SIC %s is not found in persist file %s' %(sic, persist_dump_file)

def verify_all_sics_in_persistFile(sicDomain_persist ,sicDomain_exl):
     
     """ Verify SICs in persist file are available compare to exl files.
       Argument:
           sicDomain_persist: dictionary {contextID:set {(sic|domain)}} from Persist file
           sicDomain_exl: dictionary {contextID:set {(sic|domain)}} from exl
    """
     for contextID in sicDomain_exl:
        if contextID not in sicDomain_persist:
            raise AssertionError("*ERROR* No entries in Persist file for context id %s" %contextID)
        else:
            missing = sicDomain_exl[contextID] - sicDomain_persist[contextID]
            if len(missing):
                raise AssertionError("*ERROR* The following SIC|domain entries are missing from Persist file for context id %s: %s"%(contextID,','.join(str(self) for self in missing)))

#############################################################################
# Keywords that use remote PERSIST files
#############################################################################

def generate_persistence_backup(keepDays):
    """ based on the no. of keeping days generate dummy persistence backup files 
        
        params : keepDays = value found in MTE config tag <NumberOfDailyBackupsToKeep>

        return : N/A
        
        Examples :
            | generate persistence backup | 3
    """
            
    #Persistence backup filename format : PERSIST_${MTE}_YYYYMMDDTHHMMSS.DAT
    dummyRefFile = 'PERSIST_' + MTE + '.DAT'
    listOfPersistBackupFiles = LinuxFSUtilities().search_remote_files(VENUE_DIR, dummyRefFile, True)
    if (len(listOfPersistBackupFiles) == 0):
        raise AssertionError('*ERROR* Persistence file is missing' )
    
    backupfileDir = os.path.dirname(listOfPersistBackupFiles[0])
    tdBoxDatetime = LinuxCoreUtilities().get_date_and_time()
    oneDayInSecond = 60*60*24*-1
    for dayCount in range(0, int(keepDays)+2):
        dummyDatetime = datetime(int(tdBoxDatetime[0]), int(tdBoxDatetime[1]), int(tdBoxDatetime[2]), int('01'), int('00'), int('00')) + timedelta(seconds=int(dayCount*oneDayInSecond))
        targetFile = 'PERSIST_%s_%s%02d%02dT010000.DAT' %(MTE,dummyDatetime.year,dummyDatetime.month,dummyDatetime.day)
        cmd = "cp -a %s %s"%(listOfPersistBackupFiles[0], backupfileDir + '/' + targetFile)
        stdout, stderr, rc = _exec_command(cmd)
    
        if rc !=0 or stderr !='':
            raise AssertionError('*ERROR* cmd=%s, rc=%s, %s %s' %(cmd,rc,stdout,stderr))                                                                                                                          
                                                                                                                         
def verify_persistence_cleanup(keepDays):
    """ verify if cleanup action has carried out properly after EndOfDay time
        
        params : keepDays = value found in MTE config tag <NumberOfDailyBackupsToKeep>

        return : N/A
        
        Examples :
         | verify persistence cleanup | 3 |
    """
        
    #Get a list of persist backup file
    targetFile = 'PERSIST_' + MTE + '_*.DAT'
    listOfPersistBackupFiles = LinuxFSUtilities().search_remote_files(VENUE_DIR, targetFile, True)
    
    # 1. Test Case will use generate_persistence_backup_files() to generate dummy persist backup files
    # 2. Total no. of backup file generated is 1(current day) + keeyDays + 1(Suppose to be cleanup/deleted)
    originalNoOfBackupFile = 1 + int(keepDays) + 1
    if not ((originalNoOfBackupFile - len(listOfPersistBackupFiles)) == 1):
        raise AssertionError('*ERROR* Expected no. of backup file remain after cleanup (%d), but (%d) has found' %(originalNoOfBackupFile-1,len(listOfPersistBackupFiles)))
 