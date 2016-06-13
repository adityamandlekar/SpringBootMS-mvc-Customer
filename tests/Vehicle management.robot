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
    ${EXLfullpath}=    Get EXL For RIC    ${domain}    ${serviceName}    ${ric}
    ${EXLfile}=    Fetch From Right    ${EXLfullpath}    \\
    ${localEXLfile}=    set variable    ${LOCAL_TMP_DIR}/${EXLfile}
    ${long_ric}=    Create Unique RIC Name    32_chars_total
    Set RIC In EXL    ${EXLfullpath}    ${localEXLfile}    ${ric}    ${domain}    ${long_ric}
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    Start Capture MTE Output    ${remoteCapture}
    Load Single EXL File    ${localEXLfile}    ${serviceName}    ${CHE_IP}    --AllowRICChange true
    Wait For Persist File Update    5    60
    Stop Capture MTE Output    1    5
    ${newRic}    ${newPubRic}    Run Keyword And Continue On Failure    Verify RIC In MTE Cache    ${long_ric}
    Run Keyword And Continue On Failure    Verify RIC Published    ${remoteCapture}    ${localEXLfile}    ${newPubRic}    ${domain}
    Run Keyword And Continue On Failure    Verfiy Item Persisted    ${long_ric}    ${EMPTY}    ${domain}
    Load Single EXL File    ${EXLfullpath}    ${serviceName}    ${CHE_IP}    --AllowRICChange true
    Wait For Persist File Update
    [Teardown]    case teardown    ${localEXLfile}

Verify PE Change Behavior
    [Documentation]    Test Case - Verify PE Change Behavior : http://www.iajira.amers.ime.reuters.com/browse/CATF-1715
    Set Mangling Rule    UNMANGLED
    ${domain}    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${EXLfullpath}    Get EXL For RIC    ${domain}    ${serviceName}    ${ric}
    @{pe}=    get ric fields from EXL    ${EXLfullpath}    ${ric}    PROD_PERM
    ${penew}=    set variable    @{pe}[0]1
    ${exlfile}=    Fetch From Right    ${EXLfullpath}    \\
    ${exlmodified} =    set variable    ${LOCAL_TMP_DIR}/${exlfile}_modified.exl
    Set PE in EXL    ${EXLfullpath}    ${exlmodified}    ${penew}
    Start Capture MTE Output
    Load Single EXL File    ${exlmodified}    ${serviceName}    ${CHE_IP}
    Stop Capture MTE Output    1    15
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    Run Keyword And Continue On Failure    verify PE Change in message    ${LOCAL_TMP_DIR}/capture_local.pcap    ${pubRic}    ${pe}    ${penew}
    Load Single EXL File    ${EXLfullpath}    ${serviceName}    ${CHE_IP}
    Load Mangling Settings
    Wait For Persist File Update
    [Teardown]    case teardown    ${exlmodified}    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify New Item Creation via FMS
    [Documentation]    Verify that a new item can be created by adding it to an EXL file and loading it via FMS
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1711
    Start MTE
    ${domain}=    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${EXL_File}=    Get EXL For RIC    ${domain}    ${serviceName}    ${ric}
    ${uniqueRic}=    Create Unique RIC Name
    add ric to exl file    ${EXL_File}    ${LOCAL_TMP_DIR}/output.exl    ${uniqueRic}
    Load Single EXL File    ${LOCAL_TMP_DIR}/output.exl    ${serviceName}    ${CHE_IP}
    Wait For FMS Reorg
    Verify RIC In MTE Cache    ${uniqueRic}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/output.exl

