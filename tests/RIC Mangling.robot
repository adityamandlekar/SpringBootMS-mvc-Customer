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
    Set Mangling Rule    ${MTE}    SOU
    ${output}    Send TRWF2 Refresh Request    ${MTE}    ${expected_RicPrefix}${sampleRic}    ${domain}
    Run Keyword And Continue On Failure    verify mangling from dataview response    ${output}    ${expected_pe}    ${expected_RicPrefix}${sampleRic}
    Load Mangling Settings    ${MTE}

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
    ${exlfile}=    Get EXL For RIC    ${LOCAL_FMS_DIR}    ${domain}    ${serviceName}    ${sampleRic}
    @{pe}=    get ric fields from EXL    ${exlfile}    ${sampleRic}    PROD_PERM
    ${penew}=    set variable    @{pe}[0]
    ${localcapture}    Change Phase    SOU    BETA
    ${remotedumpfile}=    dump cache    ${MTE}    ${VENUE_DIR}
    Load Mangling Settings    ${MTE}
    ${matchedLines}    grep_remote_file    ${remotedumpfile}    ,Elektron SOU,
    delete remote files    ${remotedumpfile}
    ${length}    Get Length    ${matchedLines}
    Should Be Equal    ${length}    ${0}    Phase isn't changed successfully    ${False}
    Run Keyword And Continue On Failure    verify PE Change in message    ${localcapture}    ${VENUE_DIR}    ${DAS_DIR}    ${expected_RicPrefix}${sampleRic}    ${expected_pe}
    ...    ${penew}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify Electron RRG Phase - RIC Mangling change without Restart
    [Documentation]    Without restarting SMF, by running command, change phase to "Elektron RRG" successfully.
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1820
    ...
    ...    Test Case - Verify RRG Phase - RIC Mangling changes without Restart
    ${beta_RicPrefix}    set variable    ![
    ${expected_RicPrefix}    set variable    !!
    ${sampleRic}    ${publishKey}    Get RIC From MTE Cache
    ${localcapture}=    Change Phase    BETA    RRG
    ${remotedumpfile}=    dump cache    ${MTE}    ${VENUE_DIR}
    ${matchedLines}    grep_remote_file    ${remotedumpfile}    ,Elektron Beta,
    delete remote files    ${remotedumpfile}
    Load Mangling Settings    ${MTE}
    ${length}    Get Length    ${matchedLines}
    Should Be Equal    ${length}    ${0}    Phase wasn't changed successfully    ${False}
    Run Keyword And Continue On Failure    verify DROP message in itemstatus messages    ${localcapture}=    ${VENUE_DIR}    ${DAS_DIR}    ${beta_RicPrefix}${sampleRic}
    Run Keyword And Continue On Failure    verify all response message num    ${localcapture}=    ${VENUE_DIR}    ${DAS_DIR}    ${expected_RicPrefix}${sampleRic}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify IDN RRG Phase - RIC Mangling change without Restart
    [Documentation]    Without restarting SMF, by running command, phase change to IDN RRG(Unmangled) successfully.
    ...
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1821
    ...
    ...    _Test Case - Verify Production Phase -- No mangling, changes applied without Restart_
    ${rrg_RicPrefix}    set variable    !!
    ${sampleRic}    ${publishKey}    Get RIC From MTE Cache
    ${localcapture}    Change Phase    RRG    UNMANGLED
    ${remotedumpfile}=    dump cache    ${MTE}    ${VENUE_DIR}
    ${matchedLines}    grep_remote_file    ${remotedumpfile}    ,Elektron RRG,
    delete remote files    ${remotedumpfile}
    Load Mangling Settings    ${MTE}
    ${length}    Get Length    ${matchedLines}
    Should Be Equal    ${length}    ${0}    Mangled isn't removed    ${False}
    Run Keyword And Continue On Failure    verify DROP message in itemstatus messages    ${localcapture}    ${VENUE_DIR}    ${DAS_DIR}    ${rrg_RicPrefix}${sampleRic}
    Run Keyword And Continue On Failure    verify all response message num    ${localcapture}    ${VENUE_DIR}    ${DAS_DIR}    ${sampleRic}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

*** Keywords ***
Change Phase
    [Arguments]    ${PrePhase}    ${NewPhase}
    Set Mangling Rule    ${MTE}    ${PrePhase}
    Start Capture MTE Output    ${MTE}
    Set Mangling Rule    ${MTE}    ${NewPhase}
    Stop Capture MTE Output    ${MTE}
    ${localcapture}    set variable    ${LOCAL_TMP_DIR}/capture_local.pcap
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${localcapture}
    delete remote files    ${REMOTE_TMP_DIR}/capture.pcap
    [Return]    ${localcapture}
