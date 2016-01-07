*** Settings ***
Documentation     Vehicle management functionality.
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
Verify Long RIC handled correctly
    [Documentation]    Verify long RIC appeared in the cache dump file, published pcap file and persist file after the modified EXL with a long RIC has been loaded
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1648
    ${domain}=    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${EXLfullpath}=    Get EXL For RIC    ${LOCAL_FMS_DIR}    ${domain}    ${serviceName}    ${ric}
    ${EXLfile}=    Fetch From Right    ${EXLfullpath}    \\
    ${localEXLfile}=    set variable    ${LOCAL_TMP_DIR}/${EXLfile}
    ${long_ric}=    Create Unique RIC Name    32_chars_total
    Set RIC In EXL    ${EXLfullpath}    ${localEXLfile}    ${ric}    ${domain}    ${long_ric}
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    Start Capture MTE Output    ${MTE}    ${remoteCapture}
    Load Single EXL File    ${localEXLfile}    ${serviceName}    ${CHE_IP}    25000    --AllowRICChange true
    Wait For Persist File Update    ${MTE}    ${VENUE_DIR}    5    60
    Stop Capture MTE Output    ${MTE}    1    5
    ${newRic}    ${newPubRic}    Run Keyword And Continue On Failure    Verify RIC In MTE Cache    ${MTE}    ${long_ric}
    Run Keyword And Continue On Failure    Verify RIC Published    ${remoteCapture}    ${localEXLfile}    ${newPubRic}    ${domain}
    Run Keyword And Continue On Failure    Verfiy RIC Persisted    ${MTE}    ${long_ric}    ${domain}
    Load Single EXL File    ${EXLfullpath}    ${serviceName}    ${CHE_IP}    25000    --AllowRICChange true
    Wait For Persist File Update    ${MTE}    ${VENUE_DIR}
    [Teardown]    case teardown    ${localEXLfile}

Verify PE Change Behavior
    [Documentation]    Test Case - Verify PE Change Behavior : http://www.iajira.amers.ime.reuters.com/browse/CATF-1715
    Set Mangling Rule    ${MTE}    UNMANGLED
    ${domain}    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${exlfile}=    Get EXL For RIC    ${LOCAL_FMS_DIR}    ${domain}    ${serviceName}    ${ric}
    @{pe}=    get ric fields from EXL    ${exlfile}    ${ric}    PROD_PERM
    ${penew}=    set variable    @{pe}[0]1
    ${exlmodified} =    set variable    ${exlfile}_modified.exl
    Set PE in EXL    ${exlfile}    ${exlmodified}    ${penew}
    Start Capture MTE Output    ${MTE}
    Load Single EXL File    ${exlmodified}    ${serviceName}    ${CHE_IP}    25000
    Stop Capture MTE Output    ${MTE}    1    15
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    Run Keyword And Continue On Failure    verify PE Change in message    ${LOCAL_TMP_DIR}/capture_local.pcap    ${VENUE_DIR}    ${DAS_DIR}    ${pubRic}    ${pe}
    ...    ${penew}
    Load Single EXL File    ${exlfile}    ${serviceName}    ${CHE_IP}    25000
    Load Mangling Settings    ${MTE}
    Wait For Persist File Update    ${MTE}    ${VENUE_DIR}
    [Teardown]    case teardown    ${exlmodified}    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify New Item Creation via FMS
    [Documentation]    Verify that a new item can be created by adding it to an EXL file and loading it via FMS
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1711
    Start MTE    ${MTE}
    ${domain}=    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${EXL_File}=    Get EXL For RIC    ${LOCAL_FMS_DIR}    ${domain}    ${serviceName}    ${ric}
    ${uniqueRic}=    Create Unique RIC Name
    add ric to exl file    ${EXL_File}    ${LOCAL_TMP_DIR}/output.exl    ${uniqueRic}
    Load Single EXL File    ${LOCAL_TMP_DIR}/output.exl    ${serviceName}    ${CHE_IP}
    Wait For FMS Reorg    ${MTE}
    Verify RIC In MTE Cache    ${MTE}    ${uniqueRic}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/output.exl

