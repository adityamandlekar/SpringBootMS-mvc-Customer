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
