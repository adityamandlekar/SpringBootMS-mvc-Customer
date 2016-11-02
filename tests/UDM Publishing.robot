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
    ${fileList}=    backup remote cfg file    ${REMOTE_MTE_CONFIG_DIR}    FIDFilter.txt
    ${fidFilterPath}    set variable    ${fileList[0]}
    ${fidfilterBackup}    set variable    ${fileList[1]}
    ${emptyContent}=    set variable    ${EMPTY}
    Create Remote File Content    ${fidFilterPath}    ${emptyContent}
    Reset Sequence Numbers
    ${service}    Get FMS Service Name
    ${pcapFileName} =    Generate PCAP File Name    ${service}    General RIC Update
    Run Keyword And Continue On Failure    Verify No Realtime Update    ${pcapFileName}
    Stop MTE
    Restore Remote and Restart MTE    ${fidFilterPath}    ${fidfilterBackup}
    [Teardown]

Empty Payload Detection with Blank TCONF
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1987
    ...
    ...    Restart MTE with empty tconf file and modified ${MTE}.xml config file. Verify no update messages with playback data. Restart MTE with restored tconf and config file
    ${fileList}=    backup remote cfg file    ${REMOTE_MTE_CONFIG_DIR}    ${MTE_CONFIG}
    ${remoteConfig}    set variable    ${fileList[0]}
    ${remoteConfigBackup}    set variable    ${fileList[1]}
    ${rmtCfgPath}    ${rmtCfgFile}    Split Path    ${remoteConfig}
    ${rmtCfgPath}=    Replace String    ${rmtCfgPath}    \\    /
    ${remoteEmptyTconf}    set variable    ${rmtCfgPath}/emptyTconf.tconf
    Create Remote File Content    ${remoteEmptyTconf}    //empty file
    Set Value in MTE cfg    ${remoteConfig}    TransformConfig    emptyTconf.tconf
    Reset Sequence Numbers
    ${service}    Get FMS Service Name
    ${pcapFileName} =    Generate PCAP File Name    ${service}    General RIC Update
    Run Keyword And Continue On Failure    Verify No Realtime Update    ${pcapFileName}
    Stop MTE
    Restore Remote and Restart MTE    ${remoteConfig}    ${remoteConfigBackup}
    [Teardown]

Validate Downstream FID publication
    [Documentation]    Verify if MTE has publish fids that matches fids defined in fidfilter file
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1632
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    ${mteConfigFile}    Get MTE Config File
    ${contextIds}    get context ids from config file    ${mteConfigFile}
    Get FIDFilter File
    : FOR    ${contextId}    IN    @{contextIds}
    \    ${status}    ${ricFiledList}    Run Keyword And Ignore Error     get ric fields from cache    1    ${EMPTY}
    \    ...    ${contextId}
    \    Continue For Loop If     '${status}' == 'FAIL'
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
    Get FIDFilter File
    verify FIDfilter FIDs are in message    ${LOCAL_TMP_DIR}/capture_local.pcap
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify Outbound Heartbeats
    [Documentation]    Verify if MTE has publish heartbeat at specified interval
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1721
    Start Capture MTE Output
    Stop Capture MTE Output    5    10
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    verify MTE heartbeat in message    ${LOCAL_TMP_DIR}/capture_local.pcap    1
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify Downstream Recovery Functions
    [Documentation]    This test uses DataView to send refresh request. MTE response will be captured in pcap and analysed with solicited flag for all possible constituents for the RIC
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1707
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
    Get FIDFilter File
    ${constituents}=    get constituents from FidFilter    ${contextId}
    Verify Unsolicited Response in Capture    ${localCapture}    ${pubRic}    ${domain}    ${constituents}
    [Teardown]    case teardown    ${localCapture}