Partial REORG on EXL Change
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1791
    ${domain}    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${exlFile}=    Get EXL For RIC    ${domain}    ${serviceName}    ${ric}
    ${fieldName}=    set variable    DSPLY_NAME
    ${fieldValueNew}=    set variable    PARTIALREORGTEST
    ${fieldValueOrg}=    Set Field Value in EXL    ${exlFile}    ${ric}    ${domain}    ${fieldName}    ${fieldValueNew}
    Start Capture MTE output
    ${UpdateSince}=    Calculate UpdateSince for REORG    ${exlFile}
    Trigger Partial REORG    ${UpdateSince}    ${serviceName}
    Stop Capture MTE output    1    15
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    ${verifyFIDs}=    Create List    3
    ${verifyValues}=    Create List    ${fieldValueNew}
    Run Keyword And Continue On Failure    verify correction change in message    ${LOCAL_TMP_DIR}/capture_local.pcap    ${pubRic}    ${verifyFIDs}    ${verifyValues}
    ${fieldValueOrg}=    Set Field Value in EXL    ${exlFile}    ${ric}    ${domain}    ${fieldName}    ${fieldValueOrg}
    Load Single EXL File    ${exlFile}    ${serviceName}    ${CHE_IP}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify RIC rename handled correctly
    [Documentation]    Verify RIC rename appeared in the cache dump file and updated persist file
    start MTE
    Comment    //Setup variables for test
    ${domain}=    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${RIC_Before_Rename}    ${Published_RIC_Before_Rename}    Get RIC From MTE Cache    ${domain}
    ${RIC_Before_Rename_Trunc}=    Get Substring    ${RIC_Before_Rename}    0    14
    ${RIC_After_Rename}=    Create Unique RIC Name    ${RIC_Before_Rename_Trunc}
    ${EXLfullpath}=    Get EXL For RIC    ${domain}    ${serviceName}    ${RIC_Before_Rename}
    ${EXLfile}    Fetch From Right    ${EXLfullpath}    \\
    ${LocalEXLfullpath}    set variable    ${LOCAL_TMP_DIR}/${EXLfile}
    ${contextIDs}=    Get Ric Fields from EXL    ${EXLfullpath}    ${RIC_Before_Rename}    CONTEXT_ID
    ${constituent_list}=    Get Constituents From FidFilter    ${contextIDs[0]}
    Comment    //Start test. Test 1: Check that the new RIC that we are about to create is NOT already in the cache
    Start Capture MTE Output
    Copy File    ${EXLfullpath}    ${LocalEXLfullpath}
    Load Single EXL File    ${LocalEXLfullpath}    ${serviceName}    ${CHE_IP}    --AllowRICChange true
    Wait For FMS Reorg
    Verify RIC NOT In MTE Cache    ${RIC_After_Rename}
    Comment    //Start test. Test 2: Check that the RIC can be renamed and that the existing RIC is no longer in the cache
    Start Capture MTE Output
    Set RIC in EXL    ${EXLfullpath}    ${LocalEXLfullpath}    ${RIC_Before_Rename}    ${domain}    ${RIC_After_Rename}
    Load Single EXL File    ${LocalEXLfullpath}    ${serviceName}    ${CHE_IP}    --AllowRICChange true
    Wait For FMS Reorg
    Verify RIC NOT In MTE Cache    ${RIC_Before_Rename}
    ${ric}    ${Published_RIC_After_Rename}    Verify RIC In MTE Cache    ${RIC_After_Rename}
    Send TRWF2 Refresh Request    ${Published_RIC_After_Rename}    ${domain}
    Wait For Persist File Update    5    60
    Stop Capture MTE Output
    Get Remote File    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local_2.pcap
    verify Unsolicited Response In Capture    ${LOCAL_TMP_DIR}/capture_local_2.pcap    ${Published_RIC_After_Rename}    ${domain}    ${constituent_list}
    Verfiy Item Persisted    ${RIC_After_Rename}    ${EMPTY}    ${domain}
    Comment    //Start test. Test 3: Check that the new RIC can be renamed back to the original name.
    Comment    //This also reverts the state back to as the begining of the test
    Start Capture MTE Output
    Load Single EXL File    ${EXLfullpath}    ${serviceName}    ${CHE_IP}    --AllowRICChange true
    Wait For FMS Reorg
    Verify RIC NOT In MTE Cache    ${RIC_After_Rename}
    ${ric}    ${Published_RIC_Before_Rename}    Verify RIC In MTE Cache    ${RIC_Before_Rename}
    Send TRWF2 Refresh Request    ${Published_RIC_Before_Rename}    ${domain}
    Wait For Persist File Update    5    60
    Stop Capture MTE Output
    Get Remote File    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local_3.pcap
    Verify Unsolicited Response In Capture    ${LOCAL_TMP_DIR}/capture_local_3.pcap    ${Published_RIC_Before_Rename}    ${domain}    ${constituent_list}
    Verfiy Item Persisted    ${RIC_Before_Rename}    ${EMPTY}    ${domain}
    [Teardown]    case teardown    ${LocalEXLfullpath}    ${LOCAL_TMP_DIR}/capture_local_2.pcap    ${LOCAL_TMP_DIR}/capture_local_3.pcap

