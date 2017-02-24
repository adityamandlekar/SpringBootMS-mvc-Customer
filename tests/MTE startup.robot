*** Settings ***
Documentation     Verify MTE startup functionality.
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
Full Reorg on Startup
    [Documentation]    Verify on startup the MTE does a Full Reorg if the Persist File does not exist.
    Stop MTE
    Delete Persist Files
    Start MTE
    Wait For FMS Reorg
    verify FMS full reorg
    [Teardown]

Partial REORG on Startup
    [Documentation]    Verify Partial REORG behaviour of MTE http://www.iajira.amers.ime.reuters.com/browse/CATF-1755
    Wait For Persist File Update
    Stop MTE
    Start MTE
    verify FMS partial reorg
    [Teardown]

Verify MTE behavior when FMS Connectivity is not available
    [Documentation]    Verify MTE behavior when FMS Connectivity is not available
    ...
    ...    http://jirag.int.thomsonreuters.com/browse/CATF-2198
    ${serviceName}=    Get FMS Service Name
    ${feedEXLFiles}    ${modifiedFeedEXLFiles}    Force Persist File Write    ${serviceName}
    ${dstdumpfile_before}=    set variable    ${LOCAL_TMP_DIR}/cachedump_before.csv
    Get Sorted Cache Dump    ${dstdumpfile_before}
    block dataflow by port protocol    INPUT    ${PROTOCOL}    ${FMSCMD_PORT}
    Stop SMF
    Start SMF
    ${dstdumpfile_after}=    set variable    ${LOCAL_TMP_DIR}/cachedump_after.csv
    Get Sorted Cache Dump    ${dstdumpfile_after}
    ${removeFMSREORGTIMESTAMP}    Create Dictionary    .*CHE%FMSREORGTIMESTAMP.*=${EMPTY}
    Modify Lines Matching Pattern    ${dstdumpfile_before}    ${dstdumpfile_before}    ${removeFMSREORGTIMESTAMP}    ${False}
    Modify Lines Matching Pattern    ${dstdumpfile_after}    ${dstdumpfile_after}    ${removeFMSREORGTIMESTAMP}    ${False}
    verify csv files match    ${dstdumpfile_before}    ${dstdumpfile_after}    ignorefids=ITEM_ID,CURR_SEQ_NUM,TIME_CREATED,LAST_ACTIVITY,LAST_UPDATED,THREAD_ID,ITEM_FAMILY
    [Teardown]    Run Keywords    Unblock Dataflow    case teardown    ${dstdumpfile_before}    ${dstdumpfile_after}

*** Keywords ***
verify FMS full reorg
    statBlock should be equal    ${MTE}    FMS    lastReorgType    2    lastReorgType should be 2 (Full Reorg)

verify FMS partial reorg
    wait for StatBlock    ${MTE}    FMS    lastReorgType    1