Verify Common Required FID output
    [Documentation]    Verify the common fid in the output, http://www.iajira.amers.ime.reuters.com/browse/CATF-1847
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    ${serviceName}    Get FMS Service Name
    Start Capture MTE Output    ${remoteCapture}
    ${currentDateTime}    get date and time
    Rebuild FMS service    ${serviceName}
    wait smf log message after time    Finished Sending Images    ${currentDateTime}
    Stop Capture MTE Output
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    ${domain}=    Get Preferred Domain
    @{ric_contextid_list}    get ric fields from cache    1    ${domain}    ${EMPTY}
    ${publishKey}=    set variable    ${ric_contextid_list[0]['PUBLISH_KEY']}
    ${contextId}=    set variable    ${ric_contextid_list[0]['CONTEXT_ID']}
    ${mteConfigFile}=    Get MTE Config File
    ${labelID}=    Get Label ID For Context ID    ${mteConfigFile}    ${contextId}
    Verify DDS_DSO_ID    ${localCapture}    ${publishKey}    ${domain}
    Verify SPS_SP_RIC    ${localCapture}    ${publishKey}    ${labelID}    ${domain}
    Verify CONTEXT_ID    ${localCapture}    ${publishKey}    ${contextId}    ${domain}
    Verify MC_LABEL    ${localCapture}    ${publishKey}    ${labelID}    ${domain}
    Verify MC_REC_LAB    ${localCapture}    ${publishKey}    ${labelID}    ${domain}
    Verify UNCOMP_NAM    ${localCapture}    ${publishKey}    ${domain}
    Verify CMP_NME_ET    ${localCapture}    ${publishKey}    ${domain}
    Verify SetID In Response    ${localCapture}    ${publishKey}    ${domain}
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
    Load Single EXL File    ${localEXLfile}    ${serviceName}    ${CHE_IP}
    Wait For Persist File Update    5    60
    Stop Capture MTE Output    1    5
    get remote file    ${remoteCapture}    ${localCapture}
    ${mangle}    Fetch From Left    ${pubRic}    ${ric}
    verify key compression in message    ${localCapture}    ${mangle}${long_ric}
    Load Single EXL File    ${EXLfullpath}    ${serviceName}    ${CHE_IP}
    [Teardown]    case teardown    ${localCapture}