Partial REORG on EXL Change
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1791
    ${domain}    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${exlFile}=    Get EXL For RIC    ${LOCAL_FMS_DIR}    ${domain}    ${serviceName}    ${ric}
    ${fieldName}=    set variable    DSPLY_NAME
    ${fieldValueNew}=    set variable    PARTIALREORGTEST
    ${fieldValueOrg}=    Set Field Value in EXL    ${exlFile}    ${ric}    ${domain}    ${fieldName}    ${fieldValueNew}
    Start Capture MTE output    ${MTE}
    ${UpdateSince}=    Calculate UpdateSince for REORG    ${exlFile}
    Trigger Partial REORG    ${UpdateSince}    ${serviceName}
    Stop Capture MTE output    ${MTE}    1    15
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    ${verifyFIDs}=    Create List    3
    ${verifyValues}=    Create List    ${fieldValueNew}
    Run Keyword And Continue On Failure    verify correction change in message    ${LOCAL_TMP_DIR}/capture_local.pcap    ${DAS_DIR}    ${pubRic}    ${verifyFIDs}    ${verifyValues}
    ${fieldValueOrg}=    Set Field Value in EXL    ${exlFile}    ${ric}    ${domain}    ${fieldName}    ${fieldValueOrg}
    Load Single EXL File    ${exlFile}    ${serviceName}    ${CHE_IP}    25000
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify RIC rename handled correctly
    [Documentation]    Verify RIC rename appeared in the cache dump file
    start MTE    ${MTE}
    Comment    //Setup variables for test
    ${domain}=    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${RIC_Before_Rename}    ${Published_RIC_Before_Rename}    Get RIC From MTE Cache    ${domain}
    ${RIC_After_Rename}=    Create Unique RIC Name    ${RIC_Before_Rename}
    ${EXLfullpath}=    Get EXL For RIC    ${LOCAL_FMS_DIR}    ${domain}    ${serviceName}    ${RIC_Before_Rename}
    ${EXLfile}    Fetch From Right    ${EXLfullpath}    \\
    ${LocalEXLfullpath}    set variable    ${LOCAL_TMP_DIR}/${EXLfile}
    ${contextIDs}=    Get Ric Fields from EXL    ${EXLfullpath}    ${RIC_Before_Rename}    CONTEXT_ID
    ${constituent_list}=    Get Constituents From FidFilter    ${VENUE_DIR}    ${contextIDs[0]}
    Comment    //Start test. Test 1: Check that the new RIC that we are about to create is NOT already in the cache
    Start Capture MTE Output    ${MTE}
    Copy File    ${EXLfullpath}    ${LocalEXLfullpath}
    Load Single EXL File    ${LocalEXLfullpath}    ${serviceName}    ${CHE_IP}    25000    --AllowRICChange true
    Wait For FMS Reorg    ${MTE}
    Verify RIC NOT In MTE Cache    ${MTE}    ${RIC_After_Rename}
    Comment    //Start test. Test 2: Check that the RIC can be renamed and that the existing RIC is no longer in the cache
    Start Capture MTE Output    ${MTE}
    Set RIC in EXL    ${EXLfullpath}    ${LocalEXLfullpath}    ${RIC_Before_Rename}    ${domain}    ${RIC_After_Rename}
    Load Single EXL File    ${LocalEXLfullpath}    ${serviceName}    ${CHE_IP}    25000    --AllowRICChange true
    Wait For FMS Reorg    ${MTE}
    Verify RIC NOT In MTE Cache    ${MTE}    ${RIC_Before_Rename}
    ${ric}    ${Published_RIC_After_Rename}    Verify RIC In MTE Cache    ${MTE}    ${RIC_After_Rename}
    Send TRWF2 Refresh Request    ${MTE}    ${Published_RIC_After_Rename}    ${domain}
    Wait For Persist File Update    ${MTE}    ${VENUE_DIR}    5    60
    Stop Capture MTE Output    ${MTE}
    Get Remote File    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local_2.pcap
    verify Unsolicited Response In Capture    ${LOCAL_TMP_DIR}/capture_local_2.pcap    ${DAS_DIR}    ${Published_RIC_After_Rename}    ${domain}    ${constituent_list}
    Comment    //Start test. Test 3: Check that the new RIC can be renamed back to the original name.
    Comment    //This also reverts the state back to as the begining of the test
    Start Capture MTE Output    ${MTE}
    Load Single EXL File    ${EXLfullpath}    ${serviceName}    ${CHE_IP}    25000    --AllowRICChange true
    Wait For FMS Reorg    ${MTE}
    Verify RIC NOT In MTE Cache    ${MTE}    ${RIC_After_Rename}
    ${ric}    ${Published_RIC_Before_Rename}    Verify RIC In MTE Cache    ${MTE}    ${RIC_Before_Rename}
    Send TRWF2 Refresh Request    ${MTE}    ${Published_RIC_Before_Rename}    ${domain}
    Wait For Persist File Update    ${MTE}    ${VENUE_DIR}    5    60
    Stop Capture MTE Output    ${MTE}
    Get Remote File    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local_3.pcap
    Verify Unsolicited Response In Capture    ${LOCAL_TMP_DIR}/capture_local_3.pcap    ${DAS_DIR}    ${Published_RIC_Before_Rename}    ${domain}    ${constituent_list}
    [Teardown]    case teardown    ${LocalEXLfullpath}    ${LOCAL_TMP_DIR}/capture_local_2.pcap    ${LOCAL_TMP_DIR}/capture_local_3.pcap

