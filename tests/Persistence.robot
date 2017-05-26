*** Settings ***
Documentation     Verify MTE functionality related to the PERSIST file creation, updating, loading.
Suite Setup       Suite Setup With Playback
Suite Teardown    Suite Teardown
Force Tags        Playback
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
Persistence File Backup
    [Documentation]    Verify persistence file could be backup after end of connection time http://www.iajira.amers.ime.reuters.com/browse/CATF-1756
    [Setup]
    Delete Persist Backup
    ${serviceName}=    Get FMS Service Name
    ${currDateTime}=    get date and time
    ${exlFiles}    ${modifiedExlFiles}    Go Into End Feed Time    ${serviceName}
    Wait SMF Log Message After Time    ${MTE}.*Creating Snapshot of Persister Database    ${currDateTime}    waittime=10    timeout=120
    @{existingPersistBackupFiles}=    wait for search file    ${VENUE_DIR}    PERSIST_${MTE}_*.DAT    2    180
    Delete Persist Backup
    [Teardown]    Run Keywords    Restore EXL Changes    ${serviceName}    ${exlFiles}
    ...    AND    Case Teardown    @{modifiedExlFiles}

Persistence File Cleanup
    ${keepDays}=    Get Backup Keep Days
    Delete Persist Backup
    ${keepDays}=    Set Variable If    '${keepDays}' == 'NOT FOUND'    3    ${keepDays}
    generate persistence backup    ${keepDays}
    Go Into EndOfDay time
    verify persistence cleanup    ${keepDays}
    Delete Persist Backup

Persistence File Creation
    [Documentation]    Verify that on startup, the MTE creates a persist file.
    Stop MTE
    Delete Persist Files
    Start MTE
    Persist File Should Exist
    [Teardown]

Persistence File Loading
    [Documentation]    Verify that the MTE correctly loads the existing persist file on startup to initialize its cache.
    Stop MTE
    Delete Persist Files
    Start MTE
    Wait For Persist File Update
    Get Sorted Cache Dump    ${LOCAL_TMP_DIR}/cache_before.csv
    Stop MTE
    Start MTE
    Get Sorted Cache Dump    ${LOCAL_TMP_DIR}/cache_after.csv
    Comment    As a workaround of MTE defect (ERTCADVAMT-827), remove the CHE%FMSREORGTIMESTAMP line from the cache dump files before comparing them    When the MTE is started and the PERSIST file does not exist (full Reorg), the CHE%FMSREORGTIMESTAMP RIC has MANGLING_RULE = Unmangled (Default).    When the MTE is restarted without removing the PERSIST file (partial Reorg), the CHE%FMSREORGTIMESTAMP RIC has MANGLING_RULE = CATF Specified Mangle Settings
    ${removeFMSREORGTIMESTAMP}    Create Dictionary    .*CHE%FMSREORGTIMESTAMP.*=${EMPTY}
    Modify Lines Matching Pattern    ${LOCAL_TMP_DIR}/cache_before.csv    ${LOCAL_TMP_DIR}/cache_before.csv    ${removeFMSREORGTIMESTAMP}    ${False}
    Modify Lines Matching Pattern    ${LOCAL_TMP_DIR}/cache_after.csv    ${LOCAL_TMP_DIR}/cache_after.csv    ${removeFMSREORGTIMESTAMP}    ${False}
    verify csv files match    ${LOCAL_TMP_DIR}/cache_before.csv    ${LOCAL_TMP_DIR}/cache_after.csv    ignorefids=ITEM_ID,CURR_SEQ_NUM,TIME_CREATED,LAST_ACTIVITY,LAST_UPDATED,THREAD_ID,ITEM_FAMILY
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/cache_before.csv    ${LOCAL_TMP_DIR}/cache_after.csv

