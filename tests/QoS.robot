*** Settings ***
Documentation     Verify QoS value when disable the NIC
Suite Setup       Suite Setup Two TD Boxes
Suite Teardown    Suite Teardown
Force Tags        Peer
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
Verify Sync Pulse Missed QoS
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1763
    ...
    ...    Test Case - Verify Sync Pulse Missed QoS by blocking sync pulse publiscation port and check the missing statistic by SCWCli
    [Setup]    QoS Case Setup
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    ${ddnpublishersLabelfilepaths}=    Get CHE Config Filepaths    ddnPublishers.xml
    ${ddnpublishersLabelfilepath}=    Get From List    ${ddnpublishersLabelfilepaths}    0
    ${labelfile_local}=    set variable    ${LOCAL_TMP_DIR}/ddnPublishers.xml
    ${modifyLabelFile}=    set variable    ${LOCAL_TMP_DIR}/ddnPublishersModify.xml
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State IN Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State IN Specific Box    ${CHE_B_IP}    STANDBY
    Comment    Blocking Standby Side INPUT
    Switch to TD Box    ${CHE_B_IP}
    @{labelIDs}=    Get Label IDs
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
    \    sleep    5
    \    Verify Sync Pulse Received    ${master_ip}
    Comment    Blocking Live Side OUTPUT
    Switch to TD Box    ${CHE_A_IP}
    @{labelIDs}=    Get Label IDs
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
    \    Sleep    5
    \    Verify Sync Pulse Received    ${master_ip}
    [Teardown]    Run Keywords    Unblock Dataflow
    ...    AND    QoS Case Teardown
    ...    AND    Case Teardown    ${modifyLabelFile}    ${labelfile_local}

Verify QoS Failover for Critical Process Failure
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1762 to verify QOS CritProcessFail will increase and failover happen if critical process is shutdown.
    ...
    ...    1. Stop each of the following critical processes: \ GRS, FMSClient, NetConStat, EventScheduler, StatsGen, GapStatGen, LatencyHandler, StatRicGen.
    ...    2. Verify LIVE MTE failover after first Critical Process failure.
    ...    3. Verify CritProcessFail count indicates the number of critical processes that are down.
    ...    4. Restart the components.
    ...    5. Verify CritProcessFail count goes back to zero and Total QoS goes back to 100.
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Switch To TD Box    ${CHE_A_IP}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Stop Process    GRS
    Comment    Use 'continue on failure' so the processes are restarted even if a validation fails.
    Run Keyword and Continue on Failure    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    Run Keyword and Continue on Failure    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    Run Keyword and Continue on Failure    Verify QoS for CritProcessFail    A    ${master_ip}    1    0
    Stop Process    FMSClient
    Stop Process    NetConStat
    Stop Process    EventScheduler
    Stop Process    StatsGen
    Stop Process    GapStatGen
    Stop Process    LatencyHandler
    Stop Process    DudtGen
    Stop Process    StatRicGen
    Run Keyword and Continue on Failure    Verify QoS for CritProcessFail    A    ${master_ip}    9    0
    Comment    Restart process in same order that SMF starts them
    Run Keyword and Continue on Failure    Start Process    StatRicGen
    Run Keyword and Continue on Failure    Start Process    DudtGen
    Run Keyword and Continue on Failure    Start Process    LatencyHandler
    Run Keyword and Continue on Failure    Start Process    GapStatGen
    Run Keyword and Continue on Failure    Start Process    StatsGen
    Run Keyword and Continue on Failure    Start Process    EventScheduler
    Run Keyword and Continue on Failure    Start Process    NetConStat
    Run Keyword and Continue on Failure    Start Process    FMSClient
    Run Keyword and Continue on Failure    Start Process    GRS
    Verify QoS for CritProcessFail    A    ${master_ip}    0    100
    [Teardown]