Verify FMS Rebuild
    [Documentation]    Force a rebuild of RIC via FMS and verify that a rebuild message is published for the RIC
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1849
    Start MTE
    ${domain}    Get Preferred Domain
    ${serviceName}    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    Start Capture MTE Output
    rebuild ric    ${serviceName}    ${ric}    ${domain}
    Stop Capture MTE Output
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    Run Keyword And Continue On Failure    verify all response message num    ${LOCAL_TMP_DIR}/capture_local.pcap    ${pubRic}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Drop a RIC by deleting EXL File and Full Reorg
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1850
    ...    To verify whether the RICs in a exl file can be dropped if the exl file is deleted.
    [Setup]    Drop a RIC Case Setup
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${exlFullFileName}=    get EXL for RIC    ${domain}    ${serviceName}    ${ric}
    Append To List    ${processedEXLs}    ${exlFullFileName}
    ${exlFilePath}    ${exlFileName}    Split Path    ${exlFullFileName}
    copy File    ${exlFullFileName}    ${LOCAL_TMP_DIR}/${exlFileName}
    remove file    ${exlFullFileName}
    Set To Dictionary    ${backupEXLs}    ${LOCAL_TMP_DIR}/${exlFileName}    ${exlFullFileName}
    ${currentDateTime}    get date and time
    Load All EXL Files    ${serviceName}    ${CHE_IP}
    wait smf log message after time    Drop message sent    ${currentDateTime}
    Verify RIC is Dropped In MTE Cache    ${ric}
    [Teardown]    Drop a RIC Case Teardown    ${LOCAL_TMP_DIR}/${exlFileName}

Drop a RIC by deleting EXL file from LXL file
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1924
    ...
    ...    Find a RIC associated exl file. Create LXL file with all exl files for the service except the founded one and place the lxl file to FMAREA/Service/System Files/Reconcile Files folder. \ After reconcile, verify RICs is dropped.
    ${domain}    Get Preferred Domain
    ${service}    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${exlFullFileName}=    get EXL for RIC    ${domain}    ${service}    ${ric}
    ${exlFilePath}    ${exlFileName}    Split Path    ${exlFullFileName}
    ${service_dir}    Fetch From Left    ${exlFilePath}    \\${service}\\
    ${recon_files_dir}=    set variable    ${service_dir}\\${service}\\System Files\\Reconcile Files
    ${exl_path_in_lxl}=    Get exl file path for lxl file    ${exlFilePath}
    ${tmp_lxl}    set variable    ${recon_files_dir}\\tmp.lxl
    ${exl_file_list} =    List Files In Directory    ${exlFilePath}    *.exl
    Remove Values From List    ${exl_file_list}    ${exlFileName}
    ${lxl_content}=    Build LXL File    ${exl_path_in_lxl}    ${exl_file_list}
    Create File    ${tmp_lxl}    ${lxl_content}
    Run FmsCmd    ${CHE_IP}    Recon    --Services ${service}    --InputFile "${tmp_lxl}"    --HandlerName ${MTE}    UseReconcileLXL true
    Wait For Persist File Update
    Run Keyword And Continue On Failure    Verify RIC is Dropped In MTE Cache    ${ric}
    Run FmsCmd    ${CHE_IP}    UnDrop    --Services ${service}    --InputFile "${exlFullFileName}"    --HandlerName ${MTE}
    Wait For Persist File Update
    Verify RIC In MTE Cache    ${ric}
    [Teardown]    case teardown    ${tmp_lxl}

