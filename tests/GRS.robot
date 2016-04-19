*** Settings ***
Documentation     Verify GRS functionality
Suite Setup       Suite Setup With Playback
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
Check GRS StatBlocks
    Reset Sequence Numbers
    ${grsStreamNames}    get stat blocks for category    GRS    Input
    ${lastPacketSNBeforePlayback}    Create List
    :FOR    ${grsStreamName}    IN    @{grsStreamNames}
    \    ${value}    get stat block field    GRS    ${grsStreamName}    lastPacketSN
    \    Append To List    ${lastPacketSNBeforePlayback}    ${value}
    ${serviceName}=    Get FMS Service Name
    ${pcapFile}=    Generate PCAP File Name    ${serviceName}    GRS
    Inject PCAP File on UDP    ${pcapFile}
    Sleep    10
    ${lastPacketSNAfterPlayback}    Create List
    :FOR    ${grsStreamName}    IN    @{grsStreamNames}
    \    ${value}    get stat block field    GRS    ${grsStreamName}    lastPacketSN
    \    Append To List    ${lastPacketSNAfterPlayback}    ${value}
    Log    ${lastPacketSNBeforePlayback}
    Log    ${lastPacketSNAfterPlayback}
    Should Not Be Equal    ${lastPacketSNBeforePlayback}    ${lastPacketSNAfterPlayback}    GRS last Packet Sequence Number has not increase after playback

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
    ${remoteCapture}=    Inject File and Wait for Output    ${injectFile}
    ${ricFile}=    Create Remote RIC List    ${remoteCapture}    ${domain}
    Reset Sequence Numbers
    ${startupFIDs}=    Get FID values    ${ricFile}    ${domain}
    ${remoteCapture}=    Inject File and Wait for Output    ${injectFile}
    ${afterInjectionFIDs}=    Get FID values    ${ricFile}    ${domain}
    Run Keyword and Expect Error    Following keys*    Dictionary of Dictionaries Should Be Equal    ${startupFIDs}    ${afterInjectionFIDs}
    Restart MTE With GRS Recovery
    ${afterRecoveryFIDs}=    Get FID values    ${ricFile}    ${domain}
    Dictionary of Dictionaries Should Be Equal    ${afterInjectionFIDs}    ${afterRecoveryFIDs}
    [Teardown]    Run Keyword If Test Passed    Delete Remote Files    ${remoteCapture}    ${ricFile}

*** Keywords ***
Create Remote RIC List
    [Arguments]    ${remoteCapture}    ${domain}
    @{ricList}=    Get RIC List From Remote PCAP    ${remoteCapture}    ${domain}
    ${ricFile}=    Set Variable    ${REMOTE_TMP_DIR}/ricList.txt
    Create Remote File Content    ${ricFile}    ${ricList}
    [Return]    ${ricFile}

Get FID Values
    [Arguments]    ${ricList}    ${domain}
    ${result}=    Send TRWF2 Refresh Request No Blank FIDs    ${ricList}    ${domain}    -RL 1
    ${ricDict}=    Convert DataView Response to MultiRIC Dictionary    ${result}
    [Return]    ${ricDict}

Get RIC List From Remote PCAP
    [Arguments]    ${remoteCapture}    ${domain}
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    @{ricList}=    Get RICs From PCAP    ${localCapture}    ${domain}
    Should Not Be Empty    ${ricList}    Injected file produced no published RICs
    [Return]    ${ricList}

Inject File and Wait For Output
    [Arguments]    ${injectFile}
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    Start Capture MTE Output    ${remoteCapture}
    Inject PCAP File on UDP    ${injectFile}
    Stop Capture MTE Output
    [Return]    ${remoteCapture}

Restart MTE With GRS Recovery
    ${currDateTime}    get date and time
    Stop MTE
    Delete Persist Files
    Start MTE
    Wait SMF Log Message After Time    Finished Startup, Begin Regular Execution    ${currDateTime}