Verify QoS Failover for UDP Feed Line Down
    [Documentation]    Verify that the LIVE MTE fails over to the STANDBY MTE when the UDP feed line is down longer than HiActTimeLimit/LoActTimeLimit configuration value.
    ...
    ...    Set feed line down timeout interval (HiActTimeLimit/LoActTimeLimit) for MTE A to a small value, which still gives the MTE time to start up (currently using 150 seconds) and stop/start SMF.
    ...    Promote MTE A to LIVE.
    ...    Wait for feed line down timeout interval.
    ...    Verify that failover occurred and MTE B is now LIVE.
    Pass Execution If    '${PROTOCOL}' !='UDP'    Venue Protocol ${PROTOCOL} is not UDP
    Switch To TD Box    ${CHE_A_IP}
    ${timeoutLimit}=    Set Variable    200
    ${orgCfgFile}    ${backupCfgFile}    Set UDP Feed Line Timeout    ${timeoutLimit}
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State IN Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State IN Specific Box    ${CHE_B_IP}    STANDBY
    Comment    Failover should occur when feed line timeout on A is reached
    Sleep    ${timeoutLimit}
    Verify MTE State IN Specific Box    ${CHE_A_IP}    STANDBY    5    60
    Verify MTE State IN Specific Box    ${CHE_B_IP}    LIVE
    [Teardown]    Run Keyword If    '${PROTOCOL}' == 'UDP'    Restore Feed Line Timeout    ${orgCfgFile}    ${backupCfgFile}

Verify QoS Failover for TCP-FTP Feed Line Down
    [Documentation]    Verify that the LIVE MTE fails over to the STANDBY MTE when the TCP-FTP feed line is down longer than HighActTimeOut/LoActTimeOut configuration value.
    ...
    ...    Set feed line down timeout interval (HighActTimeOut/LoActTimeOut) for MTE A to a small value, which still gives the MTE time to start up (currently using 150 seconds) and stop/start SMF.
    ...    Promote MTE A to LIVE.
    ...    Wait for feed line down timeout interval.
    ...    Verify that failover occurred and MTE B is now LIVE.
    Pass Execution If    '${PROTOCOL}' == 'UDP'    Venue Protocol ${PROTOCOL} is not TCP or FTP
    Switch To TD Box    ${CHE_A_IP}
    ${TimeOut}=    Set Variable    200
    ${orgCfgFile}    ${backupCfgFile}    Set TCP-FTP Feed Line Timeout    ${TimeOut}
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    Comment    Failover should occur when feed line timeout on A is reached
    Sleep    ${timeoutLimit}
    Verify MTE State IN Specific Box    ${CHE_A_IP}    STANDBY    5    60
    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    [Teardown]    Run Keyword If    '${PROTOCOL}' != 'UDP'    Restore Feed Line Timeout    ${orgCfgFile}    ${backupCfgFile}

