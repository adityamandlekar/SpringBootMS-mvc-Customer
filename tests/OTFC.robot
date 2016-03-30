*** Settings ***
Suite Setup       Suite Setup with Playback
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
OTFC PE and RIC mangling
    [Documentation]    For OTFC RIC, PE mangling and RIC mangling still works, it includes below scenario:
    ...    a.	Mangled PE + Prefix ![ mangling
    ...    b.	Non-mangled PE + Prefix !! mangling
    ...    1. Change to Elektron SOU stage
    ...    2. Inject PCAP
    ...    3. Check OTFC log
    ...    4. Get an OTFC RIC
    ...    5. Check the Prefix mangling
    ...    6. Check the PE
    ...    7. Change to Elektron RRG
    ...    8. Check the Prefix mangling
    ...    9. Fallback the mangling setting
    Start MTE
    Set Mangling Rule    SOU
    @{expected_pe}    Create List    4128    4245    4247
    ${domain}    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${currDateTime}    get date and time
    ${otfcExtractFile}    set variable    ${LOCAL_TMP_DIR}/otfcExtractFile.icf
    Inject PCAP in TCP    ${PLAYBACK_PCAP_DIR}
    ${Ric}    wait and get OTFC RIC from smf    ${MTE}.+Created on-the-fly Real-time    ${currDateTime}
    ${Ric}    ${pubRic}    Run Keyword And Continue On Failure    Verify RIC In MTE Cache    ${Ric}
    ${mangelPrefix}    Remove String    ${pubRic}    ${Ric}
    should be equal    ${mangelPrefix}    ![
    extract icf    ${Ric}    ${domain}    ${otfcExtractFile}    ${serviceName}
    check PE in icf file    ${otfcExtractFile}    @{expected_pe}
    Set Mangling Rule    RRG
    ${Ric}    ${pubRic}    Run Keyword And Continue On Failure    Verify RIC In MTE Cache    ${Ric}
    ${mangelPrefix}    Remove String    ${pubRic}    ${Ric}
    should be equal    ${mangelPrefix}    !!
    Load Mangling Settings
    [Teardown]    case teardown    ${PLAYBACK_PCAP_DIR}

OTFC Persistence
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1999
    ...
    ...    Test Case - OTFC persistence
    ...    Create an automated test case to verify OTFC Persistence and persistence loading.
    [Setup]    OTFC Setup
    ${serviceName}=    Get FMS Service Name
    ${preferredDomain}=    Get Preferred Domain
    Comment    Inject FMS file assoicate with playback test pcap file
    Load All EXL Files    ${serviceName}    ${CHE_IP}
    @{otfRicListBeforePlayback}=    get otf rics from cahce    ${preferredDomain}
    Should Be Empty    ${otfRicListBeforePlayback}    OTFC item found before starting playback
    Comment    Start Playback
    ${pcapFile}=    Generate PCAP File Name    ${serviceName}    ${TEST NAME}
    Inject PCAP File on UDP    ${pcapFile}
    @{otfRicListAfterPlayback}=    get otf rics from cahce    ${preferredDomain}
    Comment    Verify OTFC has saved to MTE cache
    Should Not Be Empty    ${otfRicListAfterPlayback}    No OTFC items created or saved to persist file after playback completed
    Stop MTE
    Start MTE for OTFC
    @{otfRicListAfterRestart}=    get otf rics from cahce    ${preferredDomain}
    ${NoOfOTFAfterPlayback}    Get Length    ${otfRicListAfterPlayback}
    ${NoOfOTFAfterRestart}    Get Length    ${otfRicListAfterRestart}
    Comment    Verify OTFC has saved to persist file and also can recreated from persist file after restart MTE
    Should Be Equal    ${NoOfOTFAfterPlayback}    ${NoOfOTFAfterRestart}    Number of OTFC items is different after restart i.e. not all OTFC items successful loaded from persist file
    [Teardown]    OTFC Teardown    ${serviceName}

*** Keywords ***
Start MTE for OTFC
    [Documentation]    When disable <ResendFM> in MTE config file, no more reconcile action will be done after MTE restart.
    ...    This mean IsLineHandlerStartupComplete won't turn to 1.
    ...    This make original KW 'Start MTE' fail to use in our case.
    ...
    ...    This KW doing similar thing as 'Start MTE' but it would check other important health status and skip checking IsLineHandlerStartupComplete
    ${result}=    find processes by pattern    MTE -c ${MTE}
    ${len}=    Get Length    ${result}
    Run keyword if    ${len} != 0    wait for HealthCheck    ${MTE}    IsLinehandlerStartupComplete    waittime=5    timeout=600
    Return from keyword if    ${len} != 0
    run commander    process    start ${MTE}
    wait for process to exist    MTE -c ${MTE}
    wait for HealthCheck    ${MTE}    DownstreamRecoveryConfigurationIsvalid
    wait for HealthCheck    ${MTE}    FMSConfigurationIsValid
    wait for HealthCheck    ${MTE}    IsConnectedToFMSClient
    wait for HealthCheck    ${MTE}    IsConnectedToFMSServer
    wait for HealthCheck    ${MTE}    IsConnectedToSCW

OTFC Teardown
    [Arguments]    ${serviceName}
    [Documentation]    Before end the test we
    ...    1. restore MTE config file
    ...    2. delete persist file and trigger reconcile one more time. (to restore the cache to original status)
    restore remote cfg file    ${mtecfgfile_org}    ${mtecfgfile_backup}
    Stop MTE
    Comment    Remove OTFC items from cache
    Delete Persist Files
    Start MTE
    Comment    Restore MTE cache to original status

OTFC Setup
    [Documentation]    Change the MTE config for
    ...    1. Enable OTFC
    ...    2. Disable ResendFM so that No Ric will be created from FMS Server provided EXL files.
    ...    (This actual empty the cache of MTE so that making OTFC easier)
    ${mtecfgfile}=    Convert To Lowercase    ${MTE}.xml
    ${orgFile}    ${backupFile}    backup remote cfg file    ${VENUE_DIR}    ${mtecfgfile}
    Set Suite Variable    ${mtecfgfile_backup}    ${backupFile}
    Set Suite Variable    ${mtecfgfile_org}    ${orgFile}
    Stop MTE
    Comment    Remove all items from MTE cache and stop MTE getting Ric information from FMS server (if exist)
    Delete Persist Files
    set value in MTE cfg    ${mtecfgfile_org}    ResendFM    0
    Comment    Enable OTFC for MTE
    set value in MTE cfg    ${mtecfgfile_org}    EnableOTFC    true
    Start MTE for OTFC
