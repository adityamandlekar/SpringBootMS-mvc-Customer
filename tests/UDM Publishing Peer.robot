*** Settings ***
Documentation     Demo Suit for Peer Related Test Cases
Suite Setup       Suite Setup Two TD Boxes
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
Verify Live Instance Publishing
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1765
    ...
    ...    1. Checking if LIVE Box has output
    ...    2. Checking if STANDBY Box has NO output
    [Tags]    Peer
    [Setup]
    Force MTE to Status    ${CHE_A_IP}    A    LIVE
    ${domain}=    Get Preferred Domain
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    Switch To TD Box    ${CHE_A_IP}
    ${ret}    Send TRWF2 Refresh Request    ${MTE}    ${pubRic}    ${domain}
    Should Not be Empty    ${ret}    CHE_A is LIVE box , should have output
    Switch To TD Box    ${CHE_B_IP}
    ${ret}    Send TRWF2 Refresh Request    ${MTE}    ${pubRic}    ${domain}
    Should be Empty    ${ret}    CHE_B is STANDBY box , should NOT have output
    Force MTE to Status    ${CHE_A_IP}    B    LIVE
    Switch To TD Box    ${CHE_B_IP}
    ${ret}    Send TRWF2 Refresh Request    ${MTE}    ${pubRic}    ${domain}
    Should Not be Empty    ${ret}    CHE_B is LIVE box , should have output
    Switch To TD Box    ${CHE_A_IP}
    ${ret}    Send TRWF2 Refresh Request    ${MTE}    ${pubRic}    ${domain}
    Should be Empty    ${ret}    CHE_A is STANDBY box , should NOT have output

*** Keywords ***
Force MTE to Status
    [Arguments]    ${che_ip}    ${Node}    ${state}
    [Documentation]    Force specific MTE (by CHE_X_IP) to decided stat (LIVE or STANDBY)
    switch MTE LIVE STANDBY status    ${LOCAL_SCWCLI_BIN}    ${MTE}    ${Node}    ${state}    ${USERNAME}    ${PASSWORD}
    ...    ${che_ip}
    Switch To TD Box    ${che_ip}
    verify MTE state    ${MTE}    ${state}
