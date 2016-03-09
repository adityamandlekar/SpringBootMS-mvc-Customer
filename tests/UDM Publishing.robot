*** Settings ***
Suite Setup       Suite Setup with Playback
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
Empty Payload Detection with Blank FIDFilter
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1988
    ...
    ...    Restart MTE with empty FIDFilter file. Verify no update messages with playback data. Restart MTE with restored FIDFilter file
    ${fileList}=    backup remote cfg file    ${VENUE_DIR}    FIDFilter.txt
    ${fidfilterFile}    set variable    ${fileList[0]}
    ${fidfilterBackup}    set variable    ${fileList[1]}
    ${emptyFidFilter}    set variable    ${LOCAL_TMP_DIR}/empty_FIDFilter.txt
    Create File    ${emptyFidFilter}
    Stop MTE
    Push File to Remote and Restart MTE    ${emptyFidFilter}    ${fidfilterFile}
    ${service}    Get FMS Service Name
    ${pcapFileName} =    Generate PCAP File Name    ${service}    ${TEST NAME}
    Run Keyword And Continue On Failure    Verify No Realtime Update    ${pcapFileName}
    Stop MTE
    Restore Remote and Restart MTE    ${fidfilterFile}    ${fidfilterBackup}
    [Teardown]    case teardown    ${emptyFidFilter}

Validate Downstream FID publication
    [Documentation]    Verify if MTE has publish fids that matches fids defined in fidfilter file
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1632
    Start MTE
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    ${mteConfigFile}    Get MTE Config File
    ${serviceName}    Get FMS Service Name
    ${fmsFilterString}    get MTE config value    ${mteConfigFile}    FMS    ${serviceName}    FilterString
    ${contextIds}    get context ids from fms filter string    ${fmsFilterString}
    : FOR    ${contextId}    IN    @{contextIds}
    \    ${ricFiledList}    get ric fields from cache    1    ${EMPTY}    ${contextId}
    \    ${pubRic}=    set variable    ${ricFiledList[0]['PUBLISH_KEY']}
    \    ${domain}=    set variable    ${ricFiledList[0]['DOMAIN']}
    \    Start Capture MTE Output    ${remoteCapture}
    \    Send TRWF2 Refresh Request    ${pubRic}    ${domain}
    \    Stop Capture MTE Output    60
    \    get remote file    ${remoteCapture}    ${localCapture}
    \    Verify Message Fids are in FIDfilter    ${localCapture}    ${pubRic}    ${domain}    ${contextId}
    [Teardown]    case teardown    ${localCapture}

Validate Downstream FID publication from Reconcile
    [Documentation]    Validate output from MTE after manual triggered Reconcile against FIDFilter.txt
    Start Capture MTE Output    ${REMOTE_TMP_DIR}/capture.pcap
    Stop MTE
    Delete Persist Files
    Start MTE
    Wait For FMS Reorg
    Stop Capture MTE Output
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    verify FIDfilter FIDs are in message    ${LOCAL_TMP_DIR}/capture_local.pcap
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify Outbound Heartbeats
    [Documentation]    Verify if MTE has publish heartbeat at specified interval
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1721
    Start MTE
    Start Capture MTE Output
    Stop Capture MTE Output    5    10
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    verify MTE heartbeat in message    ${LOCAL_TMP_DIR}/capture_local.pcap    1
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify Downstream Recovery Functions
    [Documentation]    This test uses DataView to send refresh request. MTE response will be captured in pcap and analysed with solicited flag for all possible constituents for the RIC
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1707
    Start MTE
    ${domain}=    Get Preferred Domain
    ${ric_contextid_list}=    get RIC fields from cache    1    ${domain}    ${EMPTY}
    ${ric}=    set variable    ${ric_contextid_list[0]['RIC']}
    ${contextId}=    set variable    ${ric_contextid_list[0]['CONTEXT_ID']}
    ${pubRic}=    set variable    ${ric_contextid_list[0]['PUBLISH_KEY']}
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    Start Capture MTE Output    ${remoteCapture}
    Send TRWF2 Refresh Request    ${pubRic}    ${domain}
    Stop Capture MTE Output    5    10
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    ${constituents}=    get constituents from FidFilter    ${contextId}
    Verify Unsolicited Response in Capture    ${localCapture}    ${pubRic}    ${domain}    ${constituents}
    [Teardown]    case teardown    ${localCapture}