Verify SPS RIC is published
    [Documentation]    Verify SPS RIC and SPS Input Stats RIC are published.
    ...    Since Recon creates the ddnLabels.xml file, we cannot verify that the SPS RIC name is defined using the correct rules in the production label files.
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1757
    @{labelIDs}=    Get Label IDs
    ${SPSric}=    Get SPS RIC From Label File    @{labelIDs}[0]
    ${SPSric_input_stats}=    set variable    ${SPSric}_INS
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    Start Capture MTE Output    ${remoteCapture}    DDNA    @{labelIDs}[0]
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
    ...
    ...    Auto Check DUDT FIDs
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2230
    ...
    ...    According to DDN DN124 - DUDT Section 4.2, check the published DUDT RIC with the following fields:
    ...    1. FID: 1080, DataType: UInt
    ...    2. FID: 3263, DataType: UInt
    ...    3. FID: 6401, DataType: UInt
    ...    4. FID: 6461, DataType: Buffer, Value: hostname of TD
    ...    5. FID: 6462, DataType: UInt, Value: 0, 1 or 2
    ...    6. FID: 6463, DataType: Integer
    ...    7. FID: 6464, DataType: Time, Value: within the range of TD Local System Time +10 sec as threshold
    ...    8. FID: 6468, DataType: Integer
    ...
    ...    Verify DDS RIC is published test fails because it does not conform to DUDT DN
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2031
    ...
    ...    DDN124 v3.3
    ...    https://theshare.thomsonreuters.com/sites/rttal/_layouts/WordViewer.aspx?id=/sites/rttal/Shared%20Documents/ERT%20Design%20Notes/DN124-DDS%20DUDT%20status%20instruments/DDN%20DN124%20-%20DUDT.docx&Source=https%3A%2F%2Ftheshare%2Ethomsonreuters%2Ecom%2Fsite
    ...
    ...    The following defines the key structure of all new status instrument items.
    ...    The key structure is designed so that consuming applications can, if required, ‘slice’ the key at known positions to break it down into its constituents.
    ...
    ...    1. Prefix
    ...    2 fixed characters to prefix status instruments. This is ‘off limits’ as a prefix to any product instrument keys and \ \ \ \ serves to indicate that the instrument is status, not product, data. The prefix for all status instrument keys should \ \ \ \ be ‘.[’ \ = \ ASCI 46 & 91 \ = \ Full Stop & Open Square bracket.
    ...
    ...    2. LH/EDF/MTE
    ...    10 characters specifiying the Line Handler/EDF/MTE on the particular system (EG. 'LSEFTS', ‘TIF’). \ \ If length is \ \ \ equal or less than 6, then start at 5th byte, otherwise right justified. \ Unused characters are filled as hyphen. \ \ \ \ (This strange behaviour is aimed to be backward compatible). \ Below are examples:
    ...    - 3 characters name ‘TIF’, it is filled as ‘----TIF---‘
    ...    - 6 characters name ‘LSEFTS’, it is filled as ‘----LSEFTS’.
    ...    - 7 characters name ‘TDDS01M ‘, it is filled as ‘---TDDS01M’.
    ...
    ...    3. Instance
    ...    1 character to present instance in the redundancy cluster. \ ‘0’ to ‘3’ represents nodes ‘A’to ‘D’.
    ...
    ...    4. Label ID
    ...    4 characters indicating the Label ID. Some feeds may use different Label IDs \ for different data (eg Level 1 and \ \ \ Level 2 data). \ Each DUDT instrument will use the same Label ID as used for the LH it tracks. If an LH generates \ \ \ data in more than one Multicast group there will be a separate DUDT instrument for each group.
    ...    For EDF/Feed Handler, fill these 4 characters as “0000”.
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    @{labelIDs}=    Get Label IDs
    ${mteConfigFile}=    Get MTE Config File
    ${instance}=    Get MTE Instance    ${mteConfigFile}
    ${hostname}=    Get Hostname
    ${fidsList}=    Create List    1080    3263    6401    6461    6462
    ...    6463    6468    6464
    ${dataTypeList}=    Create List    UInt    UInt    UInt    Buffer    UInt
    ...    Integer    Integer    Time
    ${valuesList}=    Create List    ${None}    ${None}    ${None}    ${hostname}    0,1,2
    ...    ${None}    ${None}    0
    : FOR    ${labelID}    IN    @{labelIDs}
    \    ${published_DDS_ric}=    Get DDS RIC    ${labelID}    ${instance}
    \    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    \    Comment    Update the expected current time range of FID 6464
    \    ${timeThreshold}=    set variable    10
    \    ${timeBeforeMidnight}=    Get Time Before Midnight In Seconds
    \    Comment    To handle the boundary case of running test pass through midnight, sleep a few seconds to avoid the time wrap around to 0.
    \    Run Keyword If    ${timeThreshold} > ${timeBeforeMidnight}    Sleep    ${timeBeforeMidnight}
    \    ${curTimeMicrosec}=    Get Time in Microseconds
    \    ${microsecLowerLimit}=    set variable    ${curTimeMicrosec}
    \    ${microsecUpperLimit}=    Evaluate    ${curTimeMicrosec}+(${timeThreshold}*1000000)
    \    Remove From List    ${valuesList}    -1
    \    Append To List    ${valuesList}    ${microsecLowerLimit}:${microsecUpperLimit}
    \    Start Capture MTE Output    ${remoteCapture}    DDNA    ${labelID}
    \    Stop Capture MTE Output    11    11
    \    get remote file    ${remoteCapture}    ${localCapture}
    \    Verify Unsolicited Response in Capture    ${localCapture}    ${published_DDS_ric}    TIMING_LOG    0
    \    Verify FID DataType Value in Unsolicited Response    ${localCapture}    ${published_DDS_ric}    TIMING_LOG    1    ${fidsList}
    \    ...    ${dataTypeList}    ${valuesList}
    [Teardown]    case teardown    ${localCapture}

Perform DVT Validation - Process all EXL files
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1887
    ...    Verify DVT rule when process all EXL files
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    Start Capture MTE Output    ${remoteCapture}
    ${serviceName}    Get FMS Service Name
    ${currentDateTime}    get date and time
    Load All EXL Files    ${serviceName}    ${CHE_IP}
    wait smf log message after time    FMS REORG DONE    ${currentDateTime}    waittime=2    timeout=120
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
    wait SMF log message after time    Finished Sending Images    ${currentDateTime}    waittime=2    timeout=120
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
    Start Capture MTE Output    ${remoteCapture}
    ${serviceName}=    Get FMS Service Name
    Manual ClosingRun for ClosingRun Rics    ${serviceName}
    Stop Capture MTE Output
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    ${ruleFilePath}    get DVT rule file
    validate messages against DVT rules    ${localCapture}    ${ruleFilePath}
    [Teardown]    case teardown    ${localCapture}

Perform DVT Validation - Playback
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-2090
    ...    Verify DVT rule after playback of pcap file
    ${serviceName}    Get FMS Service Name
    ${pcapFileName} =    Generate PCAP File Name    ${serviceName}    General RIC Update
    Reset Sequence Numbers
    ${remoteCapture}=    Inject PCAP File And Wait For Output    ${pcapFileName}
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
    ${pcapFileName} =    Generate PCAP File Name    ${service}    General RIC Update
    Reset Sequence Numbers
    Verify Realtime Update    ${pcapFileName}
    ${domain}    Get Preferred Domain
    ${sampleRic}    ${publishKey}    Get RIC From MTE Cache    ${domain}
    Manual ClosingRun for a RIC    ${sampleRic}    ${publishKey}    ${domain}

*** Keywords ***
Delete Persist Files and Restart MTE
    Delete Persist Files
    Start MTE

Get DDS RIC
    [Arguments]    ${labelID}    ${instance}
    ${mteLength}=    Get Length    ${MTE}
    Should Be True    ${mteLength} > 0 and ${mteLength} <= 10    Length of MTE should be greater than 0 and less than or equal to 10
    ${fiveHyphens}=    Set Variable    -----
    ${mteLeadingOffSet}=    Evaluate    10 - ${mteLength}
    ${mteLeadingOffSet}=    Set Variable If    ${mteLength} > 6    ${mteLeadingOffSet}    4
    ${mteTrailingOffSet}=    Evaluate    6 - ${mteLength}
    ${mteTrailingOffSet}=    Set Variable If    ${mteLength} < 6    ${mteTrailingOffSet}    0
    ${mteLeadingHyphens}=    Get Substring    ${fiveHyphens}    0    ${mteLeadingOffSet}
    ${mteTrailingHyphens}=    Get Substring    ${fiveHyphens}    0    ${mteTrailingOffSet}
    ${hyphenPaddedMte}=    Catenate    SEPARATOR=    ${mteLeadingHyphens}    ${MTE}    ${mteTrailingHyphens}
    ${labelLength}=    Get Length    ${labelID}
    Should Be True    ${labelLength} > 0 and ${labelLength} <= 4    Length of label ID should be greater than 0 and less than or equal to 4
    ${fourZeros}=    Set Variable    0000
    ${labelOffSet}=    Evaluate    4 - ${labelLength}
    ${zeroPaddedLabelID}=    Get Substring    ${fourZeros}    0    ${labelOffSet}
    ${zeroPaddedLabelID}=    Catenate    SEPARATOR=    ${zeroPaddedLabelID}    ${labelID}
    ${publishedDDSRic}=    Set Variable    .[${hyphenPaddedMte}${instance}${zeroPaddedLabelID}
    [Return]    ${publishedDDSRic}

Get MTE Instance
    [Arguments]    ${mteConfigFile}
    [Documentation]    Get "ProviderInstance" (nodes 'A' to 'D') from MTE config and convert it to 0-3.
    ${instance}=    Get MTE Config Value    ${mteConfigFile}    Publishing    DDS    ProviderInstance
    ${instance}=    Evaluate    ord(('${instance}').upper())-ord('A')
    Should Be True    ${instance} >= 0 and ${instance} < 4    Instance should be greater than or equal to 0 and less than 4
    [Return]    ${instance}

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
    [Arguments]    ${pcapfilename}    ${ricname}    ${domain}
    [Documentation]    Verify DDO_DSO_ID should equal to provider id
    ${mteConfigFile}=    Get MTE Config File
    ${providerId}    Get MTE Config Value    ${mteConfigFile}    ProviderId
    ${fids}    Create List    6401
    ${values}    Create List    ${providerId}
    verify fid value in message    ${pcapfilename}    ${ricname}    1    ${domain}    ${fids}    ${values}

Verify SPS_SP_RIC
    [Arguments]    ${pcapfilename}    ${ricname}    ${labelid}    ${domain}
    ${spsRicName}    Get SPS RIC From Label File    ${labelid}
    ${fids}    Create List    6480
    ${values}    Create List    ${spsRicName}
    verify fid value in message    ${pcapfilename}    ${ricname}    1    ${domain}    ${fids}    ${values}

Verify CONTEXT_ID
    [Arguments]    ${pcapfilename}    ${ricname}    ${contextID}    ${domain}
    ${fids}    Create List    5357
    ${values}    Create List    ${contextID}
    verify fid value in message    ${pcapfilename}    ${ricname}    1    ${domain}    ${fids}    ${values}

Verify MC_LABEL
    [Arguments]    ${pcapfilename}    ${ricname}    ${labelid}    ${domain}
    ${fids}    Create List    6394
    ${values}    Create List    ${labelid}
    verify fid value in message    ${pcapfilename}    ${ricname}    0    ${domain}    ${fids}    ${values}

Verify CMP_NME_ET
    [Arguments]    ${pcapfilename}    ${ricname}    ${domain}
    verify CMP_NME_ET in message    ${pcapfilename}    ${ricname}    ${domain}

Get SPS RIC From Label File
    [Arguments]    ${labelid}
    ${ddnLabelfilepath}=    Get CHE Config Filepaths    ddnLabels.xml
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
    [Arguments]    ${pcapfilename}    ${ricname}    ${domain}
    ${fids}    Create List    6395
    ${values}    Create List    ${ricname}
    verify fid value in message    ${pcapfilename}    ${ricname}    0    ${domain}    ${fids}    ${values}

Verify SetID In Response
    [Arguments]    ${pcapfilename}    ${ricname}    ${domain}
    verify setID in message    ${pcapfilename}    ${ricname}    30    Resopnse    ${domain}

Verify MC_REC_LAB
    [Arguments]    ${pcapfilename}    ${ricname}    ${labelid}    ${domain}
    ${fids}    Create List    9140
    ${values}    Create List    ${labelid}
    verify fid value in message    ${pcapfilename}    ${ricname}    0    ${domain}    ${fids}    ${values}

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
    ${remoteCapture}=    Inject PCAP File and Wait For Output    @{pcap_file_list}
    get remote file    ${remoteCapture}    ${LOCAL_TMP_DIR}/capture_local.pcap
    : FOR    ${domain}    IN    @{domainList}
    \    verify realtime update type in capture    ${LOCAL_TMP_DIR}/capture_local.pcap    ${domain}
    remove file    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify No Realtime Update
    [Arguments]    @{pcap_file_list}
    ${mteConfigFile} =    Get MTE Config File
    @{domainList} =    Get Domain Names    ${mteConfigFile}
    ${remoteCapture}=    Inject PCAP File And Wait For Output    @{pcap_file_list}
    get remote file    ${remoteCapture}    ${LOCAL_TMP_DIR}/capture_local.pcap
    : FOR    ${domain}    IN    @{domainList}
    \    verify no realtime update type in capture    ${LOCAL_TMP_DIR}/capture_local.pcap    ${domain}
    remove file    ${LOCAL_TMP_DIR}/capture_local.pcap