Verify Reconcile of Cache
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1848
    ...    To verify whether a new RIC can be added and a old RIC can be dropped via reconcile
    ${mteConfigFile}=    Get MTE Config File
    ${SendRefreshForFullReorg}    Get MTE Config Value    ${mteConfigFile}    SendRefreshForFullReorg
    Should Be True    ${SendRefreshForFullReorg} != '1'    SendRefreshForFullReorg should be disabled
    ${domain}    Get Preferred Domain
    ${serviceName}    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${exlFullFileName}=    get EXL for RIC    ${domain}    ${serviceName}    ${ric}
    ${exlFilePath}    ${exlFileName}    Split Path    ${exlFullFileName}
    copy File    ${exlFullFileName}    ${LOCAL_TMP_DIR}/${exlFileName}
    ${newRICName}    Create Unique RIC Name
    Set Symbol In EXL    ${exlFullFileName}    ${exlFullFileName}    ${ric}    ${domain}    ${newRICName}
    Set RIC In EXL    ${exlFullFileName}    ${exlFullFileName}    ${ric}    ${domain}    ${newRICName}
    ${currentDateTime}    get date and time
    Run Keyword And Continue On Failure    Load All EXL Files    ${serviceName}    ${CHE_IP}    --UseReconcileLXL true
    copy File    ${LOCAL_TMP_DIR}/${exlFileName}    ${exlFullFileName}
    wait smf log message after time    FMS REORG DONE    ${currentDateTime}
    Verify RIC In MTE Cache    ${newRICName}
    Run Keyword And Continue On Failure    Verify RIC is Dropped In MTE Cache    ${ric}
    Load Single EXL File    ${exlFullFileName}    ${serviceName}    ${CHE_IP}
    Verify RIC In MTE Cache    ${ric}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/${exlFileName}

Verify SIC rename handled correctly
    [Documentation]    Verify SIC rename appeared in the cache dump file and updated persist file
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1893
    ${domain}=    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${result}=    get RIC fields from cache    1    ${domain}    ${EMPTY}
    ${RIC} =    set variable    ${result[0]['RIC']}
    ${SIC_Before_Rename} =    set variable    ${result[0]['SIC']}
    ${SIC_After_Rename}=    set variable    ${SIC_Before_Rename}TestSIC
    ${Symbol_After_Rename}=    Get Substring    ${SIC_After_Rename}    2
    ${EXLfullpath}=    Get EXL For RIC    ${domain}    ${serviceName}    ${RIC}
    ${EXLfile}    Fetch From Right    ${EXLfullpath}    \\
    ${LocalEXLfullpath}=    set variable    ${LOCAL_TMP_DIR}/${EXLfile}
    Copy File    ${EXLfullpath}    ${LocalEXLfullpath}
    Set Symbol In EXL    ${EXLfullpath}    ${LocalEXLfullpath}    ${RIC}    ${domain}    ${Symbol_After_Rename}
    Load Single EXL File    ${LocalEXLfullpath}    ${serviceName}    ${CHE_IP}    --AllowSICChange true
    remove file    ${LocalEXLfullpath}
    ${ricFields}=    Get All Fields For RIC From Cache    ${RIC}
    ${SIC_1}=    set variable    ${ricFields['SIC']}
    Should Be Equal    ${SIC_1}    ${SIC_After_Rename}
    Wait For Persist File Update    5    60
    Verfiy Item Persisted    ${EMPTY}    ${SIC_After_Rename}    ${domain}
    Comment    //fallback
    Load Single EXL File    ${EXLfullpath}    ${serviceName}    ${CHE_IP}    --AllowSICChange true
    ${ricFields}=    Get All Fields For RIC From Cache    ${RIC}
    ${SIC_2}=    set variable    ${ricFields['SIC']}
    Should Be Equal    ${SIC_2}    ${SIC_Before_Rename}
    Wait For Persist File Update    5    60
    Verfiy Item Persisted    ${EMPTY}    ${SIC_Before_Rename}    ${domain}
    [Teardown]    Load Single EXL File    ${EXLfullpath}    ${serviceName}    ${CHE_IP}    --AllowSICChange true