Verify Common Required FID output
    [Documentation]    Verify the common fid in the output, http://www.iajira.amers.ime.reuters.com/browse/CATF-1847
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    ${serviceName}    Get FMS Service Name
    Start MTE
    Start Capture MTE Output    ${remoteCapture}
    ${currentDateTime}    get date and time
    Rebuild FMS service    ${serviceName}
    wait smf log message after time    Finished Sending Images    ${currentDateTime}
    Stop Capture MTE Output
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    ${mteConfigFile}=    Get MTE Config File
    ${domain}=    Get Preferred Domain
    @{ric_contextid_list}    get ric fields from cache    1    ${domain}    ${EMPTY}
    ${publishKey}=    set variable    ${ric_contextid_list[0]['PUBLISH_KEY']}
    ${contextId}=    set variable    ${ric_contextid_list[0]['CONTEXT_ID']}
    Verify DDS_DSO_ID    ${localCapture}    ${publishKey}
    @{labelIDs}=    get MTE config list by section    ${mteConfigFile}    Publishing    LabelID
    Verify SPS_SP_RIC    ${localCapture}    ${publishKey}    ${labelIDs[0]}
    Verify CONTEXT_ID    ${localCapture}    ${publishKey}    ${contextId}
    Verify MC_LABEL    ${localCapture}    ${publishKey}    ${labelIDs[0]}
    Verify MC_REC_LAB    ${localCapture}    ${publishKey}    ${labelIDs[0]}
    Verify UNCOMP_NAM    ${localCapture}    ${publishKey}
    Verify CMP_NME_ET    ${localCapture}    ${publishKey}
    Verify SetID In Response    ${localCapture}    ${publishKey}
    [Teardown]    case teardown    ${localCapture}

Verify Message Key Name is Compressed
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1884
    ...    ensure all TD CHE releases message key name compression is enabled
    ${domain}=    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${EXLfullpath}=    Get EXL For RIC    ${domain}    ${serviceName}    ${ric}
    ${EXLfile}=    Fetch From Right    ${EXLfullpath}    \\
    ${localEXLfile}=    set variable    ${LOCAL_TMP_DIR}/${EXLfile}
    ${long_ric}=    Create Unique RIC Name    32_chars_total
    Set RIC In EXL    ${EXLfullpath}    ${localEXLfile}    ${ric}    ${domain}    ${long_ric}
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    Start Capture MTE Output    ${remoteCapture}
    Load Single EXL File    ${localEXLfile}    ${serviceName}    ${CHE_IP}    --AllowRICChange true
    Wait For Persist File Update    5    60
    Stop Capture MTE Output    1    5
    get remote file    ${remoteCapture}    ${localCapture}
    ${mangle}    Fetch From Left    ${pubRic}    ${ric}
    verify key compression in message    ${localCapture}    ${mangle}${long_ric}
    Load Single EXL File    ${EXLfullpath}    ${serviceName}    ${CHE_IP}    --AllowRICChange true
    [Teardown]    case teardown    ${localCapture}

Verify SPS RIC is published
    [Documentation]    Verify SPS RIC and SPS Input Stats RIC are published.
    ...    Since Recon creates the ddnLabels.xml file, we cannot verify that the SPS RIC name is defined using the correct rules in the production label files.
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1757
    ${mteConfigFile}=    Get MTE Config File
    @{labelIDs}=    get MTE config list by section    ${mteConfigFile}    Publishing    LabelID
    ${SPSric}=    Get SPS RIC From Label File    @{labelIDs}[0]
    ${SPSric_input_stats}=    set variable    ${SPSric}_INS
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    Start Capture MTE Output    ${remoteCapture}
    Stop Capture MTE Output    5    10
    get remote file    ${remoteCapture}    ${localCapture}
    Verify Unsolicited Response in Capture    ${localCapture}    ${SPSric}    SERVICE_PROVIDER_STATUS    0
    Verify Unsolicited Response in Capture    ${localCapture}    ${SPSric_input_stats}    SERVICE_PROVIDER_STATUS    0
    Verify Unsolicited Response in Capture    ${localCapture}    ${SPSric}    SERVICE_PROVIDER_STATUS    1
    Verify Unsolicited Response in Capture    ${localCapture}    ${SPSric_input_stats}    SERVICE_PROVIDER_STATUS    1
    [Teardown]    case teardown    ${localCapture}

