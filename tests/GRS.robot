*** Settings ***
Documentation     Verify GRS functionality
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
GRS Control by SMF
    [Documentation]    Perform SMF start/stop to verify the GRS is being started or shut down by SMF
    ...    Kill GRS and make sure it is started by smf
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1895
    [Setup]
    comment    smf already started
    ${result}=    find processes by pattern    GRS
    Should Contain    ${result}    GRS
    comment    kill process, smf will start it
    Kill Processes    GRS
    sleep    2
    ${result}=    find processes by pattern    GRS
    Should Contain    ${result}    GRS
    comment    stop smf and check GRS
    stop smf
    sleep    5
    ${result}=    find processes by pattern    GRS
    Should Be Empty    ${result}
    start smf
    sleep    8
    ${result}=    find processes by pattern    GRS
    Should Contain    ${result}    GRS
    [Teardown]

*** Keywords ***