Verify FMS Rebuild
    [Documentation]    Force a rebuild of RIC via FMS and verify that a rebuild message is published for the RIC
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1849
    Start MTE    ${MTE}
    ${domain}    Get Preferred Domain
    ${serviceName}    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    Start Capture MTE Output    ${MTE}
    rebuild ric    ${serviceName}    ${ric}    ${domain}
    Stop Capture MTE Output    ${MTE}
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    Run Keyword And Continue On Failure    verify all response message num    ${LOCAL_TMP_DIR}/capture_local.pcap    ${VENUE_DIR}    ${DAS_DIR}    ${pubRic}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Drop a RIC by deleting EXL File and Full Reorg
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1850
    ...    To verify whether the RICs in a exl file can be dropped if the exl file is deleted.
    ${domain}    Get Preferred Domain
    ${serviceName}    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${exlFullFileName}=    get EXL for RIC    ${LOCAL_FMS_DIR}    ${domain}    ${serviceName}    ${ric}
    ${exlFilePath}    ${exlFileName}    Split Path    ${exlFullFileName}
    copy File    ${exlFullFileName}    ${LOCAL_TMP_DIR}/${exlFileName}
    remove file    ${exlFullFileName}
    ${currentDateTime}    get date and time
    Run Keyword And Continue On Failure    Load All EXL Files    ${serviceName}    ${CHE_IP}
    copy File    ${LOCAL_TMP_DIR}/${exlFileName}    ${exlFullFileName}
    wait smf log message after time    Drop message sent    ${currentDateTime}
    Run Keyword And Continue On Failure    Verify RIC is Dropped In MTE Cache    ${MTE}    ${ric}
    Load Single EXL File    ${exlFullFileName}    ${serviceName}    ${CHE_IP}    25000
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/${exlFileName}

