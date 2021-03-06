*** Settings ***
Suite Setup       Suite Setup Two TD Boxes With Playback
Suite Teardown    Suite Teardown
Force Tags        Peer    Playback
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
Valid Manual State Changes
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1764
    ...    Verify valid requests to switch Live/Standby and lock Live/Standby using SCW CLI.
    ...    Note, the SCW CLI does allow state changes to LOCKED_LIVE and LOCKED_STANDBY even when one of the MTEs is already in a locked state.
    ...
    ...    The following valid state transitions are tested:
    ...    Promote from Standby to Live
    ...    Demote from Live to Standby
    ...    Switch Live to Locked Live
    ...    Unlock Live
    ...    Switch Standby to Locked Live
    ...    Switch Standby to Locked Standby
    ...    Unlock Standby
    ...    Switch Live to Locked Standby
    ...    Switch Standby to Locked_Live when other instance is already Locked_Live
    ...    Switch a Locked_Live to Locked_Standby (without first unlocking)
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    Comment    Promote from Standby to Live
    switch MTE LIVE STANDBY status    B    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    Comment    Demote from Live to Standby
    switch MTE LIVE STANDBY status    B    STANDBY    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    Comment    Switch Live to Locked Live
    switch MTE LIVE STANDBY status    A    LOCK_LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    Comment    Unlock Live
    switch MTE LIVE STANDBY status    A    UNLOCK    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    Comment    Switch Standby to Locked Live
    switch MTE LIVE STANDBY status    B    LOCK_LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    Verify MTE State In Specific Box    ${CHE_B_IP}    LOCKED_LIVE
    Comment    Switch Standby to Locked Standby
    switch MTE LIVE STANDBY status    A    LOCK_STANDBY    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_STANDBY
    Verify MTE State In Specific Box    ${CHE_B_IP}    LOCKED_LIVE
    Comment    Unlock Standby (and Live)
    switch MTE LIVE STANDBY status    A    UNLOCK    ${master_ip}
    switch MTE LIVE STANDBY status    B    UNLOCK    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    Comment    Switch Live to Locked Standby
    switch MTE LIVE STANDBY status    B    LOCK_STANDBY    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    LOCKED_STANDBY
    Comment    Switch from Standby to Locked_Live when other instance is already Locked_Live
    switch MTE LIVE STANDBY status    A    LOCK_LIVE    ${master_ip}
    switch MTE LIVE STANDBY status    B    UNLOCK    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    switch MTE LIVE STANDBY status    B    LOCK_LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    Verify MTE State In Specific Box    ${CHE_B_IP}    LOCKED_LIVE
    Comment    Switch from Locked_Live to Locked_Standby (without first unlocking)
    switch MTE LIVE STANDBY status    B    LOCK_STANDBY    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    LOCKED_STANDBY
    [Teardown]    MTE Failover Case Teardown    ${master_ip}

Invalid Manual State Changes
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1764
    ...    Verify invalid requests to switch Live/Standby and lock Live/Standby using SCW CLI are rejected
    ...    Test will wait 60 seconds and verify no state change occured
    ...
    ...    The following invalid state transitions are tested:
    ...    Promote from Locked_Standby
    ...    Demote from Locked_Live
    ${sleeptime}=    Set Variable    60
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    Comment    Attempt Promote from Locked_Standby
    switch MTE LIVE STANDBY status    B    LOCK_STANDBY    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    LOCKED_STANDBY
    switch MTE LIVE STANDBY status    B    LIVE    ${master_ip}
    sleep    ${sleeptime}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE    waittime=1    timeout=1
    Verify MTE State In Specific Box    ${CHE_B_IP}    LOCKED_STANDBY    waittime=1    timeout=1
    Comment    Attempt Demote from Locked_Live
    switch MTE LIVE STANDBY status    B    UNLOCK    ${master_ip}
    switch MTE LIVE STANDBY status    A    LOCK_LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    switch MTE LIVE STANDBY status    A    STANDBY    ${master_ip}
    sleep    ${sleeptime}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE    waittime=1    timeout=1
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY    waittime=1    timeout=1
    [Teardown]    MTE Failover Case Teardown    ${master_ip}

Critical Message Logging - MTE State change
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1754
    ...    To verify SMF Critical Message generates alert in GMI Log when using SCW CLI to switch Live/Standby
    ...    The test steps as follow:
    ...    1 Switch to SCW Master box (LIVE switch log only found in Master SCW box)
    ...    2 Switch A to Live
    ...    3 Switch A to Standby
    ...    4 Verify log in EventLogAdapterGMILog.txt
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    Switch To TD Box    ${master_ip}
    ${currDateTime}    get date and time
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    switch MTE LIVE STANDBY status    A    STANDBY    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    wait GMI message after time    WARNING.*LIVE switch has occurred.*Entity: ${MTE}.*EVENT:WDG_ERROR_ENTITY_LIVE_SWITCH : Investigate the cause of the entity switch    ${currDateTime}    waittime=2    timeout=100
    wait GMI message after time    CRITICAL.*Normal Processing.*[FM]TE.*ReportSituation    ${currDateTime}    waittime=2    timeout=100
    wait GMI message after time    CRITICAL.*Watchdog event.*[FM]TE.*ReportSituation    ${currDateTime}    waittime=2    timeout=100
    [Teardown]    MTE Failover Case Teardown    ${master_ip}

Verify STANDBY Handles Sync Pulse
    [Documentation]    Verify the STANDBY MTE clears its message buffer based on the Sync Pulse it receives from the LIVE MTE. \ Inject messages, then failover to the STANDBY and verify that STANDBY does not re-publish the messages when it goes LIVE.
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1759
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    ${service}=    Get FMS Service Name
    ${injectFile}=    Generate PCAP File Name    ${service}    General RIC Update
    ${domain}=    Get Preferred Domain
    Reset Sequence Numbers    ${CHE_A_IP}    ${CHE_B_IP}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    Switch To TD Box    ${CHE_A_IP}
    Inject PCAP File and Wait For Output    ${injectFile}
    Switch To TD Box    ${CHE_B_IP}
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/afterfailover.pcap
    ${currDateTime}    get date and time
    Start Capture MTE Output    ${remoteCapture}
    switch MTE LIVE STANDBY status    B    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    Wait SMF Log Message After Time    No messages in buffer to publish    ${currDateTime}
    Wait SMF Log Message After Time    Finished Publishing Buffer    ${currDateTime}
    Stop Capture Packets
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}${/}afterfailover.pcap
    Get Remote File    ${remoteCapture}    ${localCapture}
    Verify No Messages In Capture    ${localCapture}    ${domain}
    [Teardown]    MTE Failover Case Teardown    ${master_ip}    ${localCapture}

*** Keywords ***
MTE Failover Case Teardown
    [Arguments]    ${master_ip}    @{filesToRemove}
    [Documentation]    If a KW fail, unlocking both A and B
    switch MTE LIVE STANDBY status    A    UNLOCK    ${master_ip}
    switch MTE LIVE STANDBY status    B    UNLOCK    ${master_ip}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    Switch To TD Box    ${CHE_A_IP}
    Run Keyword If    ${filesToRemove}    Case Teardown    @{filesToRemove}
