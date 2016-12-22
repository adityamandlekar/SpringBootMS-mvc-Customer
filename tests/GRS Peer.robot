*** Settings ***
Documentation     Verify GRS functionality across peer machines
Suite Setup       Suite Setup Two TD Boxes With Playback
Suite Teardown    Suite Teardown
Force Tags        Peer    Playback
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
GRS Peer Recovery SMF Restart
    [Documentation]    Verify that on SMF restart, the GRS recovers missed messages from its GRS peer and the MTE also receives the missed messages. \ This test uses a small replay file with about 10 RICs, and the injection completes before the GRS recovery starts. \ This test verifies the FID values for the changed RICs are the same between the two MTEs.
    ${service}=    Get FMS Service Name
    ${injectFile}=    Generate PCAP File Name    ${service}    General RIC Update
    Recovery Setup With SMF Standby Stop
    ${remoteCapture}=    Inject PCAP File And Wait For Output    ${injectFile}
    Switch To TD Box    ${CHE_B_IP}
    ${currDateTime}    get date and time
    Start smf
    Comment    Verify GRS recovery request was fully processed
    wait smf log message after time    ${MTE}.*Start of Day request accepted    ${currDateTime}    waittime=10    timeout=180
    wait smf log message after time    ${MTE}.*Start of Day request complete    ${currDateTime}    waittime=2    timeout=10
    wait smf log message after time    ${MTE}.*Begin Regular Execution    ${currDateTime}    waittime=2    timeout=10
    Verify Peers Match    ${remoteCapture}
    [Teardown]    Peer Recovery Teardown

GRS Peer Recovery Successive Restart
    [Documentation]    Verify that the GRS recovery properly handles successive restart.
    ...    1. Delete GRS PCAP files on live and standby
    ...    2. Reset sequence numbers on live and standby
    ...    3. Stop GRS and MTE on standby
    ...    4. Inject generic PCAP file
    ...    5. Start GRS and MTE on standby
    ...    6. Verify Peers match
    ...    7. Stop GRS and MTE on standby
    ...    8. Start GRS and MTE on standby
    ...    9. Verify Peers match
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2128
    ${service}=    Get FMS Service Name
    ${injectFile}=    Generate PCAP File Name    ${service}    General RIC Update
    Reset Sequence Numbers    ${CHE_A_IP}    ${CHE_B_IP}
    Switch To TD Box    ${CHE_B_IP}
    Stop Process    GRS
    Stop MTE
    Switch To TD Box    ${CHE_A_IP}
    ${remoteCapture}=    Inject PCAP File and Wait For Output    ${injectFile}
    Switch To TD Box    ${CHE_B_IP}
    ${currDateTime}    get date and time
    Start Process    GRS
    Start MTE
    wait smf log message after time    ${MTE}.*Start of Day request accepted    ${currDateTime}    waittime=10    timeout=180
    wait smf log message after time    ${MTE}.*Start of Day request complete    ${currDateTime}    waittime=2    timeout=10
    wait smf log message after time    ${MTE}.*Begin Regular Execution    ${currDateTime}    waittime=2    timeout=10
    Verify Peers Match    ${remoteCapture}    ${False}
    Switch To TD Box    ${CHE_B_IP}
    Stop Process    GRS
    Stop MTE
    ${currDateTime}    get date and time
    Start Process    GRS
    Start MTE
    wait smf log message after time    ${MTE}.*Start of Day request accepted    ${currDateTime}    waittime=10    timeout=180
    wait smf log message after time    ${MTE}.*Start of Day request complete    ${currDateTime}    waittime=2    timeout=10
    wait smf log message after time    ${MTE}.*Begin Regular Execution    ${currDateTime}    waittime=2    timeout=10
    Verify Peers Match    ${remoteCapture}    ${True}
    [Teardown]    Peer Recovery Teardown

GRS Peer Recovery With All Local PCAPs
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-2123
    ...
    ...    Verify that GRS recovery when all GRS PCAP files are on local machine.
    Comment    Set ${CHE_B_IP} GRS maxstreambuffer to smaller value in order to get multiple GRS pcaps
    Switch to TD Box    ${CHE_B_IP}
    ${grsConfigFiles}=    Get CHE Config Filepaths    *_grs.json    config_grs.json    SCWatchdog
    ${grsConfigFile}=    Get From List    ${grsConfigFiles}    0
    ${locaConfigFile}=    set variable    ${LOCAL_TMP_DIR}${/}local_grs_config.json
    get remote file    ${grsConfigFile}    ${locaConfigFile}
    ${itemValue}=    Convert To Integer    300
    ${modifiedConfigFile}=    Modify GRS config feed item value    ${locaConfigFile}    maxstreambuffer    ${itemValue}
    put remote file    ${modifiedConfigFile}    ${grsConfigFile}
    Reset Sequence Numbers    ${CHE_A_IP}    ${CHE_B_IP}
    Switch To TD Box    ${CHE_A_IP}
    ${service}=    Get FMS Service Name
    ${injectFile}=    Generate PCAP File Name    ${service}    GRS_1000
    ${remoteCapture}=    Inject PCAP File And Wait For Output    ${injectFile}
    Switch To TD Box    ${CHE_B_IP}
    Stop MTE
    Stop Process    GRS
    ${currDateTime}    get date and time
    Start Process    GRS
    Start MTE
    wait smf log message after time    ${MTE}.*Start of Day request accepted    ${currDateTime}    waittime=2    timeout=120
    wait smf log message after time    ${MTE}.*Start of Day request complete    ${currDateTime}    waittime=2    timeout=30
    wait smf log message after time    Loading ${/}ThomsonReuters${/}GRS${/}bin${/}*.pcap to streambuffer    ${currDateTime}    waittime=2    timeout=10
    wait smf log does not contain    Peer Recovery finished for stream:*    waittime=2    timeout=10
    Verify Peers Match    ${remoteCapture}
    Stop MTE
    Stop Process    GRS
    [Teardown]    Run Keywords    put remote file    ${locaConfigFile}    ${grsConfigFile}
    ...    AND    Peer Recovery Teardown

*** Keywords ***
Peer Recovery Teardown
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    Switch To TD Box    ${CHE_B_IP}
    Start smf
    Start MTE
    Start Process    GRS
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
    [Arguments]    ${remoteCapture}    ${deleteRemoteCapture}=${True}
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    ${domain}=    Get Preferred Domain
    Switch To TD Box    ${CHE_A_IP}
    ${ricList}=    Get RIC List From Remote PCAP    ${remoteCapture}    ${domain}
    ${remoteRicFile}=    Set Variable    ${REMOTE_TMP_DIR}/ricList.txt
    Create Remote File Content    ${remoteRicFile}    ${ricList}
    Comment    Make sure A is LIVE before running Dataview on A.
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    verify MTE state    LIVE
    ${A_FIDs}=    Get FID Values From Refresh Request    ${remoteRicFile}    ${domain}
    Run Keyword If    ${deleteRemoteCapture}==${True}    Delete Remote Files    ${remoteCapture}
    Delete Remote Files    ${remoteRicFile}
    Comment    Make B LIVE before running Dataview on B.
    Switch To TD Box    ${CHE_B_IP}
    Create Remote File Content    ${remoteRicFile}    ${ricList}
    switch MTE LIVE STANDBY status    B    LIVE    ${master_ip}
    verify MTE state    LIVE
    ${B_FIDs}=    Get FID Values From Refresh Request    ${remoteRicFile}    ${domain}
    Dictionary of Dictionaries Should Be Equal    ${A_FIDs}    ${B_FIDs}
    Delete Remote Files    ${remoteRicFile}
