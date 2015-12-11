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
    [Setup]
    Force MTE to State    ${CHE_A_IP}
    ${domain}=    Get Preferred Domain
    ${ric}    ${pubRic}    Get RIC From MTE Cache    ${domain}
    Switch To TD Box    ${CHE_A_IP}
    ${ret}    Send TRWF2 Refresh Request    ${MTE}    ${pubRic}    ${domain}
    Should Not be Empty    ${ret}
    Switch To TD Box    ${CHE_B_IP}
    ${ret}    Send TRWF2 Refresh Request    ${MTE}    ${pubRic}    ${domain}
    Should be Empty    ${ret}

*** Keywords ***
Force MTE to State
    [Arguments]    ${che_ip}    ${state}=ENTITY_LIVE
    [Documentation]    Force specific MTE (by CHE_X_IP) to decided stat (ENTITY_LIVE or ENTITY_STANDBY)
    ${StandbyBox} =    set variable if    ('${che_ip}' == '${CHE_B_IP}' and '${state}' == 'ENTITY_LIVE') or ('${che_ip}' == '${CHE_A_IP}' and '${state}' == 'ENTITY_STANDBY')    ${CHE_A_IP}    ${CHE_B_IP}
    Switch To TD Box    ${StandbyBox}
    stop MTE    ${MTE}
    start MTE    ${MTE}
    Switch To TD Box    ${che_ip}
    ${ret_state} =    verify MTE state    ${MTE}
    Run Keyword unless    '${state}' == '{ret_state}'    Fail    Fail to force ${che_ip} to ${state}
