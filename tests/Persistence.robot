*** Settings ***
Documentation     Verify MTE functionality related to the PERSIST file creation, updating, loading.
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
Persistence File Backup
    [Documentation]    Verify persistence file could be backup after end of connection time http://www.iajira.amers.ime.reuters.com/browse/CATF-1756
    [Setup]
    Start MTE
    Delete Persist Backup
    ${serviceName}=    Get FMS Service Name
    ${offsetInSecond}=    set variable    120
    ${currDateTime}=    get date and time
    ${exlFiles}    ${exlBackupFiles}    Go Into Feed Time And Set End Feed Time    ${serviceName}    ${offsetInSecond}
    sleep    ${offsetInSecond}
    Wait SMF Log Message After Time    ${MTE}.*Creating Snapshot of Persister Database    ${currDateTime}    10    120
    @{existingPersistBackupFiles}=    wait for search file    ${VENUE_DIR}    PERSIST_${MTE}_*.DAT    2    180
    Delete Persist Backup
    [Teardown]    Restore EXL Changes    ${serviceName}    ${exlFiles}    ${exlBackupFiles}

Persistence File Cleanup
    Start MTE
    ${keepDays}=    Get Backup Keep Days
    Delete Persist Backup
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

Verify FMS filter string
    [Documentation]    Verify that all context ids in the MTE cache are listed in FilterString in the MTE xml configuration file.
    Stop MTE
    Delete Persist Files
    Start MTE
    Wait For FMS Reorg
    ${dstdumpfile}=    set variable    ${LOCAL_TMP_DIR}/cachedump.csv
    Get Sorted Cache Dump    ${dstdumpfile}
    ${mteConfigFile}=    Get MTE Config File
    ${serviceName}    Get FMS Service Name
    ${fmsFilterString}    get MTE config value    ${mteConfigFile}    FMS    ${serviceName}    FilterString
    verify cache contains only configured context ids    ${dstdumpfile}    ${fmsFilterString}
    [Teardown]    case teardown    ${dstdumpfile}

Verify New Item Added to Persist File via FMS
    [Documentation]    Add new RIC to EXL, load the EXL file, use PMT to dump persist file and check if new RIC exists in the dump file.
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1844
    ${domain}=    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${EXLfullpath}=    Get EXL For RIC    ${domain}    ${serviceName}    ${ric}
    ${RicEXLfile}    Fetch From Right    ${EXLfullpath}    \\
    ${localRicEXLFile}    set variable    ${LOCAL_TMP_DIR}/${RicEXLfile}
    ${newRic}    Create Unique RIC Name    newric
    add ric to exl file    ${EXLfullpath}    ${localRicEXLFile}    ${newRic}    ${None}    ${domain}
    ${currDateTime}=    get date and time
    ${offsetInSecond}=    set variable    120
    ${feedEXLFiles}    ${feedEXLBackupFiles}    Go Into Feed Time And Set End Feed Time    ${serviceName}    ${offsetInSecond}
    Load Single EXL File    ${localRicEXLFile}    ${serviceName}    ${CHE_IP}
    sleep    ${offsetInSecond}
    Wait SMF Log Message After Time    ${MTE}.*Persist cycle completed    ${currDateTime}    10    120
    Verfiy RIC Persisted    ${newRic}    ${domain}
    [Teardown]    Run Keywords    Restore EXL Changes    ${serviceName}    ${feedEXLFiles}    ${feedEXLBackupFiles}
    ...    AND    Case Teardown    ${localRicEXLFile}