Verify FMS Extract and Insert
    [Documentation]    Extract existing RIC fields and values \ into an .icf file using FmsCmd. Modify some of the values and re-load the .icf file using FmsCmd.Verify that the modified values are published.
    ...    Test Case - Verify FMS Extract and Insert : http://www.iajira.amers.ime.reuters.com/browse/CATF-1892
    Start MTE
    ${domain}    Get Preferred Domain
    ${serviceName}    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${beforeExtractFile}    set variable    ${LOCAL_TMP_DIR}/beforeExtractFile.icf
    ${afterExtractFile}    set variable    ${LOCAL_TMP_DIR}/afterExtractFile.icf
    ${beforeLocalPcap}    set variable    ${LOCAL_TMP_DIR}/capture_localBefore.pcap
    ${afterLocalPcap}    set variable    ${LOCAL_TMP_DIR}/capture_localAfter.pcap
    Extract ICF    ${ric}    ${domain}    ${beforeExtractFile}    ${serviceName}
    ${FidList}    get REAL Fids in icf file    ${beforeExtractFile}    3
    ${newFidNameValue}    ${newFidNumValue}    Create Fid Value Pair    ${FidList}
    ${iniFidNameValue}    ${iniFidNumValue}    Create Fid Value Pair    ${FidList}
    Comment    //set FID 'before' values
    modify REAL items in icf    ${beforeExtractFile}    ${beforeExtractFile}    ${ric}    ${domain}    ${iniFidNameValue}
    Start Capture MTE Output
    Insert ICF    ${beforeExtractFile}    ${serviceName}
    Stop Capture MTE Output    1    15
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${beforeLocalPcap}
    ${initialAllFidsValues}    get FidValue in message    ${beforeLocalPcap}    ${pubRic}    UPDATE
    Comment    //set FID 'after' values
    modify REAL items in icf    ${beforeExtractFile}    ${afterExtractFile}    ${ric}    ${domain}    ${newFidNameValue}
    Start Capture MTE Output
    Insert ICF    ${afterExtractFile}    ${serviceName}
    Stop Capture MTE Output    1    15
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${afterLocalPcap}
    ${newAllFidsValues}    get FidValue in message    ${afterLocalPcap}    ${pubRic}    UPDATE
    Comment    //Verify \
    Dictionary Should Contain Sub Dictionary    ${initialAllFidsValues}    ${iniFidNumValue}
    Dictionary Should Contain Sub Dictionary    ${newAllFidsValues}    ${newFidNumValue}
    ${modifiedFidNum}    Get Dictionary Keys    ${iniFidNumValue}
    Remove From Dictionary    ${initialAllFidsValues}    @{modifiedFidNum}
    Remove From Dictionary    ${newAllFidsValues}    @{modifiedFidNum}
    Dictionaries Should Be Equal    ${initialAllFidsValues}    ${newAllFidsValues}
    [Teardown]    case teardown    ${beforeExtractFile}    ${afterExtractFile}    ${beforeLocalPcap}    ${afterLocalPcap}

Verify Deletion Delay
    [Documentation]    Delete an instrument. \ Rollover system time through 5 startOfDay cycles.\ Verify that the MTE cache correctly indicates that the instrument has been dropped and how many deletion delay days are left. \ After the 5th day, verify the instrument is deleted from the MTE cache. \ Reset the Thunderdome box time back to correct time.
    ...
    ...    Test Case - Verify Deletion Delay
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1891
    [Setup]    Disable MTE Clock Sync
    start mte
    ${domain}    Get Preferred Domain
    ${serviceName}    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${StartOfDayGMT}    Get Start GMT Time
    Drop ric    ${ric}    ${domain}    ${serviceName}
    Comment    Stopping EventScheduler elimintates extra processing that is done at each start of day and many FMSClient:SocketException messages. We are only interested in the deletion delay change.    This will be restarted during case teardown.
    ${result}=    Run Commander    process    stop EventScheduler
    : FOR    ${daysLeft}    IN RANGE    5    0    -1
    \    ${ricFields}=    Get All Fields For RIC From Cache    ${ric}
    \    Should Be Equal    ${ricFields['PUBLISHABLE']}    FALSE
    \    Should Be Equal As Integers    ${ricFields['DELETION_DELAY_DAYS_REMAINING']}    ${daysLeft}
    \    Should Be True    ${ricFields['NON_PUBLISHABLE_REASONS'].find('InDeletionDelay')} != -1
    \    Rollover MTE Start Date    ${StartOfDayGMT}
    Verify RIC Not In MTE Cache    ${ric}
    [Teardown]    Correct MTE Machine Time

