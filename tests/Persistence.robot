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
    Start MTE    ${MTE}
    Delete Persist Backup
    Trigger Persistence File Backup
    @{existingPersistBackupFiles}=    wait for search file    ${VENUE_DIR}    PERSIST_${mte}_*.DAT    2    180
    Delete Persist Backup
    [Teardown]

Persistence File Cleanup
    Start MTE    ${MTE}
    ${keepDays}=    Get Backup Keey Days
    Delete Persist Backup
    generate persistence backup    ${VENUE_DIR}    ${MTE}    ${keepDays}
    Go Into EndOfDay time
    verify persistence cleanup    ${VENUE_DIR}    ${MTE}    ${keepDays}
    Delete Persist Backup

Persistence File Creation
    [Documentation]    Verify that on startup, the MTE creates a persist file.
    Stop MTE    ${MTE}
    Delete Persist Files    ${MTE}    ${VENUE_DIR}
    Start MTE    ${MTE}
    Persist File Should Exist    ${MTE}    ${VENUE_DIR}
    [Teardown]

Persistence File Loading
    [Documentation]    Verify that the MTE correctly loads the existing persist file on startup to initialize its cache.
    Comment    The initial start MTE, wait for FMS reorg, wait for persist file update, and stop MTE KWs are a workaround of a MTE defect (ERTCADVAMT-827). They may be removed when the defect is fixed.    When the MTE is started and the PERSIST file does not exist (full Reorg), the CHE%FMSREORGTIMESTAMP RIC has MANGLING_RULE = Unmangled (Default).    When the MTE is restarted without removing the PERSIST file (partial Reorg), the CHE%FMSREORGTIMESTAMP RIC has MANGLING_RULE = CATF Specified Mangle Settings
    Start MTE    ${MTE}
    Wait For FMS Reorg    ${MTE}
    wait for persist file update    ${MTE}    ${VENUE_DIR}
    Stop MTE    ${MTE}
    Start MTE    ${MTE}
    Wait For FMS Reorg    ${MTE}
    wait for persist file update    ${MTE}    ${VENUE_DIR}
    Dumpcache And Copyback Result    ${MTE}    ${LOCAL_TMP_DIR}/cache_before.csv
    Stop MTE    ${MTE}
    Start MTE    ${MTE}
    Dumpcache And Copyback Result    ${MTE}    ${LOCAL_TMP_DIR}/cache_after.csv
    verify csv files match    ${LOCAL_TMP_DIR}/cache_before.csv    ${LOCAL_TMP_DIR}/cache_after.csv    ignorefids=CURR_SEQ_NUM,TIME_CREATED,LAST_ACTIVITY,LAST_UPDATED,THREAD_ID,ITEM_FAMILY
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/cache_before.csv    ${LOCAL_TMP_DIR}/cache_after.csv

Verify FMS filter string
    [Documentation]    Verify that all context ids in the MTE cache are listed in FilterString in the MTE xml configuration file.
    Stop MTE    ${MTE}
    Delete Persist Files    ${MTE}    ${VENUE_DIR}
    Start MTE    ${MTE}
    Wait For FMS Reorg    ${MTE}
    ${dstdumpfile}=    set variable    ${LOCAL_TMP_DIR}/cachedump.csv
    Dumpcache And Copyback Result    ${MTE}    ${dstdumpfile}
    ${dstresult}=    set variable    ${LOCAL_TMP_DIR}/venue_config.xml
    Get MTE Config File    ${VENUE_DIR}    ${MTE}.xml    ${dstresult}
    ${serviceName}    Get FMS Service Name    ${MTE}
    ${fmsFilterString}    get MTE config value    ${dstresult}    FMS    ${serviceName}    FilterString
    verify cache contains only configured context ids    ${dstdumpfile}    ${fmsFilterString}
    [Teardown]    case teardown    ${dstdumpfile}    ${dstresult}

*** Keywords ***
Delete Persist Backup
    [Documentation]    Delete all persist backup files in Thunderdome box
    @{existingPersistBackupFiles}=    search remote files    ${VENUE_DIR}    PERSIST_${mte}_*.DAT    ${True}
    delete remote files    @{existingPersistBackupFiles}

Get Backup Keey Days
    [Documentation]    Return the tag value of <NumberOfDailyBackupsToKeep> in MTE config file
    ${mteConfigFile}=    set variable    ${LOCAL_TMP_DIR}/mteConfigFile.xml
    Get MTE Config File    ${VENUE_DIR}    ${MTE}.xml    ${mteConfigFile}
    ${keepDays}=    get MTE config value    ${mteConfigFile}    Persister    DDS    NumberOfDailyBackupsToKeep
    [Teardown]    Remove Files    ${mteConfigFile}
    [Return]    ${keepDays}

