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