Persistence file FIDs existence check
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1845
    ...    Make sure below fids don’t exist in the dumped persistence file:
    ...    6401 DDS_DSO_ID 6480 SPS_SP_RIC 6394 MC_LABEL
    ${domain}=    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${offsetInSecond}=    set variable    120
    ${currDateTime}=    get date and time
    ${feedEXLFiles}    ${feedEXLBackupFiles}    Go Into Feed Time And Set End Feed Time    ${serviceName}    ${offsetInSecond}
    sleep    ${offsetInSecond}
    Wait SMF Log Message After Time    ${MTE}.*Persist cycle completed    ${currDateTime}    10    120
    ${cacheDomainName}=    Remove String    ${domain}    _
    ${pmatDomain}=    Map to PMAT Numeric Domain    ${cacheDomainName}
    ${pmatDumpfile}=    Dump Persist File To XML    --ric ${ric}    --domain ${pmatDomain}
    ${fidsSet}    get all fids from PersistXML    ${pmatDumpfile}
    List Should Not Contain Value    ${fidsSet}    6401
    List Should Not Contain Value    ${fidsSet}    6480
    List Should Not Contain Value    ${fidsSet}    6394
    List Should Contain Value    ${fidsSet}    1
    List Should Contain Value    ${fidsSet}    15
    List Should Contain Value    ${fidsSet}    5357
    [Teardown]    Run Keywords    Restore EXL Changes    ${serviceName}    ${feedEXLFiles}    ${feedEXLBackupFiles}
    ...    AND    Case Teardown    ${pmatDumpfile}

*** Keywords ***
Delete Persist Backup
    [Documentation]    Delete all persist backup files in Thunderdome box
    @{existingPersistBackupFiles}=    search remote files    ${VENUE_DIR}    PERSIST_${MTE}_*.DAT    ${True}
    delete remote files    @{existingPersistBackupFiles}

Get Backup Keep Days
    [Documentation]    Return the tag value of <NumberOfDailyBackupsToKeep> in MTE config file
    ${mteConfigFile}=    Get MTE Config File
    ${keepDays}=    get MTE config value    ${mteConfigFile}    DDS    NumberOfDailyBackupsToKeep
    [Teardown]
    [Return]    ${keepDays}

Go Into EndOfDay time
    [Documentation]    Force MTE go through EndOfDay event
    ${connectTimeRicDomain}=    set variable    MARKET_PRICE
    ${mtecfgfile}=    Convert To Lowercase    ${MTE}.xml
    ${mteConfigFile}=    Get MTE Config File
    @{dstRic}=    get MTE config list by path    ${mteConfigFile}    CHE-TimeZoneForConfigTimes
    @{tdBoxDateTime}=    get date and time
    @{localDateTime}    Get GMT Offset And Apply To Datetime    @{dstRic}[0]    @{tdBoxDateTime}[0]    @{tdBoxDateTime}[1]    @{tdBoxDateTime}[2]    @{tdBoxDateTime}[3]
    ...    @{tdBoxDateTime}[4]    @{tdBoxDateTime}[5]
    ${offsetInSecond}=    set variable    300
    ${endOfDay}    add time to date    @{localDateTime}[0]-@{localDateTime}[1]-@{localDateTime}[2] @{localDateTime}[3]:@{localDateTime}[4]:@{localDateTime}[5]    ${offsetInSecond} second    result_format=%H:%M
    ${orgFile}    ${backupFile}    backup remote cfg file    ${VENUE_DIR}    ${mtecfgfile}
    set value in MTE cfg    ${orgFile}    EndOfDayTime    ${endOfDay}
    stop MTE
    start MTE
    sleep    ${offsetInSecond}
    restore remote cfg file    ${orgFile}    ${backupFile}
    stop MTE
    start MTE
    Comment    Revert changes in local venue config file
    Set Suite Variable    ${LOCAL_MTE_CONFIG_FILE}    ${None}
    ${configFileLocal}=    Get MTE Config File
    [Teardown]