Watchdog QOS - Egress NIC
    [Documentation]    Test the QOS value and MTE failover when disabling MTE Egress NIC http://www.iajira.amers.ime.reuters.com/browse/CATF-1966
    ...
    ...    1. Disable DDNA NIC on LIVE MTE box. \ Verify QOS EgressNIC:50, Total QOS:0. \ Verify STANDBY MTE goes LIVE. \ Enable DDNA NIC. \ Verify QOS returns to 100.\ Standby is receiving Sync Pulses.\ and MTE recovers to STANDBY.
    ...
    ...    2. Disable DDNB NIC on LIVE MTE box. \ Verify QOS EgressNIC:50, Total QOS:0. \ Verify STANDBY MTE goes LIVE. \ Enable DDNB NIC. \ Verify QOS returns to 100. \Standby is receiving Sync Pulses. \ and MTE recovers to STANDBY. \ Standby is receiving Sync Pulses.
    ...
    ...    3. Disable DDNA NIC on STANDBY MTE box. \ Verify QOS EgressNIC:50, Total QOS:0. \ Enable DDNA NIC. \ Verify QOS returns to 100.\ Standby is receiving Sync Pulses.
    ...
    ...    4. Disable DDNB NIC on STANDBY MTE box. \ Verify QOS EgressNIC:50, Total QOS:0. \ Enable DDNB NIC. \ Verify QOS returns to 100. \ Standby is receiving Sync Pulses.
    ...
    ...    5. Disable both DDNA and DDNB on STANDBY MTE box. \ VerifyQOS EgressNIC:0, Total QOS:0. \ Enable both DDNA and DDNB. \ Verify QOS returns to 100. \ Standby is receiving Sync Pulses.
    [Setup]    QoS Case Setup
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    Comment    Disable DDNA on LIVE box, MTE should failover
    Switch To TD Box    ${CHE_A_IP}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    Verify QOS for Egress NIC    100    100    A    ${master_ip}
    Disable NIC    DDNA
    Verify QOS for Egress NIC    50    0    A    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    Enable NIC    DDNA
    Comment    Restart MTE/FTE as a workaround for ERTCADVAMT-1175, which won't be fixed.
    Stop MTE
    Start MTE
    Verify QOS for Egress NIC    100    100    A    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    Verify Sync Pulse Received    ${master_ip}
    Comment    Disable DDNB on LIVE box, MTE should failover
    Switch To TD Box    ${CHE_B_IP}
    Verify QOS for Egress NIC    100    100    B    ${master_ip}
    Disable NIC    DDNB
    Verify QOS for Egress NIC    50    0    B    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Enable NIC    DDNB
    Comment    Restart MTE/FTE workaround again
    Stop MTE
    Start MTE
    Verify QOS for Egress NIC    100    100    B    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    Verify Sync Pulse Received    ${master_ip}
    Comment    Disable NICs on STANDBY
    Disable NIC    DDNA
    Verify QOS for Egress NIC    50    0    B    ${master_ip}
    Enable NIC    DDNA
    Comment    Restart MTE/FTE workaround again
    Stop MTE
    Start MTE
    Verify QOS for Egress NIC    100    100    B    ${master_ip}
    Verify Sync Pulse Received    ${master_ip}
    Disable NIC    DDNB
    Verify QOS for Egress NIC    50    0    B    ${master_ip}
    Enable NIC    DDNB
    Comment    Restart MTE/FTE workaround again
    Stop MTE
    Start MTE
    Verify QOS for Egress NIC    100    100    B    ${master_ip}
    Verify Sync Pulse Received    ${master_ip}
    Disable NIC    DDNA
    Disable NIC    DDNB
    Verify QOS for Egress NIC    ${Empty}    0    B    ${master_ip}
    Enable NIC    DDNA
    Enable NIC    DDNB
    Comment    Restart MTE/FTE workaround again
    Stop MTE
    Start MTE
    Verify QOS for Egress NIC    100    100    B    ${master_ip}
    Verify Sync Pulse Received    ${master_ip}
    [Teardown]    QoS Case Teardown

Watchdog QOS - Ingress NIC
    [Documentation]    Test the QOS value when disable SFH Ingress NIC http://www.iajira.amers.ime.reuters.com/browse/CATF-1968
    ...
    ...    Test Steps
    ...    1. Verify IngressNIC:100, Total QOS:100
    ...    2. Disable EXCHIPA, IngressNIC:50, Total QOS:0
    ...    3. Enable EXCHIPA, IngressNIC:100, Total QOS:100
    ...    4. Disable EXCHIPB, IngressNIC:50, Total QOS:0
    ...    5. Enable EXCHIPB, IngressNIC:100, Total QOS:100
    ...    6. Disable both EXCHIPA and EXCHIPB, IngressNIC:0, Total QOS:0
    ...    7. Enable both EXCHIPA and EXCHIPB, IngressNIC:100, Total QOS:100
    [Setup]    QoS Case Setup
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Switch To TD Box    ${CHE_A_IP}
    Verify QOS for Ingress NIC    100    100    A    ${master_ip}
    Disable NIC    EXCHIPA
    Verify QOS for Ingress NIC    50    0    A    ${master_ip}
    Enable NIC    EXCHIPA
    Verify QOS for Ingress NIC    100    100    A    ${master_ip}
    Disable NIC    EXCHIPB
    Verify QOS for Ingress NIC    50    0    A    ${master_ip}
    Enable NIC    EXCHIPB
    Verify QOS for Ingress NIC    100    100    A    ${master_ip}
    Disable NIC    EXCHIPA
    Disable NIC    EXCHIPB
    Verify QOS for Ingress NIC    0    0    A    ${master_ip}
    Enable NIC    EXCHIPA
    Enable NIC    EXCHIPB
    Verify QOS for Ingress NIC    100    100    A    ${master_ip}
    [Teardown]    QoS Case Teardown

