*** Settings ***
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
Verify SOU Phase - Internal PE
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1818
    ...
    ...    Verify RIC prefic and PE mangling \ by switching to SOU Phase mangling
    ...
    ...    Hard-coded following in test case
    ...
    ...    Expected Ric Prefix for SOU : ![
    ...
    ...    Expected PE for SOU : [4128 4245 4247]
    @{expected_pe}    Create List    4128    4245    4247
    ${expected_RicPrefix}    set variable    ![
    ${domain}    Get Preferred Domain
    ${sampleRic}    ${pubRic}    Get RIC from MTE Cache    ${domain}
    Set Mangling Rule    SOU
    ${output}    Send TRWF2 Refresh Request    ${expected_RicPrefix}${sampleRic}    ${domain}
    Run Keyword And Continue On Failure    verify mangling from dataview response    ${output}    ${expected_pe}    ${expected_RicPrefix}${sampleRic}
    Load Mangling Settings

Verify BETA Phase - Disable PE Mangling without Restart
    [Documentation]    Without Restarting SMF, by running commander, phase can be changed to Elektron Beta successfully.
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1819
    ...
    ...    Test Case - Verify BETA Phase - Disable PE Mangling without Restart
    @{expected_pe}    Create List    4128    4245    4247
    ${expected_RicPrefix}    set variable    ![
    ${domain}=    Get Preferred Domain
    ${sampleRic}    ${publishKey}    Get RIC From MTE Cache    ${domain}
    ${serviceName}=    Get FMS Service Name
    ${exlfile}=    Get EXL For RIC    ${domain}    ${serviceName}    ${sampleRic}
    @{pe}=    get ric fields from EXL    ${exlfile}    ${sampleRic}    PROD_PERM
    ${penew}=    set variable    @{pe}[0]
    ${localcapture}    Change Phase    SOU    BETA
    ${remotedumpfile}=    dump cache
    Load Mangling Settings
    ${matchedLines}    grep_remote_file    ${remotedumpfile}    ,Elektron SOU,
    delete remote files    ${remotedumpfile}
    ${length}    Get Length    ${matchedLines}
    Should Be Equal    ${length}    ${0}    Phase isn't changed successfully    ${False}
    Get FIDFilter File
    Run Keyword And Continue On Failure    verify PE Change in message    ${localcapture}    ${expected_RicPrefix}${sampleRic}    ${expected_pe}    ${penew}    ${domain}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify Electron RRG Phase - RIC Mangling change without Restart
    [Documentation]    Without restarting SMF, by running command, change phase to "Elektron RRG" successfully.
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1820
    ...
    ...    Test Case - Verify RRG Phase - RIC Mangling changes without Restart
    ${beta_RicPrefix}    set variable    ![
    ${expected_RicPrefix}    set variable    !!
    ${domain}=    Get Preferred Domain
    ${sampleRic}    ${publishKey}    Get RIC From MTE Cache    ${domain}
    ${localcapture}=    Change Phase    BETA    RRG
    ${remotedumpfile}=    dump cache
    ${matchedLines}    grep_remote_file    ${remotedumpfile}    ,Elektron Beta,
    delete remote files    ${remotedumpfile}
    Load Mangling Settings
    ${length}    Get Length    ${matchedLines}
    Should Be Equal    ${length}    ${0}    Phase wasn't changed successfully    ${False}
    Get FIDFilter File
    Run Keyword And Continue On Failure    verify DROP message in itemstatus messages    ${localcapture}    ${beta_RicPrefix}${sampleRic}    ${domain}
    Run Keyword And Continue On Failure    verify all response message num    ${localcapture}    ${expected_RicPrefix}${sampleRic}    ${domain}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify IDN RRG Phase - RIC Mangling change without Restart
    [Documentation]    Without restarting SMF, by running command, phase change to IDN RRG(Unmangled) successfully.
    ...
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1821
    ...
    ...    _Test Case - Verify Production Phase -- No mangling, changes applied without Restart_
    ${rrg_RicPrefix}    set variable    !!
    ${domain}=    Get Preferred Domain
    ${sampleRic}    ${publishKey}    Get RIC From MTE Cache    ${domain}
    ${localcapture}    Change Phase    RRG    UNMANGLED
    ${remotedumpfile}=    dump cache
    ${matchedLines}    grep_remote_file    ${remotedumpfile}    ,Elektron RRG,
    delete remote files    ${remotedumpfile}
    Load Mangling Settings
    ${length}    Get Length    ${matchedLines}
    Should Be Equal    ${length}    ${0}    Mangled isn't removed    ${False}
    Get FIDFilter File
    Run Keyword And Continue On Failure    verify DROP message in itemstatus messages    ${localcapture}    ${rrg_RicPrefix}${sampleRic}    ${domain}
    Run Keyword And Continue On Failure    verify all response message num    ${localcapture}    ${sampleRic}    ${domain}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify Mangling by Context ID
    [Documentation]    For http://www.iajira.amers.ime.reuters.com/browse/CATF-1925
    ...
    ...    If venue has only 1 context id, pass test without doing anything.
    ...    If venue has at least 2 context ids:
    ...    - Set mangling for contextID 1 so it differs from default mangling. Verify contextID 1 uses new mangling setting and contextID 2 uses default mangling setting.
    ...    - Set mangling for contextID 1, mangling for contextID 2, and default mangling to three different values. Verify contextID 1 and 2 use the specified mangling.
    [Setup]    Verify Mangling by Context ID Case Setup
    ${dstdumpfile}=    set variable    ${LOCAL_TMP_DIR}/cachedump.csv
    Get Sorted Cache Dump    ${dstdumpfile}
    @{contextIDs}    get context ids from cachedump    ${dstdumpfile}
    Should Be True    len(${context_ids})>0    No context id is found
    Pass Execution If    len(${context_ids})==1    Only one context id, pass the test
    ${specialContextId}    Create Dictionary
    ${contextID1}    set variable    ${contextIDs[0]}
    ${contextID2}    set variable    ${contextIDs[1]}
    delete mangling rule partition node    ${contextIDs}    ${LOCAL_MANGLING_CONFIG_FILE}
    set mangling rule default value    UNMANGLED    ${LOCAL_MANGLING_CONFIG_FILE}
    Set Mangling Rule For Specific Context ID    ${contextID1}    SOU    @{files}[0]
    Set To Dictionary    ${specialContextId}    ${contextID1}    ![
    Verify Mangling Rule On All Context IDs    ${contextIDs}    ${specialContextId}
    Set Mangling Rule For Specific Context ID    ${contextID2}    RRG    @{files}[0]
    Set To Dictionary    ${specialContextId}    ${contextID2}    !!
    Verify Mangling Rule On All Context IDs    ${contextIDs}    ${specialContextId}
    [Teardown]    Verify Mangling by Context ID Case Teardown    ${dstdumpfile}

Verify UP_SOURCE_RIC Mangling in Shell RIC
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-2067
    ...
    ...    Verify Shell RIC C0 Respose UP_SOURCE_RIC mangling value is same as source ric
    ${contextIds}    Get ContextIDs for Shell RIC
    Pass Execution If    len(${contextIds}) == 0    MTE does not support Shell RIC
    Set Mangling Rule    SOU
    : FOR    ${contextId}    IN    @{contextIds}
    \    ${ricFiledList}    Get Ric Fields From Cache    1    ${EMPTY}    ${contextId}
    \    ${pubRic}    Set Variable    ${ricFiledList[0]['PUBLISH_KEY']}
    \    ${domain}    Set Variable    ${ricFiledList[0]['DOMAIN']}
    \    ${output}    Send TRWF2 Refresh Request    ${pubRic}    ${domain}
    \    Verify Mangling For UP SOURCE RIC FID From DataView Response    ${output}    ![
    [Teardown]    Run Keyword If    len(${contextIds}) != 0    Load Mangling Settings

*** Keywords ***
Change Phase
    [Arguments]    ${PrePhase}    ${NewPhase}
    Set Mangling Rule    ${PrePhase}
    Start Capture MTE Output
    Set Mangling Rule    ${NewPhase}
    Stop Capture MTE Output
    ${localcapture}    set variable    ${LOCAL_TMP_DIR}/capture_local.pcap
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${localcapture}
    delete remote files    ${REMOTE_TMP_DIR}/capture.pcap
    [Return]    ${localcapture}

Get ContextIDs for Shell RIC
    ${mteConfigFile}    Get MTE Config File
    ${contextIdsSupported}    Get Context Ids From Config File    ${mteConfigFile}
    ${contextIdsSupportedLen}    Get Length    ${contextIdsSupported}
    Get FIDFilter File
    ${fidfilterDict}    Get ContextId Fids Constit From Fidfiltertxt
    ${contextIds}    Get Dictionary Keys    ${fidfilterDict}
    ${contextIdsForShellRic}    Create List
    ${contextIdsUse}    Run Keyword If    ${contextIdsSupportedLen} == 0    Set Variable    ${contextIds}
    ...    ELSE    Set Variable    ${contextIdsSupported}
    : FOR    ${contextId}    IN    @{contextIdsUse}
    \    ${fids}    Get Dictionary Keys    ${fidfilterDict['${contextId}']['0']}
    \    ${isFIDExist}    Get Count    ${fids}    6632
    \    Run Keyword If    '${isFIDExist}' == '1'    Append To List    ${contextIdsForShellRic}    ${contextId}
    [Return]    ${contextIdsForShellRic}

Set Mangling Rule For Specific Context ID
    [Arguments]    ${contextid}    ${rule}    ${remoteConfigFile}
    [Documentation]    Set the mangling rule for specific context id, modify the local mangling config file and put to remote side, and then reload the mangling setting
    ${contextIdList}    Create List    ${contextid}
    set mangling rule parition value    ${rule}    ${contextIdList}    ${LOCAL_MANGLING_CONFIG_FILE}
    delete remote files    ${remoteConfigFile}
    put remote file    ${LOCAL_MANGLING_CONFIG_FILE}    ${remoteConfigFile}
    Load Mangling Settings

Verify Mangling Rule On All Context IDs
    [Arguments]    ${allcontextids}    ${specialContextId}
    [Documentation]    Verify mangling rule on all context ids.
    ...    ${specialContextId} is a dictionary, if you want to verify context id 1234 has a prefix !!, call | Set To Dictionary | ${specialContextId} | "1234" | !! |
    ${domain}    Get Preferred Domain
    : FOR    ${contextid}    IN    @{specialContextId}
    \    ${sampleRic}    ${publishKey}    Get RIC From MTE Cache    ${domain}    ${contextid}
    \    ${expectedPrefix}    Get From Dictionary    ${specialContextId}    ${contextid}
    \    Should Be Equal    ${publishKey}    ${expectedPrefix}${sampleRic}    The mangling is not set for context id ${contextid}
    \    Remove Values From List    ${allcontextids}    ${contextid}
    : FOR    ${contextid}    IN    @{allcontextids}
    \    ${sampleRic}    ${publishKey}    Get RIC From MTE Cache    ${domain}    ${contextid}
    \    Should Be Equal    ${publishKey}    ${sampleRic}    The mangling is not the default for context id ${contextid}

Verify Mangling by Context ID Case Setup
    [Arguments]    ${configFile}=manglingConfiguration.xml
    [Documentation]    Backup remote mangling config file
    @{files}=    backup remote cfg file    ${REMOTE_MTE_CONFIG_DIR}    ${configFile}
    Set Suite Variable    @{files}
    ${configFileLocal}=    Get Mangling Config File
    Set Suite Variable    ${configFileLocal}

Verify Mangling by Context ID Case Teardown
    [Arguments]    @{tmpfiles}
    [Documentation]    restore remote mangling config file and restore mangling setting
    restore remote cfg file    @{files}
    Load Mangling Settings
    Case Teardown    @{tmpfiles}