Verify Reconcile of Cache
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1848
    ...    To verify whether a new RIC can be added and a old RIC can be dropped via reconcile
    ${mteConfigFile}=    Get MTE Config File
    ${SendRefreshForFullReorg}    Get MTE Config Value    ${mteConfigFile}    SendRefreshForFullReorg
    Should Be True    ${SendRefreshForFullReorg} != '1'    SendRefreshForFullReorg should be disabled
    ${domain}    Get Preferred Domain
    ${serviceName}    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${exlFullFileName}=    get EXL for RIC    ${LOCAL_FMS_DIR}    ${domain}    ${serviceName}    ${ric}
    ${exlFilePath}    ${exlFileName}    Split Path    ${exlFullFileName}
    copy File    ${exlFullFileName}    ${LOCAL_TMP_DIR}/${exlFileName}
    ${newRICName}    Create Unique RIC Name
    Set Symbol In EXL    ${exlFullFileName}    ${exlFullFileName}    ${ric}    ${domain}    ${newRICName}
    Set RIC In EXL    ${exlFullFileName}    ${exlFullFileName}    ${ric}    ${domain}    ${newRICName}
    ${currentDateTime}    get date and time
    Run Keyword And Continue On Failure    Load All EXL Files    ${serviceName}    ${CHE_IP}    25000    --UseReconcileLXL true
    copy File    ${LOCAL_TMP_DIR}/${exlFileName}    ${exlFullFileName}
    wait smf log message after time    FMS REORG DONE    ${currentDateTime}
    Verify RIC In MTE Cache    ${MTE}    ${newRICName}
    Run Keyword And Continue On Failure    Verify RIC is Dropped In MTE Cache    ${MTE}    ${ric}
    Load Single EXL File    ${exlFullFileName}    ${serviceName}    ${CHE_IP}    25000
    Verify RIC In MTE Cache    ${MTE}    ${ric}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/${exlFileName}

Verify SIC rename handled correctly
    [Documentation]    Verify SIC rename appeared in the cache dump file
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1893
    ${domain}=    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${result}=    get RIC fields from cache    ${MTE}    ${VENUE_DIR}    1    ${domain}    ${EMPTY}
    ${RIC} =    set variable    ${result[0]['RIC']}
    ${SIC_Before_Rename} =    set variable    ${result[0]['SIC']}
    ${SIC_After_Rename}=    set variable    ${SIC_Before_Rename}TestSIC
    ${Symbol_After_Rename}=    Get Substring    ${SIC_After_Rename}    2
    ${EXLfullpath}=    Get EXL For RIC    ${LOCAL_FMS_DIR}    ${domain}    ${serviceName}    ${RIC}
    ${EXLfile}    Fetch From Right    ${EXLfullpath}    \\
    ${LocalEXLfullpath}=    set variable    ${LOCAL_TMP_DIR}/${EXLfile}
    Copy File    ${EXLfullpath}    ${LocalEXLfullpath}
    Set Symbol In EXL    ${EXLfullpath}    ${LocalEXLfullpath}    ${RIC}    ${domain}    ${Symbol_After_Rename}
    Load Single EXL File    ${LocalEXLfullpath}    ${serviceName}    ${CHE_IP}    25000    --AllowSICChange true
    remove file    ${LocalEXLfullpath}
    ${ricFields}=    Get All Fields For RIC From Cache    ${MTE}    ${VENUE_DIR}    ${RIC}
    ${SIC_1}=    set variable    ${ricFields['SIC']}
    Should Be Equal    ${SIC_1}    ${SIC_After_Rename}
    Comment    //fallback
    Load Single EXL File    ${EXLfullpath}    ${serviceName}    ${CHE_IP}    25000    --AllowSICChange true
    ${ricFields}=    Get All Fields For RIC From Cache    ${MTE}    ${VENUE_DIR}    ${RIC}
    ${SIC_2}=    set variable    ${ricFields['SIC']}
    Should Be Equal    ${SIC_2}    ${SIC_Before_Rename}
    [Teardown]    Load Single EXL File    ${EXLfullpath}    ${serviceName}    ${CHE_IP}    25000    --AllowSICChange true

