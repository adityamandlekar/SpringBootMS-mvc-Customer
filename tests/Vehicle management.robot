*** Settings ***
Documentation     Vehicle management functionality.
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         VenueVariables.py

*** Variables ***

*** Test Cases ***
Verify Long RIC handled correctly
    [Documentation]    Verify long RIC appeared in the cache dump file after the modified EXL with a long RIC has been loaded
    Start MTE    ${MTE}
    ${filesToIgnore}=    Create List    _cs_run    _dl_sav    _fd_time    _mk_holiday    _otfc
    ...    _venue_heartbeat    _trd_time
    ${srcFile}    find first non state ric exl file    ${LOCAL_FMS_DIR}    ${filesToIgnore}
    ${fileInfo}    get first ric domain service from exl    ${srcFile[2]}
    ${dstfile}    set variable    ${LOCAL_TMP_DIR}/${srcFile[0]}
    ${long_ric}=    set variable    ric_with_length_of_32_charactors
    Set RIC In EXL    ${srcFile[2]}    ${dstfile}    ${fileInfo['RIC']}    ${fileInfo['DOMAIN']}    ${long_ric}
    Load Single EXL File    ${dstfile}    ${fileInfo['SERVICE']}    ${CHE_IP}    25000    --AllowRICChange true
    Wait For FMS Reorg    ${MTE}
    ${dstdumpfile}=    set variable    ${LOCAL_TMP_DIR}/cache_after.csv
    Dumpcache And Copyback Result    ${MTE}    ${dstdumpfile}
    verify ric in cachedump    ${dstdumpfile}    ${long_ric}
    Load Single EXL File    ${srcFile[2]}    ${fileInfo['SERVICE']}    ${CHE_IP}    25000    --AllowRICChange true
    Wait For FMS Reorg    ${MTE}
    [Teardown]    case teardown    ${dstfile}    ${dstdumpfile}

