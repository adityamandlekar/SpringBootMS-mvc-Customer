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

Verify QoS Failover for Critical Process Failure
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1762 to verify QOS CritProcessFail will increase and failover happen if critical process is shutdown.
    ...
    ...    Test steps
    ...    1. Make sure A is LIVE
    ...    2. Stop MTE
    ...    3. Verify A is UNDEFINED, B is LIVE
    ...    4. Verify QOS on A side, CritProcessFail is 1, and Total QOS is 0
    ...    2. Stop below critical processes:
    ...    GPS
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
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Stop MTE
    Verify QoS for CritProcessFail    A    1    0    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    UNDEFINED
    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    Stop Process    GRS
    Stop Process    FMSClient
    Stop Process    NetConStat
    Stop Process    EventScheduler
    Stop Process    StatsGen
    Stop Process    GapStatGen
    Stop Process    LatencyHandler
    Stop Process    DudtGen
    Stop Process    StatRicGen
    Verify QoS for CritProcessFail    A    10    0    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    UNDEFINED
    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    Switch To TD Box    ${CHE_A_IP}
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
    Verify QoS for CritProcessFail    A    0    100    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE

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
    verify QOS equal to specific value     ${node}    Total QOS    ${totalQoSValue}    ${master_ip}
