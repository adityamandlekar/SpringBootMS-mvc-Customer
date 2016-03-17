*** Settings ***
Suite Setup       Suite Setup Two TD Boxes
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
Valid Manual State Changes
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1764
    ...    Verify valid requests to switch Live/Standby and lock Live/Standby using SCW CLI
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
    [Tags]    Peer
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
    [Teardown]    MTE Failover Case Teardown    ${master_ip}

Invalid Manual State Changes
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1764
    ...    Verify invalid requests to switch Live/Standby and lock Live/Standby using SCW CLI are rejected
    ...    Test will wait 60 seconds and verify no state change occured
    ...
    ...    The following invalid state transitions are tested:
    ...    Promote from Locked_Standby
    ...    Demote from Locked_Live
    ...    Switch Standby to Locked_Live when other instance is already Locked_Live
    ...    Switch a Locked_Live to Locked_Standby (without first unlocking)
    [Tags]    Peer
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
    Comment    Attempt Switch from Standby to Locked_Live when other instance is already Locked_Live
    switch MTE LIVE STANDBY status    B    LOCK_LIVE    ${master_ip}
    sleep    ${sleeptime}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE    waittime=1    timeout=1
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY    waittime=1    timeout=1
    Comment    Attempt Switch from Locked_Live to Locked_Standby (without first unlocking)
    switch MTE LIVE STANDBY status    A    LOCK_STANDBY    ${master_ip}
    sleep    ${sleeptime}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE    waittime=1    timeout=1
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY    waittime=1    timeout=1
    [Teardown]    MTE Failover Case Teardown    ${master_ip}

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
    [Tags]    Peer
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    ${ddnpublishersLabelfilepath}=    Get CHE Config Filepath    ddnPublishers.xml
    ${labelfile_local}=    set variable    ${LOCAL_TMP_DIR}/ddnPublishers.xml
    ${modifyLabelFile}=    set variable    ${LOCAL_TMP_DIR}/ddnPublishersModify.xml
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    Comment    Blocking Standby Side INPUT
    Switch to TD Box    ${CHE_B_IP}
    @{labelIDs}=    Get labelIDs
    get remote file    ${ddnpublishersLabelfilepath}    ${labelfile_local}
    remove xinclude from labelfile    ${labelfile_local}    ${modifyLabelFile}
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
    @{labelIDs}=    Get labelIDs
    get remote file    ${ddnpublishersLabelfilepath}    ${labelfile_local}
    remove xinclude from labelfile    ${labelfile_local}    ${modifyLabelFile}
    : FOR    ${labelID}    IN    @{labelIDs}
    \    @{multicastIPandPort}    get multicast address from label file    ${modifyLabelFile}    ${labelID}    ${MTE}
    \    @{syncPulseCountBefore}    get SyncPulseMissed    ${master_ip}
    \    block dataflow by port protocol    OUTPUT    UDP    @{multicastIPandPort}[1]
    \    sleep    5
    \    @{syncPulseCountAfter}    Run Keyword And Continue On Failure    get SyncPulseMissed    ${master_ip}
    \    unblock_dataflow
    \    verify sync pulse missed Qos    ${syncPulseCountBefore}    ${syncPulseCountAfter}
    [Teardown]    MTE Failover Case Teardown    ${master_ip}    ${modifyLabelFile}    ${labelfile_local}