Verify Drop and Undrop from FMSCmd
    [Documentation]    Verify Drop/Undrop form FMSCmd, 1) Verify MTE is running.
    ...    2) Start output capture.
    ...    3) Generate Drop from FMSCmd,
    ...    4) Verify item is dropped in MTE cache.
    ...    5) Stop output capture
    ...    6) Verify an Item Drop was published (MsgClass: \ TRWF_MSG_MC_ITEM_STATUS, StreamState: TRWF_MSG_SST_CLOSED)
    ...    7) Start output capture.
    ...    8) Generate Undrop from FMSCmd,
    ...    9) Verify item is in MTE cache.
    ...    10) Stop output capture
    ...    11) verify a response was published.
    ...
    ...    Test Case - Verify Drop/Undrop form FMSCmd
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2009
    start mte
    ${domain}    Get Preferred Domain
    ${serviceName}    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${mteConfigFile}=    Get MTE Config File
    ${currDateTime}    get date and time
    Start Capture MTE Output
    Drop ric    ${ric}    ${domain}    ${serviceName}
    wait smf log message after time    Drop message sent    ${currDateTime}
    Verify RIC Is Dropped In MTE Cache    ${ric}
    Stop Capture MTE Output
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    verify DROP message in itemstatus messages    ${LOCAL_TMP_DIR}/capture_local.pcap    ${pubRic}
    Start Capture MTE Output
    Undrop ric    ${ric}    ${domain}    ${serviceName}
    wait smf log message after time    was Undropped    ${currDateTime}
    Verify RIC In MTE Cache    ${ric}
    Stop Capture MTE Output
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    verify_all_response_message_num    ${LOCAL_TMP_DIR}/capture_local.pcap    ${pubRic}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

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
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    Recon    --Services ${service}
    ...    --UpdatesSince "${startDateTime}"    --UseReconcileLXL false
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Verify RIC Published
    [Arguments]    ${remoteCapture}    ${exlFile}    ${ric}    ${domain}
    [Documentation]    Check if unsolicited response message in pcap file
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    ${contextIDs}=    Get Ric Fields from EXL    ${exlFile}    ${ric}    CONTEXT_ID
    ${constituents}=    get constituents from FidFilter    ${contextIDs[0]}
    Verify Unsolicited Response in Capture    ${localCapture}    ${ric}    ${domain}    ${constituents}
    Remove Files    ${localCapture}

rebuild ric
    [Arguments]    ${serviceName}    ${ric}    ${domain}
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    rebuild    --RIC ${ric}
    ...    --Domain ${domain}    --HandlerName ${MTE}    --Services ${serviceName}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Drop ric
    [Arguments]    ${ric}    ${domain}    ${serviceName}
    ${currDateTime}    get date and time
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    drop    --RIC ${ric}
    ...    --Domain ${domain}    --HandlerName ${MTE}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}
    wait smf log message after time    Drop    ${currDateTime}

Get Start GMT Time
    ${mteConfigFile}=    Get MTE Config File
    ${StartOfDayTime}=    get MTE config value    ${mteConfigFile}    StartOfDayTime
    ${StartOfDayGMT}    Convert to GMT    ${StartOfDayTime}
    [Return]    ${StartOfDayGMT}

Convert to GMT
    [Arguments]    ${localTime}
    [Documentation]    convert the local time to GMT
    ${mteConfigFile}=    Get MTE Config File
    ${DSTRIC}=    get MTE config value    ${mteConfigFile}    CHE-TimeZoneForConfigTimes
    ${currentGmtOffset}    get stat block field    ${MTE}    ${DSTRIC}    currentGMTOffset
    ${currDateTime}    get date and time
    ${GMTTime}    Subtract Time From date    ${currDateTime[0]}.${currDateTime[1]}.${currDateTime[2]} ${localTime}    ${currentGmtOffset}    date_format=%Y.%m.%d \ %H:%M    result_format=%H:%M
    [Return]    ${GMTTime}

