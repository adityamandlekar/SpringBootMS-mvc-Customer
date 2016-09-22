*** Settings ***
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         VenueVariables.py

*** Test Cases ***
Verify CritProcMon Message Logging
    [Documentation]    Verify CritProcMon generates trap and clear messages when a process goes down, and goes up after the configured process uptime elapses.
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2311
    ...
    ...    Test Steps:
    ...    1. Read the CritProcMon config for getting the dictionary of monitored process names and their uptime value.
    ...    2. In the dictionary of process names with configured uptime value, add an item of MTE process with 20 sec uptime
    ...    (Note: MTE is not specified in CritProcMon config, please refer to https://thehub.thomsonreuters.com/message/521585)
    ...    2. Loop for the list of monitored process names
    ...    2.1. Get the current Timestamp A
    ...    2.2. Kill the monitored process
    ...    2.3. Wait for SMF Log Message started from Timestamp A and with timeout of [configured process uptime] + 10 sec
    ...    a) "[process name] is no longer running"
    ...    b) "[process name] has been back up for [configured process uptime] seconds or more"
    ...    - Verify the above 2 messages are published within the timeout period
    ...    - Verify the timestamp on the message (b) is >= Timestamp A + configured process uptime.
    @{critProcConfigInfoList}=    Get Critical Process Config Info
    @{mteInfo}=    Create List    MTE    0    20
    Append To List    ${critProcConfigInfoList}    ${mteInfo}
    : FOR    ${critProcConfigInfo}    IN    @{critProcConfigInfoList}
    \    ${configMonProcess}=    set variable    ${critProcConfigInfo[0]}
    \    ${configMonProcessLowerCase}=    Convert To Lowercase    ${critProcConfigInfo[0]}
    \    ${configMonProcessLowerCase}=    set variable if    '${configMonProcess}' == 'MTE'    mte -c ${MTE}    ${configMonProcessLowerCase}
    \    ${configProcUpTime}=    Convert To Integer    ${critProcConfigInfo[2]}
    \    ${waitLogTimeout}=    Evaluate    ${configProcUpTime} + 10
    \    ${currDateTime}=    Get Date and Time
    \    ${expectedBackUpTime}=    Get Current Date    increment=${configProcUpTime}    exclude_millis=True
    \    @{retCode}=    Kill Processes    ${configMonProcess}
    \    Should be True    ${retCode[0]} == 0    Fail to find the process ${configMonProcess} to kill
    \    ${logStopRuningTime}=    Wait SMF Log Message After Time    ${configMonProcessLowerCase} \+is no longer running    ${currDateTime}    2    ${waitLogTimeout}
    \    ${logBackUpTime}=    Wait SMF Log Message After Time    ${configMonProcessLowerCase} \+has been back up for ${configProcUpTime} seconds or more    ${currDateTime}    2    ${waitLogTimeout}
    \    ${timeDiff}=    Subtract Date From Date    ${logBackUpTime}    ${expectedBackUpTime}
    \    Should Be True    ${timeDiff} >= 0    CritProcMon should NOT generate a clear message prior to the configured process uptime
    \    Sleep    10    Sleep for 10 seconds before killing next process
    [Teardown]    Restart SMF    # Restart SMF as a workaround for the defect of fail to read Stat Blocks fields after StatBlockManager process is killed.

*** Keywords ***
Restart SMF
    Stop SMF
    Start SMF
