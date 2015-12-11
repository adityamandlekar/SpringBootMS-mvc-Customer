*** Settings ***
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
Validate Downstream FID publication from Reconcile
    [Documentation]    Validate output from MTE after manual triggered Reconcile against FIDFilter.txt
    Start Capture MTE Output    ${MTE}    ${REMOTE_TMP_DIR}/capture.pcap
    Stop MTE    ${MTE}
    Delete Persist Files    ${MTE}    ${VENUE_DIR}
    Start MTE    ${MTE}
    Wait For FMS Reorg    ${MTE}
    Stop Capture MTE Output    ${MTE}
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    verify FIDfilter FIDs are in message    ${LOCAL_TMP_DIR}/capture_local.pcap    ${VENUE_DIR}    ${DAS_DIR}
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify Outbound Heartbeats
    [Documentation]    Verify if MTE has publish heartbeat at specified interval
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1721
    Start MTE    ${MTE}
    Start Capture MTE Output    ${MTE}
    Stop Capture MTE Output    ${MTE}    5    10
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${LOCAL_TMP_DIR}/capture_local.pcap
    verify_MTE_heartbeat_in_message    ${LOCAL_TMP_DIR}/capture_local.pcap    ${DAS_DIR}    1
    [Teardown]    case teardown    ${LOCAL_TMP_DIR}/capture_local.pcap
