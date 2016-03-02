*** Settings ***
Suite Setup       Suite Setup with Playback
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
OTFC PE and RIC mangling
    [Documentation]    For OTFC RIC, PE mangling and RIC mangling still works, it includes below scenario:
    ...    a.	Mangled PE + Prefix ![ mangling
    ...    b.	Non-mangled PE + Prefix !! mangling
    ...    1. Change to Elektron SOU stage
    ...    2. Inject PCAP
    ...    3. Check OTFC log
    ...    4. Get an OTFC RIC
    ...    5. Check the Prefix mangling
    ...    6. Check the PE
    ...    7. Change to Elektron RRG
    ...    8. Check the Prefix mangling
    ...    9. Fallback the mangling setting
    Start MTE
    Set Mangling Rule    SOU
    @{expected_pe}    Create List    4128    4245    4247
    ${domain}    Get Preferred Domain
    ${serviceName}=    Get FMS Service Name
    ${currDateTime}    get date and time
    ${otfcExtractFile}    set variable    ${LOCAL_TMP_DIR}/otfcExtractFile.icf
    Inject PCAP in TCP    ${PLAYBACK_PCAP_DIR}
    ${Ric}    wait and get OTFC RIC from smf    ${MTE}.+Created on-the-fly Real-time    ${currDateTime}
    ${Ric}    ${pubRic}    Run Keyword And Continue On Failure    Verify RIC In MTE Cache    ${Ric}
    ${mangelPrefix}    Remove String    ${pubRic}    ${Ric}
    should be equal    ${mangelPrefix}    ![
    extract icf    ${Ric}    ${domain}    ${otfcExtractFile}    ${serviceName}
    check PE in icf file    ${otfcExtractFile}    @{expected_pe}
    Set Mangling Rule    RRG
    ${Ric}    ${pubRic}    Run Keyword And Continue On Failure    Verify RIC In MTE Cache    ${Ric}
    ${mangelPrefix}    Remove String    ${pubRic}    ${Ric}
    should be equal    ${mangelPrefix}    !!
    Load Mangling Settings
    [Teardown]    case teardown    ${PLAYBACK_PCAP_DIR}

*** Keywords ***