Verify FMS Extract and Insert
    [Documentation]    FMS Extract, Insert CHE owned RIC from/to CHE Database, CHE owned data can be extracted from CHE database via FMS, Insert CHE owned data to CHE database via FMS
    ...    Test Case - Verify FMS Extract and Insert : http://www.iajira.amers.ime.reuters.com/browse/CATF-1892
    Start MTE    ${MTE}
    ${domain}    Get Preferred Domain
    ${serviceName}    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${fidvalue}    Create List    300    100
    ${newfidvalue}    Create List    600    220
    ${extractFile}    set variable    ${LOCAL_TMP_DIR}/extractFile.icf
    ${extractFilemodified}    set variable    ${LOCAL_TMP_DIR}/extractFile_modified.icf
    Extract icf    ${ric}    ${domain}    ${extractFile}    ${serviceName}
    ${fieldlist}    ${fidnumlist}    get and modify 2 item in icf    ${extractFile}    ${extractFilemodified}    ${ric}    ${domain}
    ...    ${fidvalue}
    Start Capture MTE Output    ${MTE}
    Insert icf    ${extractFilemodified}    ${serviceName}
    Extract icf    ${ric}    ${domain}    ${extractFile}    ${serviceName}
    ${modifyitem}    creat REAL modify item in icf    ${fieldlist}    ${newfidvalue}
    modify icf    ${extractFile}    ${extractFilemodified}    ${ric}    ${domain}    ${modifyitem[0]}    ${modifyitem[1]}
    Insert icf    ${extractFilemodified}    ${serviceName}
    Insert icf    ${extractFile}    ${serviceName}
    Stop Capture MTE Output    ${MTE}    1    15
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    Run Keyword And Continue On Failure    verify Extract and Insert in message    ${LOCAL_TMP_DIR}/capture_local.pcap    ${VENUE_DIR}    ${DAS_DIR}    ${pubRic}    ${fidnumlist}
    ...    ${fidvalue}    ${newfidvalue}
    [Teardown]    case teardown    ${extractFile}    ${extractFilemodified}    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify Deletion Delay
    [Documentation]    Automatic delete Instrument in LH cache after 5 days, RIC is dropped and GEDA Item dropped due to expiration is sent to the SMF log, Instrument is successfully deleted \ in LH cache after 5 days
    ...
    ...    Test Case - Verify Deletion Delay
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1891
    ${domain}    Get Preferred Domain
    ${serviceName}    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${currDateTime}    get date and time
    ${bkcurrDateTime}    Set Variable    ${currDateTime}
    ${StartOfDayTime}=    get value from MTE config    StartOfDayTime
    ${EndOfDayTime}=    get value from MTE config    EndOfDayTime
    ${currDateTime}    get date and time
    ${StartOfDayGMT}    Convert to GMT    ${StartOfDayTime}
    ${EndOfDayGMT}    Convert to GMT    ${EndOfDayTime}
    start mte    ${MTE}
    Drop ric    ${ric}    ${domain}    ${serviceName}
    wait smf log message after time    Drop message sent    ${currDateTime}
    Verify RIC Is Dropped In MTE Cache    ${MTE}    ${ric}
    Rollover a day    ${StartOfDayGMT}    ${EndOfDayGMT}    5
    wait smf log message after time    dropped due to expiration    ${currDateTime}
    Verify RIC Not In MTE Cache    ${MTE}    ${ric}
    ${bkcurrDateTime[0]}    ${bkcurrDateTime[1]}    ${bkcurrDateTime[2]}    ${bkcurrDateTime[3]}    ${bkcurrDateTime[4]}    ${bkcurrDateTime[5]}    add seconds to date
    ...    ${bkcurrDateTime[0]}    ${bkcurrDateTime[1]}    ${bkcurrDateTime[2]}    ${bkcurrDateTime[3]}    ${bkcurrDateTime[4]}    ${bkcurrDateTime[5]}
    ...    60
    ${res}    set date and time    ${bkcurrDateTime[0]}    ${bkcurrDateTime[1]}    ${bkcurrDateTime[2]}    ${bkcurrDateTime[3]}    ${bkcurrDateTime[4]}
    ...    ${bkcurrDateTime[5]}

