*** Settings ***
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         VenueVariables.py

*** Test Cases ***
Validate Item Sequence Numbering on Failover
    [Documentation]    Validate Item Sequence Numbering on Failover
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2010
    ...
    ...    Verify if mte_state is failover, the response/updated message sequence number could restart from 1, then 4, 5, ... n, n+1.
    ...
    ...    Test Procedures:
    ...    1. Set FailoverPublishRate to 500 on standby MTE config
    ...    2. Reset Sequence Numbers on both machines
    ...    3. Switch to live machine
    ...    4. Inject PCAP1 and Wait For Output \ (a specific RIC A’s exchange with at least 2 SeqNo in sequence, e.g. 1000-1002)
    ...    5. Get RIC List From Remote PCAP
    ...    6. Switch to standby machine
    ...    7. Start capture
    ...    8. Switch live MTE to standby
    ...    9. Ensure previous standby MTE is now live
    ...    10. Inject PCAP2 \ (a specific RIC A’s exchange with at least 2 more SeqNo in sequence, e.g. 1003-1004)
    ...    11. Stop capture MTE output
    ...    12. Loop for each RIC captured
    ...    - Verify the messages' SeqNo (include response and update) follow failover pattern, i.e. 1, 4, 5, …, n
    ...    - The number of C1 messages (include response and update) received should be >= 2
    ...
    ...    Teardown: Restore FailoverPublishRate to 0 on standby MTE config
    [Setup]    Suite Setup Two TD Boxes With Playback
    Comment    Change the MTE config FailoverPublishRate to 500 on standby MTE B, to increase the failover rebuild publish rate
    Switch To TD Box    ${CHE_B_IP}
    ${configFile}=    Convert To Lowercase    ${MTE}.xml
    ${localConfigFile}=    set variable    ${LOCAL_TMP_DIR}${/}local_${configFile}
    ${orgCfgFile}    ${backupCfgFile}    backup remote cfg file    ${VENUE_DIR}    ${configFile}
    get remote file    ${orgCfgFile}    ${localConfigFile}
    add failover publish rate in MTE cfg    ${localConfigFile}    500
    put remote file    ${localConfigFile}    ${orgCfgFile}
    Comment    Inject PCAP1 and get the RIC list of the injected PCAP1
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    Reset Sequence Numbers    ${CHE_A_IP}    ${CHE_B_IP}
    Switch To TD Box    ${CHE_A_IP}
    ${service}=    Get FMS Service Name
    ${domain}=    Get Preferred Domain
    ${injectFile1}=    Generate PCAP File Name    ${service}    Sequence File1    A    domain=${domain}
    ${remoteCapture}=    Inject PCAP File and Wait For Output    ${injectFile1}
    @{ricList}=    Get RIC List From Remote PCAP    ${remoteCapture}    ${domain}
    Comment    Switch live MTE A to standby, and inject PCAP2
    Switch To TD Box    ${CHE_B_IP}
    ${remoteFailoverCapture}=    set variable    ${REMOTE_TMP_DIR}/captureFailover.pcap
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    Start Capture MTE Output    ${remoteFailoverCapture}
    switch MTE LIVE STANDBY status    A    STANDBY    ${master_ip}
    Verify MTE State In Specific Box    ${CHE_A_IP}    STANDBY
    Verify MTE State In Specific Box    ${CHE_B_IP}    LIVE
    ${injectFile2}=    Generate PCAP File Name    ${service}    Sequence File2    A    domain=${domain}
    Inject PCAP File on UDP    wait    ${injectFile2}
    Stop Capture MTE Output
    Comment    Loop for each RIC captured in RIC list, verify the messages SeqNo' follow failover pattern and no. of C1 message should be >=2
    get remote file    ${remoteFailoverCapture}    ${localCapture}
    : FOR    ${ric}    IN    @{ricList}
    \    @{seqNumListC1}=    verify message sequence numbers in capture    ${localCapture}    ${ric}    ${domain}    failover
    \    ${lenSeqNumListC1}=    Get Length    ${seqNumListC1}
    \    Should Be True    ${lenSeqNumListC1} >= 2    The number of C1 messages (include response and update) received should be >= 2
    [Teardown]    Validate Item Sequence Number Logic on Failover Teardown    ${orgCfgFile}    ${backupCfgFile}    ${localConfigFile}

Validate Item Sequence Numbering on Startup
    [Documentation]    Validate Item Sequence Numbering on Startup
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1894
    ...
    ...    Verify unsolicited response sequence numbers in capture start from 0, 4, 5, ... verify updated message sequence numbers start \ from possible 4, 5, .... If response messages exist, first updated message's sequence number should be last response message number + 1 if last response messages sequence number >=4, otherwise first updated message's sequence number should be 4
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    ${domain}    Get Preferred Domain
    ${ric}    ${publishKey}    Get RIC From MTE Cache    ${domain}
    ${service}    Get FMS Service Name
    ${icf_file}=    set variable    ${LOCAL_TMP_DIR}/extract_output.icf
    Run FmsCmd    ${CHE_IP}    Extract    --Services ${service}    --RIC ${ric}    --HandlerName ${MTE}    --Domain ${domain}
    ...    --OutputFile ${icf_file}
    Stop MTE
    Delete Persist Files
    Start Capture MTE Output    ${remoteCapture}
    Start MTE
    Wait For FMS Reorg
    Run FmsCmd    ${CHE_IP}    Insert    --Services ${service}    --InputFile "${icf_file}"
    Stop Capture MTE Output
    get remote file    ${remoteCapture}    ${localCapture}
    ${last_response_seq}    verify unsolicited response sequence numbers in capture    ${localCapture}    ${publishKey}    ${domain}    startup
    ${first_update_seq}    verify updated message sequence numbers in capture    ${localCapture}    ${publishKey}    ${domain}    startup
    ${last_response_seq_plus_one} =    Evaluate    ${last_response_seq}+ 1
    ${first_updatemsg_seq} =    Convert To Integer    ${first_update_seq}
    Run Keyword If    ${last_response_seq}==0    Should Be Equal    ${first_updatemsg_seq}    4
    ...    ELSE    Should Be Equal    ${last_response_seq_plus_one}    ${first_updatemsg_seq}
    [Teardown]    case teardown    ${localCapture}    ${icf_file}

*** Keywords ***
Validate Item Sequence Number Logic on Failover Teardown
    [Arguments]    ${orgCfgFile}    ${backupCfgFile}    ${localConfigFile}
    [Documentation]    Restore MTE config file on standby machine
    Switch To TD Box    ${CHE_B_IP}
    restore remote cfg file    ${orgCfgFile}    ${backupCfgFile}
    Remove Files    ${localConfigFile}
    Stop MTE
    Start MTE