Watchdog QOS - FMS NIC
    [Documentation]    Test the QOS value when disable FMS NIC http://www.iajira.amers.ime.reuters.com/browse/CATF-1967
    ...
    ...    Test Steps
    ...    1. Verify the FMS NIC sholud not equal to MGMT
    ...    2. Verify FMS NIC:100, Total QOS:100
    ...    3. Disable FMS NIC
    ...    4. Verify FMS NIC:0, Total QOS:0
    ...    5. Enable FMS NIC
    ...    6. Verify FMS NIC:100, Total QOS:100
    [Setup]    QoS Case Setup
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Switch To TD Box    ${CHE_A_IP}
    ${interfaceFM}    Get Interface Name By Alias    DB_P_FM
    ${interfaceMGMT}    Get Interface Name By Alias    MGMT
    Should Not Be Equal    ${interfaceFM}    ${interfaceMGMT}    The FMS NIC is equal to MGMT NIC
    Verify QOS for FMS NIC    100    100    A    ${master_ip}
    Disable NIC    DB_P_FM
    Verify QOS for FMS NIC    0    0    A    ${master_ip}
    Enable NIC    DB_P_FM
    Verify QOS for FMS NIC    100    100    A    ${master_ip}
    [Teardown]    QoS Case Teardown

*** Keywords ***
Disable NIC
    [Arguments]    ${NICName}
    [Documentation]    Disable a NIC, ${NICName} should be DDNA, DDNB, EXCHIPA, EXCHIPB, DB_P_FM
    Dictionary Should Contain Key    ${AliasAndInterfaceName}    ${NICName}
    ${interfaceName}    Get From Dictionary    ${AliasAndInterfaceName}    ${NICName}
    Enable Disable Interface    ${interfaceName}    Disable
    Append To List    ${disabledInterfaceName}    ${interfaceName}

Enable NIC
    [Arguments]    ${NICName}
    [Documentation]    Enable NIC, ${NICName} should be DDNA, DDNB, EXCHIPA, EXCHIPB, DB_P_FM
    Dictionary Should Contain Key    ${AliasAndInterfaceName}    ${NICName}
    ${interfaceName}    Get From Dictionary    ${AliasAndInterfaceName}    ${NICName}
    Enable Disable Interface    ${interfaceName}    Enable
    Remove Values From List    ${disabledInterfaceName}    ${interfaceName}

QoS Case Setup
    [Documentation]    Create suite dictionary variable, it saves the NIC Alias and Interface Name, like {'EXCHIPA':'eth0'}, and make sure all interfaces are enabled before the test
    @{disabledInterfaceName}    create list
    Set Suite Variable    @{disabledInterfaceName}
    ${AliasAndInterfaceName}    Create Dictionary
    Set Suite Variable    ${AliasAndInterfaceName}
    ${interfaceName}    Get Interface Name By Alias    DDNA
    Set To Dictionary    ${AliasAndInterfaceName}    DDNA    ${interfaceName}
    ${interfaceName}    Get Interface Name By Alias    DDNB
    Set To Dictionary    ${AliasAndInterfaceName}    DDNB    ${interfaceName}
    ${interfaceName}    Get Interface Name By Alias    EXCHIPA
    Set To Dictionary    ${AliasAndInterfaceName}    EXCHIPA    ${interfaceName}
    ${interfaceName}    Get Interface Name By Alias    EXCHIPB
    Set To Dictionary    ${AliasAndInterfaceName}    EXCHIPB    ${interfaceName}
    ${interfaceName}    Get Interface Name By Alias    DB_P_FM
    Set To Dictionary    ${AliasAndInterfaceName}    DB_P_FM    ${interfaceName}

QoS Case Teardown
    [Documentation]    Make sure all interfaces are enabled after the test
    : FOR    ${interfaceName}    IN    @{disabledInterfaceName}
    \    Enable Disable Interface    ${interfaceName}    Enable

Restore Feed Line Timeout
    [Arguments]    ${orgCfgFile}    ${backupCfgFile}
    [Documentation]    Restore the orginal feed line timeout values (HiActTimeLimit and LoActTimeLimit, HiActTimeOut and LoActTimeOut) in MTE config file and restart dependent components.
    restore remote cfg file    ${orgCfgFile}    ${backupCfgFile}
    stop MTE
    start MTE

