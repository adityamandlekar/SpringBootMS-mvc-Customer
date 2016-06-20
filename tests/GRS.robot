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
    ...    Verify that the MTE recovers from gaps in the message sequence numbers by requesting the missed messages from GRS.
    ...    - create baseline for FID values by injecting non-gapped pcap into both GRS and MTE.
    ...    - inject the non-gap pcap file into GRS and gapped pcap file into MTE.
    ...    - verify gap recovery occurred by verifying the FID values match the baseline FID values.
    Reset Sequence Numbers
    ${configFile}=    Convert To Lowercase    ${MTE}.xml
    ${orgCfgFile}    ${backupCfgFile}    backup remote cfg file    ${VENUE_DIR}    ${configFile}
    ${service}    Get FMS Service Name
    ${domain}=    Get Preferred Domain
    ${injectFile}=    Generate FH PCAP File Name    ${service}    General FH Output    FH={FH}
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
    ${pcapFile}=    Generate FH PCAP File Name    ${service}    General Gapped FH Output    FH={FH}
    ${gappedPcap}=    Modify MTE config and Injection pcap Port Info    ${orgCfgFile}    ${pcapFile}
    Reset Sequence Numbers
    Inject PCAP File on UDP at MTE Box    ${loopbackIntf}    ${injectFile}
    Inject PCAP File on UDP at MTE Box    ${loopbackIntf}    ${gappedPcap}
    ${FIDsFromFiles}=    Get FID Values From Refresh Request    ${remoteRicFile}    ${domain}
    Delete Remote Files    ${remoteRicFile}
    Dictionary of Dictionaries Should Be Equal    ${FIDsFromLargeFile}    ${FIDsFromFiles}
    [Teardown]    restore remote cfg file    ${orgCfgFile}    ${backupCfgFile}

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

MTE Startup with GRS Not Running
    [Documentation]    Verify that the MTE properly handles a failure to connect to GRS.
    ...    1. Stop the MTE
    ...    2. Stop the GRS
    ...    3. Start the MTE
    ...    4. Verify the MTE is unable to connect to the GRS by SMF log
    ...    5. Start GRS
    ...    6. Verify the MTE is connected to the GRS by SMF log
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1991
    Stop MTE
    Stop Process    GRS
    ${currDateTime}    Get Date and Time
    Start MTE
    Wait SMF Log Message After Time    Unable to connect to the GRS\|Failed to connect to GRS    ${currDateTime}    2    120
    ${currDateTime}    Get Date and Time
    Start Process    GRS
    Wait SMF Log Message After Time    ${MTE}..Connected to IP:127.0.0.1-TCP    ${currDateTime}    2    120

*** Keywords ***
Restart MTE With GRS Recovery
    ${currDateTime}    get date and time
    Stop MTE
    Delete Persist Files
    Start MTE
    Wait SMF Log Message After Time    Finished Startup, Begin Regular Execution    ${currDateTime}

Modify MTE config and Injection pcap Port Info
    [Arguments]    ${orgCfgFile}    ${pcapFile}
    ${mteConfigFile}=    Get MTE Config File
    ${portstr}=    get MTE config value    ${mteConfigFile}    Inputs    ${FH}    FHRealtimeLine    ServiceName
    ${portNum}=    Convert to Integer    ${portstr}
    ${portNumNew}=    Set Variable    ${portNum+ 1}
    ${modifiedPCAP}=    Rewrite PCAP File    ${pcapFile}    --portmap=${portNum}:${portNumNew}
    Set value in MTE cfg    ${orgCfgFile}    ServiceName    ${portNumNew}
    [Return]    ${modifiedPCAP}
