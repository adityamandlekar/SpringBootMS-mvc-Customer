*** Settings ***
Documentation     Verify GRS functionality on single machine
Suite Setup       Suite Setup With Playback
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
Check GRS StatBlocks
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1995
    ...
    ...    Verify that GRS receives data from FH \ and updates lastPacketSN stat block field.
    Reset Sequence Numbers
    ${grsStreamNames}    get stat blocks for category    GRS    Input
    ${lastPacketSNBeforePlayback}    Create List
    : FOR    ${grsStreamName}    IN    @{grsStreamNames}
    \    ${value}    get stat block field    GRS    ${grsStreamName}    lastPacketSN
    \    Append To List    ${lastPacketSNBeforePlayback}    ${value}
    ${serviceName}=    Get FMS Service Name
    ${pcapFile}=    Generate PCAP File Name    ${serviceName}    General RIC Update
    Inject PCAP File and Wait For Output    ${pcapFile}
    ${lastPacketSNAfterPlayback}    Create List
    : FOR    ${grsStreamName}    IN    @{grsStreamNames}
    \    ${value}    get stat block field    GRS    ${grsStreamName}    lastPacketSN
    \    Append To List    ${lastPacketSNAfterPlayback}    ${value}
    Should Not Be Equal    ${lastPacketSNBeforePlayback}    ${lastPacketSNAfterPlayback}    GRS last Packet Sequence Number has not increased after playback
    [Teardown]

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
    wait for process to exist    GRS
    comment    stop smf and check GRS
    stop smf
    wait for process to not exist    GRS
    start smf
    wait for process to exist    GRS
    [Teardown]    start smf

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
    ...    Prepare one pcap from exchange (no gaps) and split it to two pcap file. pcap1 (frame 1 to N), pcap 2 (frame N+1 to end).
    ...    With GRS and MTE running, playback whole pcap and request for all possible RICs response messages and save fid-value to dictionary1
    ...
    ...    Stop FH, GRS, MTE. Delete GRS pcap, persist file.
    ...    Check InputPortStatsBlock_0 and InputPortStatsBlock_1's segment count
    ...    Start FH, GRS, Replay pcap1
    ...    Start MTE, \ Replay pcap2
    ...
    ...    Check InputPortStatsBlock_0 and InputPortStatsBlock_1's segment count
    ...    request for all possible RICs response messages and \ save fid-value to dictionary2
    ...
    ...    fid-value dictionary1 and fid-value dictionary2 should be same.
    ...    InputPortStatsBlock_0 and InputPortStatsBlock_1's segment received \ count increased
    Stop Process    GRS
    Delete Remote Files Matching Pattern    ${BASE_DIR}    *.pcap    ${True}
    Reset Sequence Numbers
    ${service}    Get FMS Service Name
    ${domain}=    Get Preferred Domain
    ${injectFile}=    Generate PCAP File Name    ${service}    General RIC Update
    ${remoteCapture}=    Inject PCAP File And Wait For Output    ${injectFile}
    ${ricList}=    Get RIC List From Remote PCAP    ${remoteCapture}    ${domain}
    ${remoteRicFile}=    Set Variable    ${REMOTE_TMP_DIR}/ricList.txt
    Create Remote File Content    ${remoteRicFile}    ${ricList}
    ${FIDsFromLargeFile}=    Get FID Values From Refresh Request    ${remoteRicFile}    ${domain}
    Delete Remote Files    ${remoteCapture}
    Comment    run first pcap (frame: 1-n) without MTE, then second pcap (frame: n-end) with MTE running. Check stats and response messages fid value
    Stop Process    GRS
    Delete Remote Files Matching Pattern    ${BASE_DIR}    *.pcap    ${True}
    Reset Sequence Numbers
    Stop MTE
    ${port0Prev}=    get count from stat block    ${MTE}    InputPortStatsBlock_0    segmentsReceivedCount
    ${port1Prev}=    get count from stat block    ${MTE}    InputPortStatsBlock_1    segmentsReceivedCount
    ${injectFile1}=    Generate PCAP File Name    ${service}    General RIC Update1
    ${injectFile2}=    Generate PCAP File Name    ${service}    General RIC Update2
    ${remoteCapture}=    Inject PCAP File And Wait For Output    ${injectFile1}
    Delete Remote Files    ${remoteCapture}
    Start MTE
    wait for StatBlock    ${MTE}    InputPortStatsBlock_0    lineOpenStatus    1
    ${remoteCapture}=    Inject PCAP File And Wait For Output    ${injectFile2}
    ${port0After}=    get count from stat block    ${MTE}    InputPortStatsBlock_0    segmentsReceivedCount
    ${port1After}=    get count from stat block    ${MTE}    InputPortStatsBlock_1    segmentsReceivedCount
    ${FIDsFromFiles}=    Get FID Values From Refresh Request    ${remoteRicFile}    ${domain}
    Should Be True    ${port0After} > ${port0Prev}
    Should Be True    ${port1After} > ${port1Prev}
    Dictionary of Dictionaries Should Be Equal    ${FIDsFromLargeFile}    ${FIDsFromFiles}
    [Teardown]    Delete Remote Files    ${remoteCapture}    ${remoteRicFile}

Verify GRS stream creation
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1996
    ...
    ...    1. Parse venue grs config file and capture all the stream names
    ...    2. Compare with StatBlock to ensure all steam names are available
    ${files}    search remote files    ${BASE_DIR}    *_grs.json    ${TRUE}
    ${streamNames}    Create List
    : FOR    ${file}    IN    @{files}
    \    ${localFile}    Set Variable    ${LOCAL_TMP_DIR}/grs.json
    \    get remote file    ${file}    ${localFile}
    \    ${streams}    get GRS stream names from config file    ${localFile}
    \    Append To List    ${streamNames}    @{streams}
    : FOR    ${streamName}    IN    @{streamNames}
    \    get stat block field    GRS    ${streamName}    InputPacket
    [Teardown]    case teardown    ${localFile}

*** Keywords ***
Restart MTE With GRS Recovery
    ${currDateTime}    get date and time
    Stop MTE
    Delete Persist Files
    Start MTE
    Wait SMF Log Message After Time    Finished Startup, Begin Regular Execution    ${currDateTime}
