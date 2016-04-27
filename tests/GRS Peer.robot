*** Settings ***
Documentation     Verify GRS functionality across peer machines
Suite Setup       Suite Setup Two TD Boxes With Playback
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
GRS Peer Recovery SMF Restart
    [Documentation]    Verify that on SMF restart, the GRS recovers missed messages from its GRS peer and the MTE also receives the missed messages. \ This test uses a small replay file with about 10 RICs, and the injection completes before the GRS recovery starts. \ This test verifies the FID values for the changed RICs are the same between the two MTEs.
    [Tags]    Peer
    ${service}=    Get FMS Service Name
    ${injectFile}=    Generate PCAP File Name    ${service}    General RIC Update
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    Recovery Setup With SMF Standby Stop
    Start Capture MTE Output    ${remoteCapture}
    Inject PCAP File    ${injectFile}
    Stop Capture MTE Output
    Switch To TD Box    ${CHE_B_IP}
    ${currDateTime}    get date and time
    Start smf
    Comment    Verify GRS recovery request was fully processed
    wait smf log message after time    ${MTE}.*Start of Day request accepted    ${currDateTime}    10    180
    wait smf log message after time    ${MTE}.*Start of Day request complete    ${currDateTime}    2    10
    wait smf log message after time    ${MTE}.*Begin Regular Execution    ${currDateTime}    2    10
    Verify Peers Match    ${remoteCapture}
    [Teardown]    Peer Recovery Teardown

*** Keywords ***
Delete GRS PCAP Files
    Delete Remote Files Matching Pattern    ${BASE_DIR}    *.pcap    ${True}

Peer Recovery Teardown
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    Switch To TD Box    ${CHE_B_IP}
    Start smf
    Switch To TD Box    ${CHE_A_IP}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    verify MTE state    LIVE

Recovery Setup With SMF Standby Stop
    Switch To TD Box    ${CHE_B_IP}
    Stop SMF
    Delete Persist Files
    Delete GRS PCAP Files
    Switch To TD Box    ${CHE_A_IP}
    Delete GRS PCAP Files
    Reset Sequence Numbers

Verify Peers Match
    [Arguments]    ${remoteCapture}
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    ${domain}=    Get Preferred Domain
    Switch To TD Box    ${CHE_A_IP}
    ${ricFilePath}=    Get RIC List From Remote PCAP    ${remoteCapture}    ${domain}
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
