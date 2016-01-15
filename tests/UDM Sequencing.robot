*** Settings ***
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         VenueVariables.py

*** Test Cases ***
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
    Run FmsCmd    ${CHE_IP}    25000    ${LOCAL_FMS_BIN}    Extract    --Services ${service}    --RIC ${ric}
    ...    --HandlerName ${MTE}    --Domain ${domain}    --OutputFile ${icf_file}
    Stop MTE    ${MTE}
    Delete Persist Files    ${MTE}    ${VENUE_DIR}
    Start Capture MTE Output    ${MTE}    ${remoteCapture}
    Start MTE    ${MTE}
    Wait For FMS Reorg    ${MTE}
    Run FmsCmd    ${CHE_IP}    25000    ${LOCAL_FMS_BIN}    Insert    --Services ${service}    --InputFile "${icf_file}"
    Stop Capture MTE Output    ${MTE}
    get remote file    ${remoteCapture}    ${localCapture}
    ${last_response_seq}    verify unsolicited response sequence numbers in capture    ${localCapture}    ${DAS_DIR}    ${ric}    ${domain}    startup
    ${first_update_seq}    verify updated message sequence numbers in capture    ${localCapture}    ${DAS_DIR}    ${ric}    ${domain}    startup
    ${last_response_seq_plus_one} =    Evaluate    ${last_response_seq}+ 1
    ${first_updatemsg_seq} =    Convert To Integer    ${first_update_seq}
    Run Keyword If    ${last_response_seq}==0    Should Be Equal    ${first_updatemsg_seq}    4
    ...    ELSE    Should Be Equal    ${last_response_seq_plus_one}    ${first_updatemsg_seq}
    [Teardown]    case teardown    ${localCapture}    ${icf_file}