Verify QoS Failover for Critical Process Failure
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1762 to verify QOS CritProcessFail will increase and failover happen if critical process is shutdown.
    ...
    ...    Test steps
    ...    1. Make sure A is LIVE
    ...    2. Stop MTE
    ...    3. Verify A is UNDEFINED, B is LIVE
    ...    4. Verify QOS on A side, CritProcessFail is 1, and Total QOS is 0
    ...    2. Stop below critical processes:
    ...    GRS
    ...    FMSClient
    ...    NetConStat
    ...    EventScheduler
    ...    StatsGen
    ...    GapStatGen
    ...    LatencyHandler
    ...    StatRicGen
    ...    3. Verify QOS on A side, CritProcessFail is 10, and Total QOS is 0
    ...    4. Verify A is UNDEFINED, B is LIVE
    ...    5. Restart above processes
    ...    6. Verify QOS on A side, CritProcessFail is 0, and Total QOS is 100
    ...    7. Verify A is STANDBY, B is LIVE
    [Tags]    Peer
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Switch To TD Box    ${CHE_A_IP}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Stop MTE
    Comment    Use 'continue on failure' \ so the processes are restarted even if a validation fails.
    Run Keyword and Continue on Failure    Verify MTE State In Specific Box    ${CHE_A_IP}    UNDEFINED
    Run Keyword and Continue on Failure    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    Run Keyword and Continue on Failure    Verify QoS for CritProcessFail    A    1    0    ${master_ip}
    Stop Process    GRS
    Stop Process    FMSClient
    Stop Process    NetConStat
    Stop Process    EventScheduler
    Stop Process    StatsGen
    Stop Process    GapStatGen
    Stop Process    LatencyHandler
    Stop Process    DudtGen
    Stop Process    StatRicGen
    Run Keyword and Continue on Failure    Verify QoS for CritProcessFail    A    10    0    ${master_ip}
    Start Process    StatRicGen
    Start Process    DudtGen
    Start Process    LatencyHandler
    Start Process    GapStatGen
    Start Process    StatsGen
    Start Process    EventScheduler
    Start Process    NetConStat
    Start Process    FMSClient
    Start Process    GRS
    Start MTE
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    Verify QoS for CritProcessFail    A    0    100    ${master_ip}
    [Teardown]

*** Keywords ***
Get labelIDs
    [Documentation]    Get the labelID from MTE config file on current machine.
    ...    The LabelID may be different across machines, so use config files from current machine.
    Set Suite Variable    ${LOCAL_MTE_CONFIG_FILE}    ${None}
    ${localVenueConfig}=    get MTE config file
    @{labelIDs}=    get MTE config list by section    ${localVenueConfig}    Publishing    LabelID
    [Return]    @{labelIDs}

Verify MTE State In Specific Box
    [Arguments]    ${che_ip}    ${state}    ${waittime}=5    ${timeout}=150
    ${host}=    get current connection index
    Switch To TD Box    ${che_ip}
    verify MTE state    ${state}    ${waittime}    ${timeout}
    Switch Connection    ${host}

MTE Failover Case Teardown
    [Arguments]    ${master_ip}    @{filesToRemove}
    [Documentation]    If a KW fail, unlocking both A and B
    switch MTE LIVE STANDBY status    A    UNLOCK    ${master_ip}
    switch MTE LIVE STANDBY status    B    UNLOCK    ${master_ip}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Switch To TD Box    ${CHE_A_IP}
    Run Keyword If    ${filesToRemove}    Case Teardown    @{filesToRemove}

Start Process
    [Arguments]    ${process}
    [Documentation]    Start process, argument is the process name
    run commander    process    start ${process}
    wait for process to exist    ${process}
    wait for StatBlock    CritProcMon    ${process}    m_IsAvailable    1

Stop Process
    [Arguments]    ${process}
    [Documentation]    Stop process, argument is the process name
    run commander    process    stop ${process}
    wait for process to not exist    ${process}

Verify QoS for CritProcessFail
    [Arguments]    ${node}    ${CritProcessFailValue}    ${totalQoSValue}    ${master_ip}
    [Documentation]    Verify the QOS of CritProcessFail and TotalQOS on specified node, &{node} should be A, B, C or D
    wait for QOS    ${node}    CritProcessFail    ${CritProcessFailValue}    ${master_ip}
    verify QOS equal to specific value    ${node}    Total QOS    ${totalQoSValue}    ${master_ip}
