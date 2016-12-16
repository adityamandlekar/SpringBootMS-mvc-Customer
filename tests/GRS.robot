*** Settings ***
Documentation     Verify GRS functionality on single machine
Suite Setup       Suite Setup With Playback
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
GRS Writes to PCAP on Feed Close
    [Documentation]    Verify that GRS writes messages from its buffer to a PCAP file upon feed close event.
    ...    1. Delete GRS PCAP files
    ...    2. Reset sequence numbers
    ...    3. Inject generic pcap file
    ...    4. Force feed close time
    ...    5. Verify GRS PCAP file is created
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2120
    Reset Sequence Numbers
    ${service}=    Get FMS Service Name
    ${injectFile}=    Generate PCAP File Name    ${service}    General RIC Update
    ${remoteCapture}=    Inject PCAP File and Wait For Output    ${injectFile}
    ${exlFiles}    ${modifiedExlFiles}    Go Into End Feed Time    ${service}
    ${files}    Search Remote Files    ${BASE_DIR}    *.pcap    ${True}
    Should Not Be Empty    ${files}
    [Teardown]    Run Keywords    Restore EXL Changes    ${service}    ${exlFiles}
    ...    AND    Case Teardown    @{modifiedExlFiles}

MTE Start of Day Recovery
    [Documentation]    Verify that the MTE recovers lost messages by sending 'start of day' request to GRS.
    ...    1. Get the list of RICs that are changed by the PCAP file.
    ...    2. Get the initial FID values for those RICs before injection.
    ...    3. Get the FID values after the injection.
    ...    4. Verify the before and after FID values differ (i.e. the injection changes some FIDs)
    ...    4. Restart the MTE to create 'start of day' GRS recovery, and get the FID values after recovery.
    ...    6. Verify that the FID values after injection match those after recovery.
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1990
    ${service}=    Get FMS Service Name
    ${injectFile}=    Generate PCAP File Name    ${service}    General RIC Update
    ${domain}=    Get Preferred Domain
    Reset Sequence Numbers
    ${remoteCapture}=    Inject PCAP File and Wait For Output    ${injectFile}
    ${ricList}=    Get RIC List From Remote PCAP    ${remoteCapture}    ${domain}
    ${remoteRicFile}=    Set Variable    ${REMOTE_TMP_DIR}/ricList.txt
    Create Remote File Content    ${remoteRicFile}    ${ricList}
    Reset Sequence Numbers
    ${startupFIDs}=    Get FID Values From Refresh Request    ${remoteRicFile}    ${domain}
    ${remoteCapture}=    Inject PCAP File and Wait For Output    ${injectFile}
    ${afterInjectionFIDs}=    Get FID Values From Refresh Request    ${remoteRicFile}    ${domain}
    Run Keyword and Expect Error    Following keys*    Dictionary of Dictionaries Should Be Equal    ${startupFIDs}    ${afterInjectionFIDs}
    Restart MTE With GRS Recovery
    ${afterRecoveryFIDs}=    Get FID Values From Refresh Request    ${remoteRicFile}    ${domain}
    Dictionary of Dictionaries Should Be Equal    ${afterInjectionFIDs}    ${afterRecoveryFIDs}
    [Teardown]    Run Keyword If Test Passed    Delete Remote Files    ${remoteCapture}    ${remoteRicFile}

MTE Recovery by SN Range Request
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1989
    ...
    ...    Verify that the MTE recovers from gaps in the message sequence numbers by requesting the missed messages from GRS.
    ...    - create baseline for FID values by injecting non-gapped pcap into both GRS and MTE.
    ...    - inject the non-gap pcap file into GRS and gapped pcap file into MTE.
    ...    - verify gap recovery occurred by verifying the FID values match the baseline FID values.
    Reset Sequence Numbers
    ${orgCfgFile}    ${backupCfgFile}    backup remote cfg file    ${REMOTE_MTE_CONFIG_DIR}    ${MTE_CONFIG}
    ${service}    Get FMS Service Name
    ${domain}=    Get Preferred Domain
    ${injectFile}=    Generate FH PCAP File Name    ${service}    General FH Output    FH=${FH}
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    ${loopbackIntf}=    set variable    127.0.0.1
    Start Capture MTE Output    ${remoteCapture}
    Inject PCAP File on UDP at MTE Box    ${loopbackIntf}    ${injectFile}
    Stop Capture MTE Output
    ${ricList}=    Get RIC List From Remote PCAP    ${remoteCapture}    ${domain}
    ${remoteRicFile}=    Set Variable    ${REMOTE_TMP_DIR}/ricList.txt
    Create Remote File Content    ${remoteRicFile}    ${ricList}
    ${FIDsFromLargeFile}=    Get FID Values From Refresh Request    ${remoteRicFile}    ${domain}
    Delete Remote Files    ${remoteCapture}
    Comment    Now we have none gapped injection refresh data.
    ${pcapFile}=    Generate FH PCAP File Name    ${service}    General Gapped FH Output    FH=${FH}
    ${gappedPcap}=    Modify MTE config and Injection pcap Port Info    ${orgCfgFile}    ${pcapFile}
    Reset Sequence Numbers
    Inject PCAP File on UDP at MTE Box    ${loopbackIntf}    ${injectFile}
    Inject PCAP File on UDP at MTE Box    ${loopbackIntf}    ${gappedPcap}
    ${FIDsFromFiles}=    Get FID Values From Refresh Request    ${remoteRicFile}    ${domain}
    Delete Remote Files    ${remoteRicFile}
    Dictionary of Dictionaries Should Be Equal    ${FIDsFromLargeFile}    ${FIDsFromFiles}
    [Teardown]    restore remote cfg file    ${orgCfgFile}    ${backupCfgFile}

*** Keywords ***
Restart MTE With GRS Recovery
    ${currDateTime}    get date and time
    Stop MTE
    Delete Persist Files
    Start MTE
    Wait SMF Log Message After Time    Finished Startup, Begin Regular Execution    ${currDateTime}