Verify DDS RIC is published
    [Documentation]    Verify DDS RIC is published
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1758
    ${FiveZeros}=    set variable    00000
    ${mteConfigFile}=    Get MTE Config File
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    @{labelIDs}=    get MTE config list by section    ${mteConfigFile}    Publishing    LabelID
    : FOR    ${labelID}    IN    @{labelIDs}
    \    ${Length}=    Get Length    ${label_ID}
    \    ${OffSet}=    Evaluate    5 - ${Length}
    \    ${ZeroPaddedLableID}=    Get Substring    ${FiveZeros}    0    ${OffSet}
    \    ${ZeroPaddedLableID}=    Catenate    SEPARATOR=    ${ZeroPaddedLableID}    ${label_ID}
    \    ${published_DDS_ric}=    set variable    .[----${MTE}${ZeroPaddedLableID}
    \    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    \    Start Capture MTE Output    ${remoteCapture}
    \    Stop Capture MTE Output    11    11
    \    get remote file    ${remoteCapture}    ${localCapture}
    \    Verify Unsolicited Response in Capture    ${localCapture}    ${published_DDS_ric}    TIMING_LOG    0
    \    Verify Unsolicited Response in Capture    ${localCapture}    ${published_DDS_ric}    TIMING_LOG    1
    [Teardown]    case teardown    ${localCapture}

Perform DVT Validation - Process all EXL files
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1887
    ...    Verify DVT rule when process all EXL files
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    Start MTE
    Start Capture MTE Output    ${remoteCapture}
    ${serviceName}    Get FMS Service Name
    ${currentDateTime}    get date and time
    Load All EXL Files    ${serviceName}    ${CHE_IP}
    wait smf log message after time    FMS REORG DONE    ${currentDateTime}    2    120
    Stop Capture MTE Output
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    ${ruleFilePath}    get DVT rule file
    validate messages against DVT rules    ${localCapture}    ${ruleFilePath}
    [Teardown]    case teardown    ${localCapture}

Perform DVT Validation - Rebuild all EXL files
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1888
    ...    Verify DVT rule when reload all exl files
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    Start MTE
    Start Capture MTE Output    ${remoteCapture}
    ${serviceName}    Get FMS Service Name
    ${currentDateTime}    get date and time
    Rebuild FMS service    ${serviceName}
    wait smf log message after time    Finished Sending Images    ${currentDateTime}
    Stop Capture MTE Output
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    ${ruleFilePath}    get DVT rule file
    validate messages against DVT rules    ${localCapture}    ${ruleFilePath}
    [Teardown]    case teardown    ${localCapture}

Perform DVT Validation -- Restart MTE
    [Documentation]    CATF-1890 Test Case - Perform DVT Validation - Restart
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1890
    ...
    ...    Veiry DVT Rule as restarting MTE
    ...
    ...    please note the DVT Rule has to be located at C:\Program Files\Reuters Test Tools\DAS where the \ DAS is at
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    Stop MTE
    Start Capture MTE Output    ${remoteCapture}
    ${currentDateTime}    get date and time
    Start MTE
    wait SMF log message after time    Finished Sending Images    ${currentDateTime}    2    120
    Stop Capture MTE Output
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    delete remote files    ${remoteCapture}
    ${ruleFilePath}    get DVT rule file
    validate messages against DVT rules    ${localCapture}    ${ruleFilePath}
    [Teardown]    case teardown    ${localCapture}

Perform DVT Validation - Closing Run for all RICs
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1889
    ...    Verify DVT rule when close all rics
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    Start MTE
    Start Capture MTE Output    ${remoteCapture}
    ${serviceName}=    Get FMS Service Name
    Manual ClosingRun for ClosingRun Rics    ${serviceName}
    Stop Capture MTE Output
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    ${ruleFilePath}    get DVT rule file
    validate messages against DVT rules    ${localCapture}    ${ruleFilePath}
    [Teardown]    case teardown    ${localCapture}

Verify TRWF Update Type
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1970
    ...
    ...    Verify FMS correction update type is "Correction"
    ...
    ...    Verify the realtime updates for MP updates are either "Quote", "Trade" or "Correction".
    ...
    ...    Verify the realtime updates for MBP updates are "unspecified".
    ...
    ...    verify "Closing Run" message triggered by FMSCMD
    ...
    ...    Trigger normal closing run via FMS and verify the normal closing run update has update type "Closing Run"
    ${service}    Get FMS Service Name
    Verify FMS Correction Update    ${service}
    ${pcapFileName} =    Generate PCAP File Name    ${service}    ${TEST NAME}
    Verify Realtime Update    ${pcapFileName}
    ${domain}    Get Preferred Domain
    ${sampleRic}    ${publishKey}    Get RIC From MTE Cache    ${domain}
    Manual ClosingRun for a RIC    ${sampleRic}    ${publishKey}    ${domain}

*** Keywords ***
Delete Persist Files and Restart MTE
    Delete Persist Files
    Start MTE

Push File to Remote and Restart MTE
    [Arguments]    ${localFile}    ${remoteFile}
    delete remote files    ${remoteFile}
    put remote file    ${localFile}    ${remoteFile}
    Delete Persist Files and Restart MTE

Restore Remote and Restart MTE
    [Arguments]    ${remoteFile}    ${remoteBackupFile}
    restore remote cfg file    ${remoteFile}    ${remoteBackupFile}
    Delete Persist Files and Restart MTE

Rebuild FMS service
    [Arguments]    ${serviceName}
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    dbrebuild    --HandlerName ${MTE}
    ...    --Services ${serviceName}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Verify DDS_DSO_ID
    [Arguments]    ${pcapfilename}    ${ricname}
    [Documentation]    Verify DDO_DSO_ID should equal to provider id
    ${mteConfigFile}=    Get MTE Config File
    ${providerId}    Get MTE Config Value    ${mteConfigFile}    ProviderId
    ${fids}    Create List    6401
    ${values}    Create List    ${providerId}
    verify fid value in message    ${pcapfilename}    ${ricname}    1    ${fids}    ${values}

Verify SPS_SP_RIC
    [Arguments]    ${pcapfilename}    ${ricname}    ${labelid}
    ${spsRicName}    Get SPS RIC From Label File    ${labelid}
    ${fids}    Create List    6480
    ${values}    Create List    ${spsRicName}
    verify fid value in message    ${pcapfilename}    ${ricname}    1    ${fids}    ${values}

Verify CONTEXT_ID
    [Arguments]    ${pcapfilename}    ${ricname}    ${contextID}
    ${fids}    Create List    5357
    ${values}    Create List    ${contextID}
    verify fid value in message    ${pcapfilename}    ${ricname}    1    ${fids}    ${values}

Verify MC_LABEL
    [Arguments]    ${pcapfilename}    ${ricname}    ${labelid}
    ${fids}    Create List    6394
    ${values}    Create List    ${labelid}
    verify fid value in message    ${pcapfilename}    ${ricname}    0    ${fids}    ${values}

Verify CMP_NME_ET
    [Arguments]    ${pcapfilename}    ${ricname}
    verify CMP_NME_ET in message    ${pcapfilename}    ${ricname}

Get SPS RIC From Label File
    [Arguments]    ${labelid}
    ${ddnLabelfilepath}=    search remote files    ${BASE_DIR}    ddnLabels.xml    recurse=${True}
    Length Should Be    ${ddnLabelfilepath}    1    ddnLabels.xml file not found (or multiple files found).
    ${localddnLabelfile}=    set variable    ${LOCAL_TMP_DIR}/ddnLabel.xml
    get remote file    ${ddnLabelfilepath[0]}    ${localddnLabelfile}
    ${updatedddnlabelfile}=    set variable    ${LOCAL_TMP_DIR}/updated_ddnLabel.xml
    remove_xinclude_from_labelfile    ${localddnLabelfile}    ${updatedddnlabelfile}
    ${spsRicName}    get sps ric name from label file    ${updatedddnlabelfile}    ${labelid}
    remove file    ${localddnLabelfile}
    remove file    ${updatedddnlabelfile}
    [Return]    ${spsRicName}

Verify UNCOMP_NAM
    [Arguments]    ${pcapfilename}    ${ricname}
    ${fids}    Create List    6395
    ${values}    Create List    ${ricname}
    verify fid value in message    ${pcapfilename}    ${ricname}    0    ${fids}    ${values}

Verify SetID In Response
    [Arguments]    ${pcapfilename}    ${ricname}
    verify setID in message    ${pcapfilename}    ${ricname}    30    Resopnse

Verify MC_REC_LAB
    [Arguments]    ${pcapfilename}    ${ricname}    ${labelid}
    ${fids}    Create List    9140
    ${values}    Create List    ${labelid}
    verify fid value in message    ${pcapfilename}    ${ricname}    0    ${fids}    ${values}

Verify FMS Correction Update
    [Arguments]    ${service}
    Start Capture MTE Output
    Load All EXL Files    ${service}    ${CHE_IP}
    Stop Capture MTE Output
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    verify correction updates in capture    ${LOCAL_TMP_DIR}/capture_local.pcap
    remove file    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify Realtime Update
    [Arguments]    @{pcap_file_list}
    ${mteConfigFile} =    Get MTE Config File
    @{domainList} =    Get Domain Names    ${mteConfigFile}
    Start Capture MTE Output
    Inject PCAP File on UDP    @{pcap_file_list}
    Stop Capture MTE Output
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    : FOR    ${domain}    IN    @{domainList}
    \    verify realtime update type in capture    ${LOCAL_TMP_DIR}/capture_local.pcap    ${domain}
    remove file    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify No Realtime Update
    [Arguments]    @{pcap_file_list}
    ${mteConfigFile} =    Get MTE Config File
    @{domainList} =    Get Domain Names    ${mteConfigFile}
    Start Capture MTE Output
    Inject PCAP File on UDP    @{pcap_file_list}
    Stop Capture MTE Output
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    : FOR    ${domain}    IN    @{domainList}
    \    verify no realtime update type in capture    ${LOCAL_TMP_DIR}/capture_local.pcap    ${domain}
    remove file    ${LOCAL_TMP_DIR}/capture_local.pcap
