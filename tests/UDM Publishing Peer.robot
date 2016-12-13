*** Settings ***
Documentation     Demo Suit for Peer Related Test Cases
Suite Setup       Suite Setup Two TD Boxes
Suite Teardown    Suite Teardown
Force Tags        Peer
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
Verify Live Instance Publishing
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1765
    ...
    ...    1. Checking if LIVE Box has output
    ...    2. Checking if STANDBY Box has NO output
    [Setup]
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    Switch To TD Box    ${CHE_A_IP}
    Force MTE to Status    ${master_ip}    A    LIVE
    ${domain}=    Get Preferred Domain
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    ${ret}    Send TRWF2 Refresh Request    ${pubRic}    ${domain}
    Should Not be Empty    ${ret}    CHE_A is LIVE box , should have output
    Switch To TD Box    ${CHE_B_IP}
    ${ret}    Send TRWF2 Refresh Request    ${pubRic}    ${domain}
    Should be Empty    ${ret}    CHE_B is STANDBY box , should NOT have output
    Switch To TD Box    ${CHE_B_IP}
    Force MTE to Status    ${master_ip}    B    LIVE
    ${ret}    Send TRWF2 Refresh Request    ${pubRic}    ${domain}
    Should Not be Empty    ${ret}    CHE_B is LIVE box , should have output
    Switch To TD Box    ${CHE_A_IP}
    ${ret}    Send TRWF2 Refresh Request    ${pubRic}    ${domain}
    Should be Empty    ${ret}    CHE_A is STANDBY box , should NOT have output

*** Keywords ***
Force MTE to Status
    [Arguments]    ${master_ip}    ${Node}    ${state}
    [Documentation]    Force specific MTE (by CHE_X_IP) to decided stat (LIVE or STANDBY)
    switch MTE LIVE STANDBY status    ${Node}    ${state}    ${master_ip}
    verify MTE state    ${state}
