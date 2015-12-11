*** Settings ***
Documentation     Verify MTE startup functionality.
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
Full Reorg on Startup
    [Documentation]    Verify on startup the MTE does a Full Reorg if the Persist File does not exist.
    Stop MTE    ${MTE}
    Delete Persist Files    ${MTE}    ${VENUE_DIR}
    Start MTE    ${MTE}
    Wait For FMS Reorg    ${MTE}
    verify FMS full reorg    ${MTE}
    [Teardown]

Partial REORG on Startup
    [Documentation]    Verify Partial REORG behaviour of MTE http://www.iajira.amers.ime.reuters.com/browse/CATF-1755
    Start MTE    ${MTE}
    ${service}    Get FMS Service Name    ${MTE}
    Load All EXL Files    ${service}    ${CHE_IP}
    Stop MTE    ${MTE}
    Persist File Should Exist    ${MTE}    ${VENUE_DIR}
    Start MTE    ${MTE}
    verify FMS partial reorg    ${MTE}
    [Teardown]

*** Keywords ***
verify FMS full reorg
    [Arguments]    ${mte}
    statBlock should be equal    ${mte}    FMS    lastReorgType    2    lastReorgType should be 2 (Full Reorg)

verify FMS partial reorg
    [Arguments]    ${mte}
    wait for StatBlock    ${mte}    FMS    lastReorgType    1
