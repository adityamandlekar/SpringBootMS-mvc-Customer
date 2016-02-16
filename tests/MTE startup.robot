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
    Stop MTE
    Delete Persist Files
    Start MTE
    Wait For FMS Reorg
    verify FMS full reorg
    [Teardown]

Partial REORG on Startup
    [Documentation]    Verify Partial REORG behaviour of MTE http://www.iajira.amers.ime.reuters.com/browse/CATF-1755
    Start MTE
    ${service}    Get FMS Service Name
    Load All EXL Files    ${service}    ${CHE_IP}
    Stop MTE
    Persist File Should Exist
    Start MTE
    verify FMS partial reorg
    [Teardown]

*** Keywords ***
verify FMS full reorg
    statBlock should be equal    ${MTE}    FMS    lastReorgType    2    lastReorgType should be 2 (Full Reorg)

verify FMS partial reorg
    wait for StatBlock    ${MTE}    FMS    lastReorgType    1
