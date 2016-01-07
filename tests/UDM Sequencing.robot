*** Settings ***
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         VenueVariables.py

*** Test Cases ***
Validate Item Sequence Number Logic
    [Documentation]    Verify published item sequence numbers at MTE start up and rollover case.
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1894
    ...
    ...    After start up MTE, verify if unsolicited response message sequence numbers for a RIC are starting from 0, 4, 5, ... and continue for updated message in MTE output pcap message
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    ${domain}    Get Preferred Domain
    ${ric}    ${publishKey}    Get RIC From MTE Cache    ${domain}
    ${service}    Get FMS Service Name
    ${icf_file}=    set variable    ${LOCAL_TMP_DIR}/extract_output.icf
    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd    ${CHE_IP}    25000    ${LOCAL_FMS_BIN}
    ...    Extract    --Services ${service}    --RIC ${ric}    --HandlerName ${MTE}    --Domain ${domain}    --OutputFile ${icf_file}
    Stop MTE    ${MTE}
    Delete Persist Files    ${MTE}    ${VENUE_DIR}
    Start Capture MTE Output    ${MTE}    ${remoteCapture}
    Start MTE    ${MTE}
    Wait For FMS Reorg    ${MTE}
    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd    ${CHE_IP}    25000    ${LOCAL_FMS_BIN}
    ...    Insert    --Services ${service}    --InputFile "${icf_file}"
    Stop Capture MTE Output    ${MTE}
    get remote file    ${remoteCapture}    ${localCapture}
    ${seq_from_responses}    verify unsolicited response sequence number are increasing    ${localCapture}    ${DAS_DIR}    ${ric}    ${domain}
    ${seq_from_updates}    verify updated message sequence number are increasing    ${localCapture}    ${DAS_DIR}    ${ric}    ${domain}
    Should Be Equal    ${seq_from_responses[0]}    0
    List Should Not Contain Value    ${seq_from_responses}    1
    List Should Not Contain Value    ${seq_from_responses}    2
    List Should Not Contain Value    ${seq_from_responses}    3
    Run Keyword If    ${seq_from_responses[-1]} >= 4    Log    More than two response messages exist
    Run Keyword If    len(${seq_from_responses})==1    Return ${seq_from_updates[0]}==4
    ${last_responses_item_with_addition} =    Evaluate    ${seq_from_responses[-1]} + ${1}
    ${first_updatemsg_seq} =    Convert To Integer    ${seq_from_updates[0]}
    Run Keyword If    ${seq_from_responses[-1]}==0    Should Be Equal    ${first_updatemsg_seq}    4
    Run Keyword If    ${seq_from_responses[-1]}!=0    Should Be Equal    ${last_responses_item_with_addition}    ${first_updatemsg_seq}
    [Teardown]    case teardown    ${localCapture}    ${icf_file}
