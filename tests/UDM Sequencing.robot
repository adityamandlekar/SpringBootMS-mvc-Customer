*** Settings ***
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         VenueVariables.py

*** Test Cases ***
Validate Item Sequence Number Logic
    [Documentation]    Validate Item Sequence Number Logic.
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1894
    ...
    ...    MTE starts up case: 'verify unsolicited response sequence numbers in capture' checks sequence numbers starting from 0, 4, 5, ... 'verify updated message sequence numbers in capture' checks sequence numbers starting from possible 4, 5, .... If response messages exist, first updated message's sequence number \ in MTE output pcap should be last response message number + 1 if last response messages sequence number >=4, otherwise first updated message's sequence number should be 4
    ...
    ...    MTE rollover case: 'verify unsolicited response sequence numbers in capture' and 'verify updated message sequence numbers in capture' check sequence numbers starting from possible 3, 4, 5, ....
    ...
    ...    MTE failover case: 'verify unsolicited response sequence numbers in capture' and \ 'verify updated message sequence numbers in capture' check sequence numbers starting from possible 1, 4, 5, ...
    ...
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
    ${seq_from_responses}    verify unsolicited response sequence numbers in capture    ${localCapture}    ${DAS_DIR}    ${ric}    ${domain}
    ${seq_from_updates}    verify updated message sequence numbers in capture    ${localCapture}    ${DAS_DIR}    ${ric}    ${domain}
    ${last_responses_item_with_addition} =    Evaluate    ${seq_from_responses[-1]} + ${1}
    ${first_updatemsg_seq} =    Convert To Integer    ${seq_from_updates[0]}
    Run Keyword If    ${seq_from_responses[-1]}==0    Should Be Equal    ${first_updatemsg_seq}    4
    Run Keyword If    ${seq_from_responses[-1]}!=0    Should Be Equal    ${last_responses_item_with_addition}    ${first_updatemsg_seq}
    [Teardown]    case teardown    ${localCapture}    ${icf_file}
