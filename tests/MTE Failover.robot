*** Settings ***
Suite Setup       Suite Setup Two TD Boxes
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
Verify Manual Live/Standby Switch via SCW CLI
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
    ${master_ip}    get master box ip    ${LOCAL_SCWCLI_BIN}    ${USERNAME}    ${PASSWORD}    ${ip_list}
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    A    LIVE    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    A    STANDBY    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    A    LOCK_LIVE    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    B    LOCK_STANDBY    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    LOCKED_STANDBY
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    B    UNLOCK    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    B    LOCK_LIVE    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LOCKED_LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    A    UNLOCK    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    LIVE
    Verify MTE State In Specific Box    ${CHE_B_IP}    STANDBY
    [Teardown]    Manual Switch Live/Standby Case Teardown    ${master_ip}

*** Keywords ***
Verify MTE State In Specific Box
    [Arguments]    ${che_ip}    ${state}
    Switch To TD Box    ${che_ip}
    verify MTE state    ${MTE}    ${state}

Manual Switch Live/Standby Case Teardown
    [Arguments]    ${master_ip}
    [Documentation]    If a KW fail, unlocking both A and B
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    A    UNLOCK    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    B    UNLOCK    ${USERNAME}    ${PASSWORD}
    ...    ${master_ip}
