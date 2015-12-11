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
    Run Keyword And Continue On Failure    verify PE Change in message    ${LOCAL_TMP_DIR}/capture_local.pcap    ${VENUE_DIR}    ${DAS_DIR}    ${pubRic}    @{pe}[0]
    ...    ${penew}
    Load Single EXL File    ${exlfile}    ${serviceName}    ${CHE_IP}    25000
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
    [Documentation]    Test Case - Verify FMS Rebuild : http://www.iajira.amers.ime.reuters.com/browse/CATF-1849
    ${mteConfigFile}    Get MTE Config File
    ${domain}    Get Preferred Domain
    ${serviceName}    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    Start MTE    ${MTE}
    Start Capture MTE Output    ${MTE}
    rebuild ric    ${serviceName}    ${ric}    ${domain}
    sleep    5s
    Stop Capture MTE Output    ${MTE}
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    Run Keyword And Continue On Failure    verify FMS rebuild in message    ${LOCAL_TMP_DIR}/capture_local.pcap    ${VENUE_DIR}    ${DAS_DIR}    ${ric}
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
    @{modifiedTimeInList}=    Get Time    year month day hour min sec    ${modifiedTime}
    @{UpdateSinceInList}=    add seconds to date    @{modifiedTimeInList}[0]    @{modifiedTimeInList}[1]    @{modifiedTimeInList}[2]    @{modifiedTimeInList}[3]    @{modifiedTimeInList}[4]
    ...    @{modifiedTimeInList}[5]    ${offsetInSecond}    ${True}
    ${UpdateSince}=    set variable    "@{UpdateSinceInList}[0]-@{UpdateSinceInList}[1]-@{UpdateSinceInList}[2] @{UpdateSinceInList}[3]:@{UpdateSinceInList}[4]:@{UpdateSinceInList}[5]"
    [Return]    ${UpdateSince}

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
