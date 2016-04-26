*** Settings ***
Documentation     Verify GRS functionality
Suite Setup       Suite Setup Two TD Boxes With Playback
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
GRS Control by SMF
    [Documentation]    Perform SMF start/stop to verify the GRS is being started or shut down by SMF
    ...    Kill GRS and make sure it is started by smf
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1895
    [Setup]
    comment    smf already started
    ${result}=    find processes by pattern    GRS
    Should Contain    ${result}    GRS
    comment    kill process, smf will start it
    Kill Processes    GRS
    wait for process to exist    GRS
    comment    stop smf and check GRS
    stop smf
    wait for process to not exist    GRS
    start smf
    wait for process to exist    GRS
    [Teardown]    start smf

MTE Start of Day Recovery
    [Documentation]    Verify that the MTE recovers lost messages by sending 'start of day' request to GRS.
    ...    1. Get the list of RICs that are changed by the PCAP file.
    ...    2. Get the initial FID values for those RICs before injection.
    ...    3. Get the FID values after the injection.
    ...    4. Verify the before and after FID values differ (i.e. the injection changes some FIDs)
    ...    4. Restart the MTE to create 'start of day' GRS recovery, and get the FID values after recovery.
    ...    6. Verify that the FID values after injection match those after recovery.
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1990
    ${service}=    Get FMS Service Name
    ${injectFile}=    Generate PCAP File Name    ${service}    General RIC Update
    ${domain}=    Get Preferred Domain
    Reset Sequence Numbers
    ${remoteCapture}=    Inject PCAP File and Wait For Output    ${injectFile}
    ${ricFile}=    Create Remote RIC List    ${remoteCapture}    ${domain}
    Reset Sequence Numbers
    ${startupFIDs}=    Get FID values    ${ricFile}    ${domain}
    ${remoteCapture}=    Inject PCAP File and Wait For Output    ${injectFile}
    ${afterInjectionFIDs}=    Get FID values    ${ricFile}    ${domain}
    Run Keyword and Expect Error    Following keys*    Dictionary of Dictionaries Should Be Equal    ${startupFIDs}    ${afterInjectionFIDs}
    Restart MTE With GRS Recovery
    ${afterRecoveryFIDs}=    Get FID values    ${ricFile}    ${domain}
    Dictionary of Dictionaries Should Be Equal    ${afterInjectionFIDs}    ${afterRecoveryFIDs}
    [Teardown]    Run Keyword If Test Passed    Delete Remote Files    ${remoteCapture}    ${ricFile}

GRS Peer Recovery SMF Restart
    [Documentation]    Verify that on SMF restart, the GRS recovers missed messages from its GRS peer and the MTE also receives the missed messages. \ This test uses a small replay file with about 10 RICs, and the injection completes before the GRS recovery starts. \ This test verifies the FID values for the changed RICs are the same between the two MTEs.
    [Tags]    Peer
    ${service}=    Get FMS Service Name
    ${injectFile}=    Generate PCAP File Name    ${service}    General RIC Update
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    Recovery Setup With SMF Restart
    Start Capture MTE Output    ${remoteCapture}
    Inject PCAP File    ${injectFile}
    Stop Capture MTE Output
    Switch To TD Box    ${CHE_B_IP}
    ${currDateTime}    get date and time
    Start smf
    Comment    Verify GRS recovery request was fully processed
    wait smf log message after time    ${MTE}.*Start of Day request accepted    ${currDateTime}    10    180
    wait smf log message after time    ${MTE}.*Start of Day request complete    ${currDateTime}    2    10
    wait smf log message after time    Begin Regular Execution    ${currDateTime}    2    10
    Verify Peers Match    ${remoteCapture}
    [Teardown]    Peer Recovery Teardown