Verify New Item Added to Persist File via FMS
    [Documentation]    Add new RIC to EXL, load the EXL file, use PMT to dump persist file and check if new RIC exists in the dump file.
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1844
    ${domain}=    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${exlFullpath}    ${ric}    ${publishKey}    Get RIC Sample    ${domain}
    ${RicEXLfile}    Fetch From Right    ${exlFullpath}    \\
    ${localRicEXLFile}    set variable    ${LOCAL_TMP_DIR}/${RicEXLfile}
    ${newRic}    Create Unique RIC Name    newric
    add ric to exl file    ${exlFullpath}    ${localRicEXLFile}    ${newRic}    ${None}    ${domain}
    Load Single EXL File    ${localRicEXLFile}    ${serviceName}    ${CHE_IP}
    Wait For Persist File Update
    Verify Item Persisted    ${newRic}    ${EMPTY}    ${domain}
    [Teardown]    Case Teardown    ${localRicEXLFile}

Verify Realtime MARKET_PRICE Persistence
    [Documentation]    Verify that realtime MARKET_PRICE messages are written to the Persist file at end of feed time.
    ${serviceName}=    Get FMS Service Name
    Comment    Get content of Persist file before injection
    Wait For Persist File Update
    ${persistDump}=    Dump Persist File to Text
    Reset Sequence Numbers
    ${injectFile}=    Generate PCAP File Name    ${serviceName}    General RIC Update
    ${remoteCapture}=    Inject PCAP File and Wait For Output    ${injectFile}
    ${domain}=    Set Variable    MARKET_PRICE
    @{ricList}=    Get RIC List From Remote PCAP    ${remoteCapture}    ${domain}
    Comment    Get FID values for published RICs from Persist file before injection.    Search pattern matches unmangled RIC name at start of line and followed by '|'
    ${re}=    Catenate    SEPARATOR=\\||^    @{ricList}
    ${re}=    Set Variable    ^${re}\\|
    ${re}=    Remove String Using Regexp    ${re}    !\\[|!!
    @{allFidValuesBefore}=    Grep Local File    ${persistDump}    ${re}
    Comment    Get FID values for published RICs from Persist file after injection
    Wait For Persist File Update
    ${persistDump}=    Dump Persist File to Text
    @{allFidValuesAfter}=    Grep Local File    ${persistDump}    ${re}
    : FOR    ${ric}    IN    @{ricList}
    \    ${unmangledRic}=    Remove String Using Regexp    ${ric}    !\\[|!!
    \    ${before}=    Get Matches    ${allFIDValuesBefore}    regexp=^${unmangledRic}\\|
    \    ${after}=    Get Matches    ${allFIDValuesAfter}    regexp=^${unmangledRic}\\|
    \    Sort List    ${before}
    \    Sort List    ${after}
    \    Run Keyword And Expect Error    *are different*    Lists Should Be Equal    ${before}    ${after}
    [Teardown]    Case Teardown    ${persistDump}

Verify Recovery if Persist File is Damaged
    [Documentation]    Verify the backup persist file (PERSIST_XXX.DAT.LOADED) is loaded if the normal persist file (PERSIST_XXX.DAT) is invalid by comparing two dump cathe files. Restore PERSIST_XXX.DAT and PERSIST_XXX.DAT.LOADED files in the MTE finally.
    ...    http://jirag.int.thomsonreuters.com/browse/CATF-2147
    [Setup]
    Delete Persist Backup
    ${serviceName}=    Get FMS Service Name
    Wait For Persist File Update
    ${fileList_DAT}=    backup remote cfg file    ${REMOTE_MTE_CONFIG_DIR}    PERSIST_${MTE}.DAT
    Get Sorted Cache Dump    ${LOCAL_TMP_DIR}/cache_before.csv
    Stop MTE
    Create Remote File Content    ${REMOTE_MTE_CONFIG_DIR}/PERSIST_${MTE}.DAT    //file 12345
    Start MTE
    Get Sorted Cache Dump    ${LOCAL_TMP_DIR}/cache_after.csv
    ${removeFMSREORGTIMESTAMP}    Create Dictionary    .*CHE%FMSREORGTIMESTAMP.*=${EMPTY}
    Modify Lines Matching Pattern    ${LOCAL_TMP_DIR}/cache_before.csv    ${LOCAL_TMP_DIR}/cache_before.csv    ${removeFMSREORGTIMESTAMP}    ${False}
    Modify Lines Matching Pattern    ${LOCAL_TMP_DIR}/cache_after.csv    ${LOCAL_TMP_DIR}/cache_after.csv    ${removeFMSREORGTIMESTAMP}    ${False}
    verify csv files match    ${LOCAL_TMP_DIR}/cache_before.csv    ${LOCAL_TMP_DIR}/cache_after.csv    ignorefids=ITEM_ID,CURR_SEQ_NUM,TIME_CREATED,LAST_ACTIVITY,LAST_UPDATED,THREAD_ID,ITEM_FAMILY
    [Teardown]    Run Keywords    Restore Persistence File    ${fileList_DAT}
    ...    AND    case teardown    ${LOCAL_TMP_DIR}/cache_before.csv    ${LOCAL_TMP_DIR}/cache_after.csv

Persistence file FIDs existence check
    [Documentation]    Make sure below fids don’t exist in the persistence file:
    ...    6401 DDS_DSO_ID
    ...    6480 SPS_SP_RIC
    ...    6394 MC_LABEL
    ...    Make sure below fids do exist in the persistence file:
    ...    1 PROD_PERM
    ...    15 CURRENCY
    ...    5257 CONTEXT_ID
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1845
    ${domain}=    Get Preferred Domain
    ${ric}    ${publishKey}    Get RIC From MTE Cache    ${domain}
    Wait For Persist File Update
    ${cacheDomainName}=    Remove String    ${domain}    _
    ${pmatDomain}=    Map to PMAT Numeric Domain    ${cacheDomainName}
    ${pmatDumpfile}=    Dump Persist File To XML    --ric ${ric}    --domain ${pmatDomain}
    ${fidsSet}    get all fids from PersistXML    ${pmatDumpfile}
    List Should Not Contain Value    ${fidsSet}    6401    Persist file should not contain DDS_DSO_ID FID 6401
    List Should Not Contain Value    ${fidsSet}    6480    Persist file should not contain SPS_SP_RIC FID 6480
    List Should Not Contain Value    ${fidsSet}    6394    Persist file should not contain MC_LABEL FID 6394
    List Should Contain Value    ${fidsSet}    1    Persist file should contain PROD_PERM FID 1
    List Should Contain Value    ${fidsSet}    15    Persist file should contain CURRENCY FID 15
    List Should Contain Value    ${fidsSet}    5357    Persist file should contain CONTEXT_ID FID 5357
    [Teardown]    Case Teardown    ${pmatDumpfile}

Verify ALL SICs are valid in Persistence file
    [Documentation]    Verify All SICs are available in Persistence file compare to EXL file by CONTEXTID in MTE config file.
    ...
    ...    http://jirag.int.thomsonreuters.com/browse/CATF-2277
    ${domain}=    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    Wait For Persist File Update
    ${cacheDomainName}=    Remove String    ${domain}    _
    ${pmatDomain}=    Map to PMAT Numeric Domain    ${cacheDomainName}
    ${pmatDumpfile}=    Dump Persist File To Text    --domain ${pmatDomain}    --fids 5357
    ${mteConfigFile}    Get MTE Config File
    ${contextIds}    get context ids from config file    ${mteConfigFile}
    ${sicDomain_EXL}    get_SicDomain_in_AllExl_by_ContextID    ${serviceName}    ${contextIds}
    ${sicDomain_persist}    get_SicDomain_in_DumpPersistFile_Txt    ${pmatDumpfile}
    verify_all_sics_in_persistFile    ${sicDomain_persist}    ${sicDomain_EXL}
    [Teardown]    Case Teardown    ${pmatDumpfile}

Process failure while loading Persist file
    [Documentation]    The backup persist file should not be overwritten by a blank persist file during MTE startup. This is to protect against the situation where we have consecutive MTE process failures overwriting the persist file because it hasn't had time to load the original from disk and write it out again after loading before the process fails again.
    ...
    ...    http://jirag.int.thomsonreuters.com/browse/CATF-2216
    ${serviceName}=    Get FMS Service Name
    Wait For Persist File Update
    Get Sorted Cache Dump    ${LOCAL_TMP_DIR}/cache_before.csv
    Stop MTE
    @{foundFiles}=    search remote files    ${VENUE_DIR}    PERSIST_${MTE}.DAT.LOADED    ${TRUE}
    Run Keyword if    len(${foundFiles})    Delete Remote Files    @{foundFiles}
    Run Commander    process    start ${MTE}
    Wait for Persist Load to Start
    Kill Processes    MTE    FTE
    Start MTE
    Get Sorted Cache Dump    ${LOCAL_TMP_DIR}/cache_after.csv
    ${removeFMSREORGTIMESTAMP}    Create Dictionary    .*CHE%FMSREORGTIMESTAMP.*=${EMPTY}
    Modify Lines Matching Pattern    ${LOCAL_TMP_DIR}/cache_before.csv    ${LOCAL_TMP_DIR}/cache_before.csv    ${removeFMSREORGTIMESTAMP}    ${False}
    Modify Lines Matching Pattern    ${LOCAL_TMP_DIR}/cache_after.csv    ${LOCAL_TMP_DIR}/cache_after.csv    ${removeFMSREORGTIMESTAMP}    ${False}
    verify csv files match    ${LOCAL_TMP_DIR}/cache_before.csv    ${LOCAL_TMP_DIR}/cache_after.csv    ignorefids=ITEM_ID,CURR_SEQ_NUM,TIME_CREATED,LAST_ACTIVITY,LAST_UPDATED,THREAD_ID,ITEM_FAMILY
    [Teardown]    Case Teardown    ${LOCAL_TMP_DIR}/cache_before.csv    ${LOCAL_TMP_DIR}/cache_after.csv

*** Keywords ***
Delete Persist Backup
    [Documentation]    Delete all persist backup files in Thunderdome box
    @{existingPersistBackupFiles}=    search remote files    ${VENUE_DIR}    PERSIST_${MTE}_*.DAT    ${True}
    delete remote files    @{existingPersistBackupFiles}

Get Backup Keep Days
    [Documentation]    Return the tag value of <NumberOfDailyBackupsToKeep> in MTE config file
    ${mteConfigFile}=    Get MTE Config File
    ${keepDays}=    get MTE config value    ${mteConfigFile}    Persistence    DDS    NumberOfDailyBackupsToKeep
    [Teardown]
    [Return]    ${keepDays}

Go Into EndOfDay time
    [Documentation]    Force MTE go through EndOfDay event
    ${connectTimeRicDomain}=    set variable    MARKET_PRICE
    ${localCfgFile}=    Get MTE Config File
    @{dstRic}=    get MTE config list by path    ${localCfgFile}    CHE-TimeZoneForConfigTimes
    @{tdBoxDateTime}=    get date and time
    @{localDateTime}    Get GMT Offset And Apply To Datetime    @{dstRic}[0]    @{tdBoxDateTime}[0]    @{tdBoxDateTime}[1]    @{tdBoxDateTime}[2]    @{tdBoxDateTime}[3]
    ...    @{tdBoxDateTime}[4]    @{tdBoxDateTime}[5]
    ${offsetInSecond}=    set variable    300
    ${endOfDay}    add time to date    @{localDateTime}[0]-@{localDateTime}[1]-@{localDateTime}[2] @{localDateTime}[3]:@{localDateTime}[4]:@{localDateTime}[5]    ${offsetInSecond} second    result_format=%H:%M
    ${remoteCfgFile}    ${backupFile}    backup remote cfg file    ${REMOTE_MTE_CONFIG_DIR}    ${MTE_CONFIG}
    set value in MTE cfg    ${localCfgFile}    EndOfDayTime    ${endOfDay}    fail
    Put Remote File    ${localCfgFile}    ${remoteCfgFile}
    stop MTE
    start MTE
    sleep    ${offsetInSecond}
    restore remote cfg file    ${remoteCfgFile}    ${backupFile}
    stop MTE
    start MTE
    Comment    Revert changes in local venue config file
    Set Suite Variable    ${LOCAL_MTE_CONFIG_FILE}    ${None}
    Get MTE Config File
    [Teardown]

Restore Persistence File
    [Arguments]    ${fileList_DAT}
    [Documentation]    Restore Persistence File, Restart MTE in order to update Persist File in the cache.
    Stop MTE
    restore_remote_cfg_file    ${fileList_DAT[0]}    ${fileList_DAT[1]}
    Start MTE
    Wait For Persist File Update
