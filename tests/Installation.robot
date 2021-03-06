*** Settings ***
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         VenueVariables.py

*** Test Cases ***
Verify duplicate processes are not created
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1964
    ...
    ...    Verify that each CHE process exists already. Start the process again by using commander and check no changes in PID
    @{process_pattern_list}=    Create List    [FM]TE -c ${MTE}    CritProcMon    DudtGen    EventScheduler    FMSClient
    ...    GapStatGen    LatencyHandler    NetConStat    SCWatchdog    StatBlockManager    StatRicGen
    ...    StatsGen
    @{process_list}=    Create List    ${MTE}    CritProcMon    DudtGen    EventScheduler    FMSClient
    ...    GapStatGen    LatencyHandler    NetConStat    SCWatchdog    StatBlockManager    StatRicGen
    ...    StatsGen
    ${pid_dict1}    Get process and pid matching pattern    @{process_pattern_list}
    ${list_length} =    Get Length    ${process_pattern_list}
    ${dict_length} =    Get Length    ${pid_dict1}
    Should Be Equal    ${list_length}    ${dict_length}    Pattern in [${pid_dict1}] does not match pattern in [${process_pattern_list}]
    : FOR    ${process_item}    IN    @{process_list}
    \    run commander    process    start ${process_item}
    \    wait for process to exist    ${process_item}
    ${pid_dict2}    Get process and pid matching pattern    @{process_pattern_list}
    Dictionaries Should Be Equal    ${pid_dict1}    ${pid_dict2}    Expected processes [${pid_dict1}], found processes [${pid_dict2}]