Set UDP Feed Line Timeout
    [Arguments]    ${timeoutLimit}
    [Documentation]    Set the feed line timeout values (HiActTimeLimit and LoActTimeLimit) in MTE config file and restart dependent components.
    ${orgCfgFile}    ${backupCfgFile}    backup remote cfg file    ${REMOTE_MTE_CONFIG_DIR}    ${MTE_CONFIG}
    set value in MTE cfg    ${orgCfgFile}    HiActTimeLimit    ${timeoutLimit}
    set value in MTE cfg    ${orgCfgFile}    LoActTimeLimit    ${timeoutLimit}
    Stop SMF
    Start SMF
    Start MTE
    [Return]    ${orgCfgFile}    ${backupCfgFile}

Set TCP-FTP Feed Line Timeout
    [Arguments]    ${TimeOut}
    [Documentation]    Set the feed line timeout values (HiActTimeOut and LoActTimeOut) in MTE config file and restart dependent components.
    ${orgCfgFile}    ${backupCfgFile}    backup remote cfg file    ${REMOTE_MTE_CONFIG_DIR}    ${MTE_CONFIG}
    set value in MTE cfg    ${orgCfgFile}    HiActTimeOut    ${TimeOut}
    set value in MTE cfg    ${orgCfgFile}    LoActTimeOut    ${TimeOut}
    Stop SMF
    Start SMF
    Start MTE
    [Return]    ${orgCfgFile}    ${backupCfgFile}

Verify QoS for CritProcessFail
    [Arguments]    ${node}    ${master_ip}    ${CritProcessFailValue}    ${totalQoSValue}=${EMPTY}
    [Documentation]    Verify the QOS of CritProcessFail on specified node, &{node} should be A, B, C or D.
    ...    If TotalQOS value is specified, also verify it.
    wait for QOS    ${node}    CritProcessFail    ${CritProcessFailValue}    ${master_ip}
    Run Keyword If    '${totalQoSValue}'    verify QOS equal to specific value    ${node}    Total QOS    ${totalQoSValue}    ${master_ip}

Verify QOS for Egress NIC
    [Arguments]    ${EgressQOS}    ${TotalQOS}    ${node}    ${master_ip}
    [Documentation]    Check whether the Egress QOS and Total QOS are equal to the given value
    Wait For QOS    ${node}    EgressNIC    ${EgressQOS}    ${master_ip}
    Verify QOS Equal To Specific Value    ${node}    Total QOS    ${TotalQOS}    ${master_ip}

Verify QOS for Ingress NIC
    [Arguments]    ${IngressQOS}    ${TotalQOS}    ${node}    ${master_ip}
    [Documentation]    Check whether the Ingress QOS and Total QOS are equal to the given value
    Wait For QOS    ${node}    IngressNIC    ${IngressQOS}    ${master_ip}
    Verify QOS Equal To Specific Value    ${node}    Total QOS    ${TotalQOS}    ${master_ip}

Verify QOS for FMS NIC
    [Arguments]    ${FMSQOS}    ${TotalQOS}    ${node}    ${master_ip}
    [Documentation]    Check whether the FMS QOS and Total QOS are equal to the given value
    Wait For QOS    ${node}    FMSNIC    ${FMSQOS}    ${master_ip}
    Verify QOS Equal To Specific Value    ${node}    Total QOS    ${TotalQOS}    ${master_ip}

Verify Sync Pulse Received
    [Arguments]    ${master_ip}
    [Documentation]    Check whether the SyncPulseMissed count has changed after restore DDNA and DDNB.
    ...    Prospect result: No change.
    @{syncPulseCountBefore}    Run Keyword And Continue On Failure    get SyncPulseMissed    ${master_ip}
    Sleep    5
    @{syncPulseCountAfter}    Run Keyword And Continue On Failure    get SyncPulseMissed    ${master_ip}
    lists Should Be Equal    ${syncPulseCountBefore}    ${syncPulseCountAfter}    *ERROR* Sync Pulse Missed Count has increased after restored NIC (Before ${syncPulseCountBefore}, After ${syncPulseCountAfter})