Go Into Feed Time And Set End Feed Time
    [Arguments]    ${serviceName}    ${offsetInSecond}
    [Documentation]    For all feeds, set start of feed time to current time and end of feed time in 2 minutes.
    ...    Return:
    ...    ${exlFiles} : list of exlFiles that is modified by this KW
    ...    ${exlBackupFiles} : list of exlFiles that renamed by this KW and reserve the original value of the EXL files
    ${connectTimeRicDomain}=    set variable    MARKET_PRICE
    ${mteConfigFile}=    Get MTE Config File
    @{connectTimesIdentifierList}=    Get ConnectTimesIdentifier    ${mteConfigFile}    ${Empty}
    @{exlBackupFiles}=    Create List
    @{exlFiles}=    Create List
    : FOR    ${connectTimesIdentifier}    IN    @{connectTimesIdentifierList}
    \    ${exlFile}=    get state EXL file    ${connectTimesIdentifier}    ${connectTimeRicDomain}    ${serviceName}    Feed Time
    \    ${count}=    Get Count    ${exlFiles}    ${exlFile}
    \    ${exlBackupFile}    set variable    ${exlFile}.backup
    \    Run Keyword if    ${count} == 0    append to list    ${exlFiles}    ${exlFile}
    \    Run Keyword if    ${count} == 0    append to list    ${exlBackupFiles}    ${exlBackupFile}
    \    Run Keyword if    ${count} == 0    Copy File    ${exlFile}    ${exlBackupFile}
    \    @{dstRic}=    get ric fields from EXL    ${exlFile}    ${connectTimesIdentifier}    DST_REF
    \    @{tdBoxDateTime}=    get date and time
    \    @{localDateTime}    Get GMT Offset And Apply To Datetime    @{dstRic}[0]    @{tdBoxDateTime}[0]    @{tdBoxDateTime}[1]    @{tdBoxDateTime}[2]
    \    ...    @{tdBoxDateTime}[3]    @{tdBoxDateTime}[4]    @{tdBoxDateTime}[5]
    \    ${startWeekDay}=    get day of week from date    @{localDateTime}[0]    @{localDateTime}[1]    @{localDateTime}[2]
    \    ${startTime}=    set variable    @{localDateTime}[3]:@{localDateTime}[4]:@{localDateTime}[5]
    \    ${endDateTime}    add time to date    @{localDateTime}[0]-@{localDateTime}[1]-@{localDateTime}[2] ${startTime}    ${offsetInSecond} second
    \    ${endDateTime}    get Time    year month day hour min sec    ${endDateTime}
    \    ${endWeekDay}=    get day of week from date    @{endDateTime}[0]    @{endDateTime}[1]    @{endDateTime}[2]
    \    ${endTime}=    set variable    @{endDateTime}[3]:@{endDateTime}[4]:@{endDateTime}[5]
    \    Set Feed Time In EXL    ${exlFile}    ${exlFile}    ${connectTimesIdentifier}    ${connectTimeRicDomain}    ${startTime}
    \    ...    ${endTime}    ${startWeekDay}
    \    Run Keyword Unless    '${startWeekDay}' == '${endWeekDay}'    Set Feed Time In EXL    ${exlFile}    ${exlFile}    ${connectTimesIdentifier}
    \    ...    ${connectTimeRicDomain}    ${startTime}    ${endTime}    ${endWeekDay}
    : FOR    ${exlFile}    IN    @{exlFiles}
    \    Load Single EXL File    ${exlFile}    ${serviceName}    ${CHE_IP}
    [Teardown]
    [Return]    ${exlFiles}    ${exlBackupFiles}

Restore EXL Changes
    [Arguments]    ${serviceName}    ${exlFiles}    ${exlBackupFiles}
    ${index}=    set variable    0
    : FOR    ${exlBackupFile}    IN    @{exlBackupFiles}
    \    Copy File    ${exlBackupFile}    ${exlFiles[${index}]}
    \    ${index}=    Evaluate    ${index} + 1
    \    Remove Files    ${exlBackupFile}
    : FOR    ${exlFile}    IN    @{exlFiles}
    \    Load Single EXL File    ${exlFile}    ${serviceName}    ${CHE_IP}
    [Teardown]
