*** Settings ***
Suite Setup       Suite Setup Two TD Boxes
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
Verify Manual Live/Standby Switch via SCW CLI
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${LOCAL_SCWCLI_BIN}    ${USERNAME}    ${PASSWORD}    ${ip_list}
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    A    LIVE    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    Switch To TD Box    ${CHE_A_IP}
    verify MTE state    ${MTE}    LIVE
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    A    STANDBY    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    verify MTE state    ${MTE}    STANDBY
    Switch To TD Box    ${CHE_B_IP}
    verify MTE state    ${MTE}    LIVE
    lock MTE status    ${LOCAL_SCWCLI_BIN}    ${MTE}    B    LIVE    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    verify MTE state    ${MTE}    LOCKED_LIVE
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    B    STANDBY    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    verify MTE state    ${MTE}    LOCKED_LIVE
    unlock MTE status    ${LOCAL_SCWCLI_BIN}    ${MTE}    B    ${USERNAME}    ${PASSWORD}    ${CHE_A_IP}
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    B    STANDBY    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    verify MTE state    ${MTE}    STANDBY

Verify Sync Pulse Missed QoS
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1763
    ...
    ...    Test Case - Verify Sync Pulse Missed QoS by blocking sync pulse publiscation port and check the missing statistic by SCWCli
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${LOCAL_SCWCLI_BIN}    ${USERNAME}    ${PASSWORD}    ${ip_list}
    @{syncPulseCountBefore}    get SyncPulseMissed    ${LOCAL_SCWCLI_BIN}    ${MTE}    ${USERNAME}    ${PASSWORD}    ${master_ip}
    ${localVenueConfig}=    get MTE config file
    @{labelIDs}=    get MTE config list by section    ${localVenueConfig}    Publishing    LabelID
    Switch to TD Box    ${CHE_A_IP}
    ${state}=    check MTE state    ${MTE}
    : FOR    ${labelID}    IN    @{labelIDs}
    \    Run Keyword If    '${state}' != 'STANDBY'    Switch to TD Box    ${CHE_B_IP}
    \    ${modifyLabelFile}=    set variable    ${LOCAL_TMP_DIR}/ddnPublishersModify.xml
    \    remove xinclude from labelfile    ${LOCAL_TMP_DIR}/ddnPublishers.xml    ${modifyLabelFile}
    \    @{multicastIPandPort}    get_multicast_address_from_lable_file    ${modifyLabelFile}    ${labelID}    ${MTE}
    \    block dataflow by port protocol    INPUT    UDP    @{multicastIPandPort}[1]
    \    @{syncPulseCountAfter}    Run Keyword And Continue On Failure    get SyncPulseMissed    ${LOCAL_SCWCLI_BIN}    ${MTE}    ${USERNAME}
    \    ...    ${PASSWORD}    ${master_ip}
    \    unblock_dataflow
    \    verify sync pulse missed Qos    ${syncPulseCountBefore}    ${syncPulseCountAfter}
    [Teardown]    Case Teardown    ${modifyLabelFile}