Drop a RIC Case Setup
    [Documentation]    The setup will get FMS service name to ${serviceName} and get perferred domain to ${domain}.
    ...
    ...    A list variable @{processedEXLs} will be created. all exl files which should be reloaded when teardown can be added into @{processedEXLs}.
    ...
    ...    A dictionary variable @{backupedEXLs} will be created as well. If you modify/delete EXLs, the orginal should be backup to a local path. Both orginal file path and backup file should be added into @{backupedEXLs}
    ...    e.g. Set To Dictionary |${backupEXLs} |${backuppath} | ${orgpath}
    ...    Teardown will copy ${backuppath} to ${orgpath}
    @{processedEXLs}    create list
    Set Suite Variable    @{processedEXLs}
    ${backupEXLs}    Create Dictionary
    Set Suite Variable    ${backupEXLs}
    ${serviceName}    Get FMS Service Name
    Set Suite Variable    ${serviceName}
    ${domain}    Get Preferred Domain
    Set Suite Variable    ${domain}

Drop a RIC Case Teardown
    [Arguments]    @{tmpfiles}
    [Documentation]    The teardown will restore all backup EXL in @{backupEXLs}, and reload all exl files in @{processedEXLs}, and remove temporary files.
    : FOR    ${backuppath}    IN    @{backupEXLs}
    \    ${orgpath}    Get From Dictionary    ${backupEXLs}    ${backuppath}
    \    Copy File    ${backuppath}    ${orgpath}
    : FOR    ${exlfile}    IN    @{processedEXLs}
    \    Load Single EXL File    ${exlfile}    ${serviceName}    ${CHE_IP}
    Case Teardown    @{tmpfiles}

Create Fid Value Pair
    [Arguments]    ${FidList}
    [Documentation]    Use a Fid name list to create Fid Value dictionary, only for REAL type fid
    ${fidnamevalue}    Create Dictionary
    ${fidnumvalue}    Create Dictionary
    : FOR    ${Fid}    IN    @{FidList}
    \    ${fidNum}    get FID ID by FIDName    ${Fid}
    \    ${value} =    Generate Random String    3    [NUMBERS]
    \    Set To Dictionary    ${fidnamevalue}    ${Fid}    1${value}
    \    Set To Dictionary    ${fidnumvalue}    ${fidNum}    1${value}
    [Return]    ${fidnamevalue}    ${fidnumvalue}

Correct MTE Machine Time
    [Documentation]    To correct Linux time and restart SMF, restart SMF because currently FMS client have a bug now, if we change the MTE Machine time when SMF running, FMS client start to report exception like below, and in this case we can't use FMS client correclty:
    ...    FMSClient:SocketException - ClientImpl::connect:connect (111); /ThomsonReuters/EventScheduler/EventScheduler; 18296; 18468; 0000235f; 07:00:00;
    ...
    ...    In addition, on a vagrant VirtualBox, restore the VirtualBox Guest Additions service, which includes clock sync with the host.
    stop smf
    ${RIDEMachineTime}    Get Current Date    UTC    result_format=datetime
    ${res}    set date and time    ${RIDEMachineTime.year}    ${RIDEMachineTime.month}    ${RIDEMachineTime.day}    ${RIDEMachineTime.hour}    ${RIDEMachineTime.minute}
    ...    ${RIDEMachineTime.second}
    Restore MTE Clock Sync
    start smf

Undrop ric
    [Arguments]    ${ric}    ${domain}    ${serviceName}
    ${currDateTime}    get date and time
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    undrop    --RIC ${ric}
    ...    --Domain ${domain}    --HandlerName ${MTE}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}
    wait smf log message after time    Undrop    ${currDateTime}

Disable MTE Clock Sync
    [Documentation]    If running on a vagrant VirtualBox, disable the VirtualBox Guest Additions service. \ This will allow the test to change the clock on the VM. \ Otherwise, VirtualBox will immediately reset the VM clock to keep it in sync with the host machine time.
    ${result}=    Execute Command    if [ -f /etc/init.d/vboxadd-service ]; then service vboxadd-service stop; fi

Restore MTE Clock Sync
    [Documentation]    If running on a vagrant VirtualBox, re-enable the VirtualBox Guest Additions service. \ This will resync the VM clock to the host machine time.
    ${result}=    Execute Command    if [ -f /etc/init.d/vboxadd-service ]; then service vboxadd-service start; fi