Verify PE Change Behavior
    [Documentation]    Test Case - Verify PE Change Behavior : http://www.iajira.amers.ime.reuters.com/browse/CATF-1715
    ${mteConfigFile}=    set variable    ${LOCAL_TMP_DIR}/mteConfigFile.xml
    Get MTE Config File    ${VENUE_DIR}    ${MTE}.xml    ${mteConfigFile}
    ${domain}    Get Preferred Domain    ${mteConfigFile}
    Disable PE Mangling    ${MTE}
    ${ric}    ${service}    ${exlfile}    get first ric for domain from exl    ${domain}    ${LOCAL_FMS_DIR}
    @{fields}=    Create List    PROD_PERM
    @{pe}=    get ric fields from EXL    ${exlfile}    ${ric}    @{fields}
    ${penew}=    set variable    @{pe}[0]1
    ${exlmodified} =    set variable    ${exlfile}_modified.exl
    Set PE in EXL    ${exlfile}    ${exlmodified}    ${penew}
    Start Capture MTE Output    ${MTE}
    Load Single EXL File    ${exlmodified}    ${service}    ${CHE_IP}    25000
    Stop Capture MTE Output    ${MTE}    1    15
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    Run Keyword And Continue On Failure    verify PE Change in message    ${LOCAL_TMP_DIR}/capture_local.pcap    ${VENUE_DIR}    ${DAS_DIR}    ${ric}    @{pe}[0]
    ...    ${penew}
    Load Single EXL File    ${exlfile}    ${service}    ${CHE_IP}    25000
    wait for file update    ${venuedir}/*/MTE/PERSIST_${mte}.DAT    5    120
    Stop MTE    ${MTE}
    Start MTE    ${MTE}
    [Teardown]    case teardown    ${exlmodified}    ${LOCAL_TMP_DIR}/capture_local.pcap    ${LOCAL_TMP_DIR}/mteConfigFile.xml

Verify New Item Creation via FMS
    [Documentation]    Verify that a new item can be created by adding it to an EXL file and loading it via FMS
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1711
    Start MTE    ${MTE}
    Get MTE Config File    ${VENUE_DIR}    ${MTE}.xml    ${LOCAL_TMP_DIR}/mteConfigFile.xml
    ${domain}=    Get Preferred Domain    ${LOCAL_TMP_DIR}/mteConfigFile.xml
    ${EXL_File} =    get EXL file from domain    ${LOCAL_FMS_DIR}    ${domain}
    ${info}=    get first ric domain service from exl    ${EXL_File}
    add ric to exl file    ${EXL_File}    ${LOCAL_TMP_DIR}/output.exl    A_RIC_THAT_WILL_NEVER_EXIST
    Load Single EXL File    ${LOCAL_TMP_DIR}/output.exl    ${info['SERVICE']}    ${CHE_IP}
    Wait For FMS Reorg    ${MTE}
    Dumpcache And Copyback Result    ${MTE}    ${LOCAL_TMP_DIR}/cache.out
    verify ric in cachedump    ${LOCAL_TMP_DIR}/cache.out    A_RIC_THAT_WILL_NEVER_EXIST
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/output.exl    ${LOCAL_TMP_DIR}/cache.out    ${LOCAL_TMP_DIR}/mteConfigFile.xml

Partial REORG on EXL Change
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1791
    ${mteConfigFile}=    set variable    ${LOCAL_TMP_DIR}/mteConfigFile.xml
    Get MTE Config File    ${VENUE_DIR}    ${MTE}.xml    ${mteConfigFile}
    ${domain}    Get Preferred Domain    ${mteConfigFile}
    ${ric}    ${service}    ${exlFile}    get first ric for domain from exl    ${domain}    ${LOCAL_FMS_DIR}
    Load Single EXL File    ${exlFile}    ${service}    ${CHE_IP}    25000
    ${fieldName}=    set variable    DSPLY_NAME
    ${fieldValueNew}=    set variable    PARTIALREORGTEST
    ${fieldValueOrg}=    Set Field Value in EXL    ${exlFile}    ${ric}    ${domain}    ${fieldName}    ${fieldValueNew}
    Start Capture MTE output    ${MTE}
    ${startDateTime}    set variable    "2010-01-01 00:00:00"
    Trigger Partial REORG    ${startDateTime}    ${service}
    Stop Capture MTE output    ${MTE}    1    15
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    ${verifyFIDs}=    Create List
    Append to List    ${verifyFIDs}    3
    ${verifyValues}=    Create List
    Append to List    ${verifyValues}    ${fieldValueNew}
    Run Keyword And Continue On Failure    verify correction change in message    ${LOCAL_TMP_DIR}/capture_local.pcap    ${DAS_DIR}    ${ric}    ${verifyFIDs}    ${verifyValues}
    ${fieldValueOrg}=    Set Field Value in EXL    ${exlFile}    ${ric}    ${domain}    ${fieldName}    ${fieldValueOrg}
    Load Single EXL File    ${exlFile}    ${service}    ${CHE_IP}    25000
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap    ${LOCAL_TMP_DIR}/mteConfigFile.xml

*** Keywords ***
Set Field Value in EXL
    [Arguments]    ${exlFile}    ${ric}    ${domain}    ${fieldName}    ${fieldValueNew}
    [Documentation]    This keyword could set the value for specific xml tag that found within <exlObject></exlObject> for specific ric and domain
    @{fields}    Create List    ${fieldName}
    @{fieldValueOrg}=    get ric fields from EXL    ${exlFile}    ${ric}    @{fields}
    modify exl    ${exlFile}    ${exlFile}    ${ric}    ${domain}    <it:${fieldName}>${fieldValueNew}</it:${fieldName}>
    [Return]    @{fieldValueOrg}[0]

Set PE in EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${newPE}
    [Documentation]    Keyword - Modify PROD_PERM value in header of EXL file
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1718
    modify exl header    ${srcFile}    ${dstFile}    <it:PROD_PERM>${newPE}</it:PROD_PERM>

Trigger Partial REORG
    [Arguments]    ${startDateTime}    ${service}
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    25000    ${LOCAL_FMS_BIN}
    ...    Recon    --Services ${service}    --UpdatesSince ${startDateTime}    --UseReconcileLXL false
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}