Verify GRS stream creation
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1996
    ...
    ...    1. Parse venue grs config file and capture all the stream names
    ...    2. Compare with StatBlock to ensure all steam names are available
    ${files}    search remote files    ${BASE_DIR}    *_grs.json    ${TRUE}
    ${streamNames}    Create List
    : FOR    ${file}    IN    @{files}
    \    ${localFile}    Set Variable    ${LOCAL_TMP_DIR}/grs.json
    \    get remote file    ${file}    ${localFile}
    \    ${streams}    get GRS stream names from config file    ${localFile}
    \    Append To List    ${streamNames}    @{streams}
    : FOR    ${streamName}    IN    @{streamNames}
    \    get stat block field    GRS    ${streamName}    InputPacket
    [Teardown]    case teardown    ${localFile}

*** Keywords ***
Create Remote RIC List
    [Arguments]    ${remoteCapture}    ${domain}
    @{ricList}=    Get RIC List From Remote PCAP    ${remoteCapture}    ${domain}
    ${ricFile}=    Set Variable    ${REMOTE_TMP_DIR}/ricList.txt
    Create Remote File Content    ${ricFile}    ${ricList}
    [Return]    ${ricFile}

Delete GRS PCAP Files
    Delete Remote Files Matching Pattern    ${BASE_DIR}/GRS    *.pcap    ${True}

Get FID Values
    [Arguments]    ${ricList}    ${domain}
    ${result}=    Send TRWF2 Refresh Request No Blank FIDs    ${ricList}    ${domain}    -RL 1
    ${ricDict}=    Convert DataView Response to MultiRIC Dictionary    ${result}
    [Return]    ${ricDict}

Get RIC List From Remote PCAP
    [Arguments]    ${remoteCapture}    ${domain}
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    @{ricList}=    Get RICs From PCAP    ${localCapture}    ${domain}
    Should Not Be Empty    ${ricList}    Injected file produced no published RICs
    Remove Files    ${localCapture}
    [Return]    ${ricList}

Peer Recovery Teardown
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    Switch To TD Box    ${CHE_B_IP}
    Start smf
    Switch To TD Box    ${CHE_A_IP}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    verify MTE state    LIVE

Recovery Setup With SMF Restart
    Switch To TD Box    ${CHE_B_IP}
    Stop SMF
    Delete Persist Files
    Delete GRS PCAP Files
    Switch To TD Box    ${CHE_A_IP}
    Delete GRS PCAP Files
    Reset Sequence Numbers

Restart MTE With GRS Recovery
    ${currDateTime}    get date and time
    Stop MTE
    Delete Persist Files
    Start MTE
    Wait SMF Log Message After Time    Finished Startup, Begin Regular Execution    ${currDateTime}

Verify Peers Match
    [Arguments]    ${remoteCapture}
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    ${domain}=    Get Preferred Domain
    Switch To TD Box    ${CHE_A_IP}
    ${ricFilePath}=    Create Remote RIC List    ${remoteCapture}    ${domain}
    ${ricFileName}=    Fetch From Right    ${ricFilePath}    /
    ${localRicFile}=    Set Variable    ${LOCAL_TMP_DIR}/${ricFileName}
    Comment    Make sure A is LIVE before running Dataview on A.
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    verify MTE state    LIVE
    ${A_FIDs}=    Get FID values    ${ricFilePath}    ${domain}
    Get Remote File    ${ricFilePath}    ${localRicFile}
    Delete Remote Files    ${remoteCapture}    ${ricFilePath}
    Comment    Make B LIVE before running Dataview on B.
    Switch To TD Box    ${CHE_B_IP}
    Put Remote File    ${localRicFile}    ${ricFilePath}
    switch MTE LIVE STANDBY status    B    LIVE    ${master_ip}
    verify MTE state    LIVE
    ${B_FIDs}=    Get FID values    ${ricFilePath}    ${domain}
    Dictionary of Dictionaries Should Be Equal    ${A_FIDs}    ${B_FIDs}
    Delete Remote Files    ${ricFilePath}
    Remove Files    ${localRicFile}