*** Keywords ***
Calculate UpdateSince for REORG
    [Arguments]    ${exlFile}
    [Documentation]    Based on the last modified time of EXL to calculate the proper value for UpdateSince argument used in FMSCMD to trigger partial REORG
    ...
    ...    Remark :
    ...    For FMSCMD used for trigger partial REORG has following behaviour :
    ...    It allow 15 mins tolerance between last modified time of EXL files and UpdateSince value.
    ...    e.g.
    ...    last modified time = "2015-11-04 14:11:39" and UpdateSince = "2015-11-04 14:26:39" : this EXL file will be included in partial REORG
    ...    last modified time = "2015-11-04 14:11:39" and UpdateSince = "2015-11-04 14:26:40" : this EXL file will be excluded in partial REORG
    ...
    ...    Setting $(offsetInSecond} = 899 is because of above behaviour.
    ...    This could also ensure on the target EXL file will be included in partial REORG.
    ${offsetInSecond}=    set variable    899
    ${modifiedTime}=    Get Modified Time    ${exlFile}
    ${UpdateSince}=    add time to date    ${modifiedTime}    ${offsetInSecond} second    exclude_millis=yes
    [Return]    ${UpdateSince}

Set PE in EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${newPE}
    [Documentation]    Keyword - Modify PROD_PERM value in header of EXL file
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1718
    modify exl header    ${srcFile}    ${dstFile}    <it:PROD_PERM>${newPE}</it:PROD_PERM>

Trigger Partial REORG
    [Arguments]    ${startDateTime}    ${service}
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    25000    ${LOCAL_FMS_BIN}
    ...    Recon    --Services ${service}    --UpdatesSince "${startDateTime}"    --UseReconcileLXL false
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Verify RIC Published
    [Arguments]    ${remoteCapture}    ${exlFile}    ${ric}    ${domain}
    [Documentation]    Check if unsolicited response message in pcap file
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    ${contextIDs}=    Get Ric Fields from EXL    ${exlFile}    ${ric}    CONTEXT_ID
    ${constituents}=    get constituents from FidFilter    ${VENUE_DIR}    ${contextIDs[0]}
    Verify Unsolicited Response in Capture    ${localCapture}    ${DAS_DIR}    ${ric}    ${domain}    ${constituents}
    Remove Files    ${localCapture}

rebuild ric
    [Arguments]    ${serviceName}    ${ric}    ${domain}
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    25000    ${LOCAL_FMS_BIN}
    ...    rebuild    --RIC ${ric}    --Domain ${domain}    --HandlerName ${MTE}    --Services ${serviceName}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Extract icf
    [Arguments]    ${ric}    ${domain}    ${extractFile}    ${serviceName}
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    25000    ${LOCAL_FMS_BIN}
    ...    extract    --RIC ${ric}    --Domain ${domain}    --ExcludeNullFields false    --HandlerName ${MTE}    --OutputFile ${extractFile}
    ...    --Services ${serviceName}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Insert icf
    [Arguments]    ${insertFile}    ${serviceName}
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    25000    ${LOCAL_FMS_BIN}
    ...    insert    --InputFile ${insertFile}    --HandlerName ${MTE}    --Services ${serviceName}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Drop ric
    [Arguments]    ${ric}    ${domain}    ${serviceName}
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    25000    ${LOCAL_FMS_BIN}
    ...    drop    --RIC ${ric}    --Domain ${domain}    --HandlerName ${MTE}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Convert to GMT
    [Arguments]    ${SourceTime}
    ${DSTRIC}=    get value from MTE config    CHE-TimeZoneForConfigTimes
    ${currentGmtOffset}    get stat block field    ${MTE}    ${DSTRIC}    currentGMTOffset
    ${numOffset}    Convert To Number    ${currentGmtOffset}
    ${currentGmtOffset}    convert num to opposite    ${numOffset}
    ${StartTime}    ${lenTime}    separate string to list    ${SourceTime}    :
    ${StartTimeSec}=    Set Variable If    ${lenTime} == 3    ${StartTime[2]}    0
    ${currDateTime}    get date and time
    ${startDatetimeYear}    ${startDatetimeMonth}    ${startDatetimeDay}    ${startDatetimeHour}    ${startDatetimeMin}    ${startDatetimeSec}    add seconds to date
    ...    ${currDateTime[0]}    ${currDateTime[1]}    ${currDateTime[2]}    ${StartTime[0]}    ${StartTime[1]}    ${StartTimeSec}
    ...    ${currentGmtOffset}
    ${GMTTime}    create list    ${startDatetimeHour}    ${startDatetimeMin}    ${startDatetimeSec}
    [Return]    ${GMTTime}

