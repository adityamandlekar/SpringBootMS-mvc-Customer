*** Settings ***
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         VenueVariables.py

*** Test Cases ***
Verify Frame Packing is Enabled
    [Documentation]    Verify the setting of frame packing is enabled, by check the "FlushBufferThreshold" value in MTE config file > 1 ("FlushBufferThreshold" <=1 means no packing and "FlushBufferThreshold" > 1 means packing)
    ...
    ...    Test Steps:
    ...    1. Check the "FlushBufferThreshold" value in MTE config file, e.g.
    ...    \ \<FlushBufferThreshold type="ul">1316</FlushBufferThreshold>
    ...    2. Fail if the FlushBufferThreshold <= 1 (means no frame packing)
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2143
    [Setup]
    ${mteConfigFile}=    Get MTE Config File
    @{flushBufferList}=    get MTE config list by section    ${mteConfigFile}    Publishing    FlushBufferThreshold
    Should Not Be Empty    ${flushBufferList}    "FlushBufferThreshold" must be defined in Publishing section of FTE/MTE config file with value greater than 1
    : FOR    ${flushBuffer}    IN    @{flushBufferList}
    \    ${flushBufferNum}=    Convert to Integer    ${flushBuffer}
    \    Should Be True    ${flushBufferNum} > 1    "FlushBufferThreshold" value in FTE/MTE config file must be greater than 1

Verify Cache Contains Only Configured Context IDs
    [Documentation]    Verify that all context ids in the MTE cache are listed in <Transforms> section \ in the MTE configuration file.
    Stop MTE
    Delete Persist Files
    Start MTE
    Wait For FMS Reorg
    ${dstdumpfile}=    set variable    ${LOCAL_TMP_DIR}/cachedump.csv
    Get Sorted Cache Dump    ${dstdumpfile}
    ${mteConfigFile}=    Get MTE Config File
    verify cache contains only configured context ids    ${dstdumpfile}    ${mteConfigFile}
    [Teardown]    case teardown    ${dstdumpfile}

Verify FilterString Contains Configured IDs
    [Documentation]    Verify that all context ids listed in the <Transforms> section should be present in FilterString
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2113
    ${mteConfigFile}=    Get MTE Config File
    ${serviceName}=    Get FMS Service Name
    ${fmsFilterString}=    Get MTE Config Value    ${mteConfigFile}    FMS    ${serviceName}    FilterString
    Verify FilterString Contains Configured Context IDs    ${fmsFilterString}    ${mteConfigFile}

Verify FilterString FID usage
    [Documentation]    Verify that FilterString does not contain following FIDs:
    ...    1. BOND_TYPE
    ...    2. LIST_MKT
    ...    3. MKT_SEGMENT
    ...    4. MIC_CODE
    ...    5. ISSUTYPE
    ...    6. ISS
    ...    7. SPG_20CHR_1
    ...    8. SPG_WORD
    ...    9. GV4_TEXT
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2114
    @{unexpectedFIDs}=    Create List    BOND_TYPE    LIST_MKT    MKT_SEGMENT    MIC_CODE    ISSUTYPE
    ...    ISS    SPG_20CHR_1    SPG_WORD    GV4_TEXT
    ${mteConfigFile}=    Get MTE Config File
    ${serviceName}=    Get FMS Service Name
    ${fmsFilterString}=    Get MTE Config Value    ${mteConfigFile}    FMS    ${serviceName}    FilterString
    ${withoutPunctuation}=    Replace String Using Regexp    ${fmsFilterString}    \\W+    ${SPACE}
    ${filterAsList}=    Split String    ${withoutPunctuation}
    : FOR    ${fid}    IN    @{unexpectedFIDs}
    \    Should Not Contain    ${filterAsList}    ${fid}

Verify all Context IDs are in FIDFilter
    [Documentation]    Verify all context IDs in cache exist in FIDFilter.txt
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2629
    ${fidFile}    Get FIDFilter File
    ${dstdumpfile}=    set variable    ${LOCAL_TMP_DIR}/cachedump.csv
    Get Sorted Cache Dump    ${dstdumpfile}
    ${cacheContextIDs}    get context ids from cachedump    ${dstdumpfile}
    ${FIDFiltercontextIDs}    Get ContextID From FidFilter
    List Should Contain Sub List    ${FIDFiltercontextIDs}    ${cacheContextIDs}
    [Teardown]    case teardown    ${dstdumpfile}

Verify SHELL_MDAT FID for SHELL RIC
    [Documentation]    For each Context ID that has a SHELL RIC, verify the SHELL_MDAT FID exists in FIDFilter for constituent 0
	...
	...	http://www.iajira.amers.ime.reuters.com/browse/CATF-2240
    ${shellCount}    Get Count Of SHELL RICs
    ${localfidFilter}=    Get FIDFilter File
    Verify Fidfilter Contains SHELL MDAT    ${shellCount}