Go Into EndOfDay time
    [Documentation]    Force MTE go through EndOfDay event
    ${connectTimeRicDomain}=    set variable    MARKET_PRICE
    ${mteConfigFile}=    set variable    ${LOCAL_TMP_DIR}/mteConfigFile.xml
    ${mtecfgfile}=    Convert To Lowercase    ${MTE}.xml
    Get MTE Config File    ${VENUE_DIR}    ${mtecfgfile}    ${mteConfigFile}
    ${connectTimesIdentifier}=    Get ConnectTimesIdentifier    ${mteConfigFile}
    ${exlfile}=    get EXL from RIC and domain    ${connectTimesIdentifier}    ${connectTimeRicDomain}    ${LOCAL_FMS_DIR}    Feed Time
    @{dstRic}=    get ric fields from EXL    ${exlfile}    ${connectTimesIdentifier}    DST_REF
    @{tdBoxDateTime}=    get date and time
    @{localDateTime}    Get GMT Offset And Apply To Datetime    @{dstRic}[0]    @{tdBoxDateTime}[0]    @{tdBoxDateTime}[1]    @{tdBoxDateTime}[2]    @{tdBoxDateTime}[3]
    ...    @{tdBoxDateTime}[4]    @{tdBoxDateTime}[5]
    ${offsetInSecond}=    set variable    120
    @{endOfDay}=    add seconds to date    @{localDateTime}[0]    @{localDateTime}[1]    @{localDateTime}[2]    @{localDateTime}[3]    @{localDateTime}[4]
    ...    @{localDateTime}[5]    ${offsetInSecond}
    ${orgFile}    ${backupFile}    backup cfg file    ${VENUE_DIR}    ${mtecfgfile}
    set value in MTE cfg    ${orgFile}    EndOfDayTime    @{endOfDay}[3]:@{endOfDay}[4]
    stop MTE    ${MTE}
    start MTE    ${MTE}
    sleep    ${offsetInSecond}
    restore cfg file    ${orgFile}    ${backupFile}
    [Teardown]    Remove Files    ${mteConfigFile}

Go into feed time and set end feed time
    [Arguments]    ${offsetInSecond}
    [Documentation]    1. Getting the time \ (GMT) of Thunderdome box and set it as start feed time
    ...    (need to convert back to local time of venue)
    ...    2. Adding ${offsetInSecond} seconds to feed start time and set it as end feed time
    ...    3. Return full path of EXL file of feed time Ric (both original and modified file)
    ${connectTimeRicDomain}=    set variable    MARKET_PRICE
    ${mteConfigFile}=    set variable    ${LOCAL_TMP_DIR}/mteConfigFile.xml
    Get MTE Config File    ${VENUE_DIR}    ${MTE}.xml    ${mteConfigFile}
    ${connectTimesIdentifier}=    Get ConnectTimesIdentifier    ${mteConfigFile}
    ${exlfile}=    get EXL from RIC and domain    ${connectTimesIdentifier}    ${connectTimeRicDomain}    ${LOCAL_FMS_DIR}    Feed Time
    @{dstRic}=    get ric fields from EXL    ${exlfile}    ${connectTimesIdentifier}    DST_REF
    @{tdBoxDateTime}=    get date and time
    @{localDateTime}    Get GMT Offset And Apply To Datetime    @{dstRic}[0]    @{tdBoxDateTime}[0]    @{tdBoxDateTime}[1]    @{tdBoxDateTime}[2]    @{tdBoxDateTime}[3]
    ...    @{tdBoxDateTime}[4]    @{tdBoxDateTime}[5]
    ${startWeekDay}=    get day of week from date    @{localDateTime}[0]    @{localDateTime}[1]    @{localDateTime}[2]
    ${startTime}=    set variable    @{localDateTime}[3]:@{localDateTime}[4]:@{localDateTime}[5]
    @{endDateTime}=    add seconds to date    @{localDateTime}[0]    @{localDateTime}[1]    @{localDateTime}[2]    @{localDateTime}[3]    @{localDateTime}[4]
    ...    @{localDateTime}[5]    ${offsetInSecond}
    ${endWeekDay}=    get day of week from date    @{endDateTime}[0]    @{endDateTime}[1]    @{endDateTime}[2]
    ${endTime}=    set variable    @{endDateTime}[3]:@{endDateTime}[4]:@{endDateTime}[5]
    ${exlmodified} =    set variable    ${exlfile}_modified.exl
    Set Feed Time In EXL    ${exlfile}    ${exlmodified}    ${connectTimesIdentifier}    ${connectTimeRicDomain}    ${startTime}    ${endTime}
    ...    ${startWeekDay}
    Run Keyword Unless    '${startWeekDay}' == '${endWeekDay}'    Set Feed Time In EXL    ${exlfile}    ${exlmodified}    ${connectTimesIdentifier}    ${connectTimeRicDomain}
    ...    ${startTime}    ${endTime}    ${endWeekDay}
    [Teardown]    Remove Files    ${mteConfigFile}
    [Return]    ${exlfile}    ${exlmodified}

Trigger Persistence File Backup
    ${offsetInSecond}=    set variable    60
    ${exlFile}    ${exlmodified}    Go into feed time and set end feed time    ${offsetInSecond}
    ${exlfileInfo}    get first ric domain service from exl    ${exlmodified}
    Load Single EXL File    ${exlmodified}    ${exlfileInfo['SERVICE']}    ${CHE_IP}    25000
    ${sleepTime}=    Evaluate    ${offsetInSecond} + 60
    sleep    ${sleepTime}
    Load Single EXL File    ${exlFile}    ${exlfileInfo['SERVICE']}    ${CHE_IP}    25000
    [Teardown]    Remove Files    ${exlmodified}

wait for persist file update
    [Arguments]    ${mte}    ${venuedir}    ${waittime}=5    ${timeout}=60
    [Documentation]    Wait for the MTE persist file to be updated (it should be updated every 30 seconds)
    wait for file update    ${venuedir}/*/MTE/PERSIST_${mte}.DAT    ${waittime}    ${timeout}
