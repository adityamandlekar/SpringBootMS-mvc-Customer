*** Settings ***
Suite Setup       Suite Setup Two TD Boxes
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
Verify Manual Live-Standby Switch via SCW CLI
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1764
    ...    To verify switch Live/Standby and lock Live/Standby using SCW CLI
    ...    The test steps as follow:
    ...    1 Switch A to Live, verify A is Live, B is Standby
    ...    2 Switch A to Standby, verify A is Standby, B is Live
    ...    3 Switch A to Lock_Live, verify A is Locked_Live, B is Standby
    ...    4 Switch B to Lock_Standby, verify A is Locked_Live, B is Locked_Standby
    ...    5 Unlock B, verify A is Locked_Live, B is Standby
    ...    6 Switch B to Lock_Live, verify A is Locked_Live, B is Standby
    ...    7 Unlock A, verify A is Live, B is Standby
    [Tags]    Peer
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    switch MTE LIVE STANDBY status    A    STANDBY    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    switch MTE LIVE STANDBY status    A    LOCK_LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    switch MTE LIVE STANDBY status    B    LOCK_STANDBY    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    LOCKED_STANDBY
    switch MTE LIVE STANDBY status    B    UNLOCK    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    switch MTE LIVE STANDBY status    B    LOCK_LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    switch MTE LIVE STANDBY status    A    UNLOCK    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    [Teardown]    Manual Switch Live-Standby Case Teardown    ${master_ip}

Critical Message Logging - MTE State change
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1754
    ...    To verify SMF Critical Message generates alert in GMI Log when using SCW CLI to switch Live/Standby
    ...    The test steps as follow:
    ...    1 Get MTE state on A
    ...    2 Switch A to Live
    ...    3 Switch A to Standby
    ...    4 Verify log in EventLogAdapterGMILog.txt
    [Tags]    Peer
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    Switch To TD Box    ${CHE_A_IP}
    ${start_state}    Get_MTE_state
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    ${currDateTime}    get date and time
    switch MTE LIVE STANDBY status    A    STANDBY    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    wait GMI message after time    CRITICAL.*Watchdog event.*MTE.*ReportSituation    ${currDateTime}    2    100
    wait GMI message after time    CRITICAL.*Normal Processing.*MTE.*ReportSituation    ${currDateTime}    2    100
    wait GMI message after time    WARNING.*LIVE switch has occurred.*Entity: MTEname.*EVENT:WDG_ERROR_ENTITY_LIVE_SWITCH : Investigate the cause of the entity switch    ${currDateTime}    2    100
    [Teardown]    switch MTE LIVE STANDBY status    A    ${start_state}    ${master_ip}

Verify Sync Pulse Missed QoS
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1763
    ...
    ...    Test Case - Verify Sync Pulse Missed QoS by blocking sync pulse publiscation port and check the missing statistic by SCWCli
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    ${localVenueConfig}=    get MTE config file
    @{labelIDs}=    get MTE config list by section    ${localVenueConfig}    Publishing    LabelID
    ${ddnpublishersLabelfilepath}=    Get CHE Config Filepath    ddnPublishers.xml
    ${labelfile_local}=    set variable    ${LOCAL_TMP_DIR}/ddnPublishers.xml
    get remote file    ${ddnpublishersLabelfilepath}    ${labelfile_local}
    ${modifyLabelFile}=    set variable    ${LOCAL_TMP_DIR}/ddnPublishersModify.xml
    remove xinclude from labelfile    ${labelfile_local}    ${modifyLabelFile}
    Comment    Blocking Standby Side INPUT
    Switch to TD Box    ${CHE_A_IP}
    ${state}=    Get MTE state
    Run Keyword If    '${state}' != 'STANDBY'    Switch to TD Box    ${CHE_B_IP}
    : FOR    ${labelID}    IN    @{labelIDs}
    \    @{multicastIPandPort}    get multicast address from label file    ${modifyLabelFile}    ${labelID}    ${MTE}
    \    @{syncPulseCountBefore}    get SyncPulseMissed    ${master_ip}
    \    block dataflow by port protocol    INPUT    UDP    @{multicastIPandPort}[1]
    \    sleep    5
    \    @{syncPulseCountAfter}    Run Keyword And Continue On Failure    get SyncPulseMissed    ${master_ip}
    \    unblock_dataflow
    \    verify sync pulse missed Qos    ${syncPulseCountBefore}    ${syncPulseCountAfter}
    Comment    Blocking Live Side OUTPUT
    Switch to TD Box    ${CHE_A_IP}
    ${state}=    Get MTE state
    Run Keyword If    '${state}' != 'LIVE'    Switch to TD Box    ${CHE_B_IP}
    : FOR    ${labelID}    IN    @{labelIDs}
    \    @{multicastIPandPort}    get multicast address from label file    ${modifyLabelFile}    ${labelID}    ${MTE}
    \    @{syncPulseCountBefore}    get SyncPulseMissed    ${master_ip}
    \    block dataflow by port protocol    OUTPUT    UDP    @{multicastIPandPort}[1]
    \    sleep    5
    \    @{syncPulseCountAfter}    Run Keyword And Continue On Failure    get SyncPulseMissed    ${master_ip}
    \    unblock_dataflow
    \    verify sync pulse missed Qos    ${syncPulseCountBefore}    ${syncPulseCountAfter}
    [Teardown]    Case Teardown    ${modifyLabelFile}    ${labelfile_local}

*** Keywords ***
Verify MTE State In Specific Box
    [Arguments]    ${che_ip}    ${state}
    Switch To TD Box    ${che_ip}
    verify MTE state    ${state}

Manual Switch Live-Standby Case Teardown
    [Arguments]    ${master_ip}
    [Documentation]    If a KW fail, unlocking both A and B
    switch MTE LIVE STANDBY status    A    UNLOCK    ${master_ip}
    switch MTE LIVE STANDBY status    B    UNLOCK    ${master_ip}