Rollover a day
    [Arguments]    ${StartOfDayTime}    ${EndOfDayTime}    ${days}
    ${currDateTime}    get date and time
    ${startDatetimeYear}    ${startDatetimeMonth}    ${startDatetimeDay}    ${startDatetimeHour}    ${startDatetimeMin}    ${startDatetimeSec}    add seconds to date
    ...    ${currDateTime[0]}    ${currDateTime[1]}    ${currDateTime[2]}    ${StartOfDayTime[0]}    ${StartOfDayTime[1]}    ${StartOfDayTime[2]}
    ...    0
    ${endSec}=    Set Variable If    ${StartOfDayTime[0]} > ${EndOfDayTime[0]}    86399    -1
    ${startSec}=    Set Variable If    ${StartOfDayTime[0]} > ${EndOfDayTime[0]}    -1    86399
    : FOR    ${index}    IN RANGE    0    ${days}
    \    log    index is -----------------------${index}
    \    ${endDatetimeYear}    ${endDatetimeMonth}    ${endDatetimeDay}    ${endDatetimeHour}    ${endDatetimeMin}    ${endDatetimeSec}
    \    ...    add seconds to date    ${startDatetimeYear}    ${startDatetimeMonth}    ${startDatetimeDay}    ${EndOfDayTime[0]}
    \    ...    ${EndOfDayTime[1]}    ${EndOfDayTime[2]}    ${endSec}
    \    ${res}    set date and time    ${endDatetimeYear}    ${endDatetimeMonth}    ${endDatetimeDay}    ${endDatetimeHour}
    \    ...    ${endDatetimeMin}    ${endDatetimeSec}
    \    sleep    2s    ${currDateTime}
    \    ${startDatetimeYear}    ${startDatetimeMonth}    ${startDatetimeDay}    ${startDatetimeHour}    ${startDatetimeMin}    ${startDatetimeSec}
    \    ...    add seconds to date    ${endDatetimeYear}    ${endDatetimeMonth}    ${endDatetimeDay}    ${startDatetimeHour}
    \    ...    ${startDatetimeMin}    ${startDatetimeSec}    ${startSec}
    \    ${res}    set date and time    ${startDatetimeYear}    ${startDatetimeMonth}    ${startDatetimeDay}    ${startDatetimeHour}
    \    ...    ${startDatetimeMin}    ${startDatetimeSec}
    \    ${currDateTime}    get date and time
    \    wait smf log message after time    StartOfDay time occurred    ${currDateTime}

Get value from MTE config
    [Arguments]    ${fieldname}
    ${mteConfigFile}=    Get MTE Config File
    ${fieldvalue}=    get MTE config value    ${mteConfigFile}    ${fieldname}
    return from keyword if    '${fieldvalue}' != 'NOT FOUND'    ${fieldvalue}
    FAIL    No ${fieldname} found in venue config file: ${mteConfigFile}
