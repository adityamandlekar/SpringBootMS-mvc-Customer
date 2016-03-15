*** Settings ***
Documentation     Verify scheduling of events by modifying EXL files and processing them.
...
...               Note that test cases will transition to IN, OUT, and IN states to cover all state cases without worrying about its current state.
Suite Setup       Scheduling Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
Verify Daylight Savings Time processing
    [Documentation]    Verify Daylight Savings Time processing:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1643
    [Tags]    CATF-1643
    [Setup]    DST Setup
    Go into DST and check stats    ${feedDstEXL}    ${feedDstRic}    ${domain}    ${currentDateTime}
    Go outside DST and check stats    ${feedDstEXL}    ${feedDstRic}    ${domain}    ${currentDateTime}
    Go into DST and check stats    ${feedDstEXL}    ${feedDstRic}    ${domain}    ${currentDateTime}
    Go into DST and check stats    ${tradeDstEXL}    ${tradeDstRic}    ${domain}    ${currentDateTime}
    Go outside DST and check stats    ${tradeDstEXL}    ${tradeDstRic}    ${domain}    ${currentDateTime}
    Go into DST and check stats    ${tradeDstEXL}    ${tradeDstRic}    ${domain}    ${currentDateTime}
    [Teardown]    DST Teardown

Verify Feed Time processing
    [Documentation]    Verify Feed Time processing:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1644
    [Tags]    CATF-1644
    [Setup]    Feed Time Setup
    Run Feed Time test
    Sort List    ${processedFeedTimeRics}
    Lists Should Be Equal    ${feedTimeRicList}    ${processedFeedTimeRics}
    [Teardown]    Feed Time Teardown

Verify Holiday RIC processing
    [Documentation]    Verify Holiday RIC processing:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1640
    [Tags]    CATF-1640
    [Setup]    Holiday Setup
    Go into holiday and check stat    ${feedHolidayEXL}    ${feedHolidayRic}    ${domain}    ${currentDateTime}
    Go outside holiday and check stat    ${feedHolidayEXL}    ${feedHolidayRic}    ${domain}    ${currentDateTime}
    Go into holiday and check stat    ${feedHolidayEXL}    ${feedHolidayRic}    ${domain}    ${currentDateTime}
    Go into holiday and check stat    ${tradeHolidayEXL}    ${tradeHolidayRic}    ${domain}    ${currentDateTime}
    Go outside holiday and check stat    ${tradeHolidayEXL}    ${tradeHolidayRic}    ${domain}    ${currentDateTime}
    Go into holiday and check stat    ${tradeHolidayEXL}    ${tradeHolidayRic}    ${domain}    ${currentDateTime}
    [Teardown]    Holiday Teardown

Verify Trade Time processing
    [Documentation]    Verify Trade Time processing:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1644
    [Tags]    CATF-1644
    [Setup]    Trade Time Setup
    Run Trade Time test
    Sort List    ${processedTradeTimeRics}
    Lists Should Be Equal    ${tradeTimeRicList}    ${processedTradeTimeRics}
    [Teardown]    Trade Time Teardown

Test inHighActivity gets updated when box goes out of feed time
    [Documentation]    Test inHighActivity gets updated when box goes out of and into feed time:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1749
    [Tags]    CATF-1749
    [Setup]    Trade Time Setup
    Go outside feed time for all feed time RICs
    Verify trade time stats updated    0
    Go into feed time for all feed time RICs
    Verify trade time stats updated    1
    Sort List    ${processedTradeTimeRics}
    Lists Should Be Equal    ${tradeTimeRicList}    ${processedTradeTimeRics}
    [Teardown]    Trade Time Teardown

Verify Re-schedule Closing Run through modifying EXL
    [Documentation]    In EXL file for Closing Run, if the time is changed, the Closing Run will be triggered at new time
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1846
    [Setup]    Initialize for Closing Run
    @{processedClosingrunRicName}    Go Into Closing Run Time For All Closing Run RICs    @{closingrunRicList}
    Sort List    ${processedClosingrunRicName}
    Lists Should Be Equal    @{processedClosingrunRicName}    @{closingrunRicList}
    [Teardown]    Re-schedule Closing Run teardown

Verify Manual Closing Runs
    [Documentation]    Test Case - Verify Manual Closing Runs
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1886
    ...
    ...    The test case is used to verify the manual closing run, including doing a Closing Run for a specific RIC, a Closing Run for a specific Exl file and a Closing Run for a specific Closing Run RIC
    ${sampleRic}    ${publishKey}    Get RIC From MTE Cache
    ${domain}    Get Preferred Domain
    Manual ClosingRun for a RIC    ${sampleRic}    ${publishKey}    ${domain}
    Manual ClosingRun for the EXL File including target Ric    ${sampleRic}    ${publishKey}    ${domain}
    ${serviceName}    Get FMS Service Name
    Manual ClosingRun for ClosingRun Rics    ${serviceName}

*** Keywords ***
Check input port stats
    [Arguments]    ${identifierName}    ${statIdentifier}    ${statField}    ${statValue}
    [Documentation]    Note that all input port stats blocks (that have ${identifierName} set to ${statIdentifier}) will be checked here.
    ...    Will stop checking when an empty stats block is encountered.
    : FOR    ${index}    IN RANGE    0    255
    \    ${identifier}    get stat block field    ${MTE}    InputPortStatsBlock_${index}    ${identifierName}
    \    run keyword if    '${identifier}' == '${statIdentifier}'    wait for statBlock    ${MTE}    InputPortStatsBlock_${index}    ${statField}
    \    ...    ${statValue}    waittime=2    timeout=300
    \    return from keyword if    '${identifier}' == ''

Get venue local datetime from MTE
    [Arguments]    ${ricName}
    ${currentDateTime}    get date and time
    ${localVenueDateTime}    Get GMT Offset And Apply To Datetime    ${ricName}    ${currentDateTime[0]}    ${currentDateTime[1]}    ${currentDateTime[2]}    ${currentDateTime[3]}
    ...    ${currentDateTime[4]}    ${currentDateTime[5]}
    [Return]    ${currentDateTime}    ${localVenueDateTime}

Load EXL and check stat
    [Arguments]    ${exlFile}    ${service}    ${identifierName}    ${statIdentifier}    ${statField}    ${statValue}
    [Documentation]    Note that all input port stats blocks (that have ${identifierName} set to ${statIdentifier}) will be checked here.
    Load Single EXL File    ${exlFile}    ${service}    ${CHE_IP}
    Check input port stats    ${identifierName}    ${statIdentifier}    ${statField}    ${statValue}

Set datetimes for IN state
    [Arguments]    ${year}    ${month}    ${day}    ${hour}    ${min}    ${sec}
    ...    ${ms}=00
    [Documentation]    For start datetime, subtracts 3 days from given: ${year}-${month}-${day}T${hour}:${min}:${sec}.${ms}
    ...
    ...    For end datetime, adds 3 days from given: ${year}, ${month}, ${day}, ${hour}, ${min}, ${sec}
    ...
    ...    Note that the above is needed to cover max possible GMT offset cases.
    ${startDateTime}    subtract time from date    ${year}-${month}-${day} ${hour}:${min}:${sec}    3 day    exclude_millis=yes
    ${endDateTime}    add time to date    ${year}-${month}-${day} ${hour}:${min}:${sec}    3 day    exclude_millis=yes
    [Return]    ${startDatetime}    ${endDatetime}

Set datetimes for OUT state
    [Arguments]    ${year}    ${month}    ${day}    ${hour}    ${min}    ${sec}
    ...    ${ms}=00
    [Documentation]    For start datetime, adds 3 days from given: ${year}-${month}-${day}T${hour}:${min}:${sec}.${ms}
    ...
    ...    For end datetime, adds 4 days from given: ${year}, ${month}, ${day}, ${hour}, ${min}, ${sec}
    ...
    ...    Note that the above is needed to cover max possible GMT offset cases.
    ${startDateTime}    add time to date    ${year}-${month}-${day} ${hour}:${min}:${sec}    3 day    exclude_millis=yes
    ${endDateTime}    add time to date    ${year}-${month}-${day} ${hour}:${min}:${sec}    4 day    exclude_millis=yes
    [Return]    ${startDatetime}    ${endDatetime}

Set times for IN state
    [Arguments]    ${hour}    ${min}    ${sec}
    [Documentation]    For start time, uses values passed in.
    ...
    ...    For end time, sets it to 23:59:59.
    ${startTime}    set variable    ${hour}:${min}:${sec}
    ${endTime}    set variable    23:59:59
    [Return]    ${startTime}    ${endTime}

Set times for OUT state
    [Arguments]    ${hour}    ${min}    ${sec}
    [Documentation]    For start time, sets it to 00:00:00.
    ...
    ...    For end time, uses values passed in.
    ${startTime}    set variable    00:00:00
    ${endTime}    set variable    ${hour}:${min}:${sec}
    [Return]    ${startTime}    ${endTime}

Calculate DST start date and check stat
    [Arguments]    ${dstRicName}    ${dstStartDatetime}
    ${normalGMTOffset}    get stat block field    ${MTE}    ${dstRicName}    normalGMTOffset
    ${startDatetime}    subtract time from date    ${dstStartDatetime}    ${normalGMTOffset} second    result_format=%Y-%m-%dT%H:%M:%S.0
    ${expectedStartDatetime}    convert EXL datetime to statblock format    ${startDatetime}
    wait for statBlock    ${MTE}    ${dstRicName}    ${dstStartDateStatField}    ${expectedStartDatetime}    waittime=2    timeout=120

Calculate DST end date and check stat
    [Arguments]    ${dstRicName}    ${dstEndDatetime}
    ${dstGMTOffset}    get stat block field    ${MTE}    ${dstRicName}    dstGMTOffset
    ${endDatetime}    subtract time from date    ${dstEndDatetime}    ${dstGMTOffset} second    result_format=%Y-%m-%dT%H:%M:%S.0
    ${expectedEndDatetime}    convert EXL datetime to statblock format    ${endDatetime}
    wait for statBlock    ${MTE}    ${dstRicName}    ${dstEndDateStatField}    ${expectedEndDatetime}    waittime=2    timeout=120

Go into DST and check stats
    [Arguments]    ${dstExlFile}    ${dstRicName}    ${domainName}    ${gmtDateTime}
    [Documentation]    Sets the box so it goes into DST and verifies ${dstStartDateField} and ${dstEndDateField} are set appropriately.
    ${feedDstEXLFile}    Fetch From Right    ${dstExlFile}    \\
    ${dstExlFileModified} =    set variable    ${LOCAL_TMP_DIR}/${feedDstEXLFile}_modified.exl
    ${dstStartDatetime}    ${dstEndDatetime}    Set datetimes for IN state    ${gmtDateTime[0]}    ${gmtDateTime[1]}    ${gmtDateTime[2]}    ${gmtDateTime[3]}
    ...    ${gmtDateTime[4]}    ${gmtDateTime[5]}
    ${startDatetime}    convert date    ${dstStartDatetime}    result_format=%Y-%m-%dT%H:%M:%S.0
    ${endDatetime}    convert date    ${dstEndDatetime}    result_format=%Y-%m-%dT%H:%M:%S.0
    Set DST Datetime In EXL    ${dstExlFile}    ${dstExlFileModified}    ${dstRicName}    ${domainName}    ${startDatetime}    ${endDatetime}
    Load Single EXL File    ${dstExlFileModified}    ${serviceName}    ${CHE_IP}
    remove files    ${dstExlFileModified}
    Calculate DST start date and check stat    ${dstRicName}    ${dstStartDatetime}
    Calculate DST end date and check stat    ${dstRicName}    ${dstEndDatetime}
    ${expectedDstGMTOffset}    get stat block field    ${MTE}    ${dstRicName}    dstGMTOffset
    wait for statBlock    ${MTE}    ${dstRicName}    currentGMTOffset    ${expectedDstGMTOffset}    waittime=2    timeout=120

Go outside DST and check stats
    [Arguments]    ${dstExlFile}    ${dstRicName}    ${domainName}    ${gmtDateTime}
    [Documentation]    Sets the box so it goes outside of DST and verifies ${dstStartDateField} and ${dstEndDateField} are set appropriately.
    ${feedDstEXLFile}    Fetch From Right    ${dstExlFile}    \\
    ${dstExlFileModified} =    set variable    ${LOCAL_TMP_DIR}/${feedDstEXLFile}_modified.exl
    ${dstStartDatetime}    ${dstEndDatetime}    Set datetimes for OUT state    ${gmtDateTime[0]}    ${gmtDateTime[1]}    ${gmtDateTime[2]}    ${gmtDateTime[3]}
    ...    ${gmtDateTime[4]}    ${gmtDateTime[5]}
    ${startDatetime}    convert date    ${dstStartDatetime}    result_format=%Y-%m-%dT%H:%M:%S.0
    ${endDatetime}    convert date    ${dstEndDatetime}    result_format=%Y-%m-%dT%H:%M:%S.0
    Set DST Datetime In EXL    ${dstExlFile}    ${dstExlFileModified}    ${dstRicName}    ${domainName}    ${startDatetime}    ${endDatetime}
    Load Single EXL File    ${dstExlFileModified}    ${serviceName}    ${CHE_IP}
    remove files    ${dstExlFileModified}
    Calculate DST start date and check stat    ${dstRicName}    ${dstStartDatetime}
    Calculate DST end date and check stat    ${dstRicName}    ${dstEndDatetime}
    ${expectedDstGMTOffset}    get stat block field    ${MTE}    ${dstRicName}    normalGMTOffset
    wait for statBlock    ${MTE}    ${dstRicName}    currentGMTOffset    ${expectedDstGMTOffset}    waittime=2    timeout=120

Run Feed Time test
    : FOR    ${feedTimeRicName}    IN    @{feedTimeRicList}
    \    Append to list    ${processedFeedTimeRics}    ${feedTimeRicName}
    \    ${feedTimeExlFile}    get state EXL file    ${feedTimeRicName}    ${domain}    ${serviceName}    Feed Time
    \    Append to list    ${processedFeedTimeExlFiles}    ${feedTimeExlFile}
    \    ${dstRicName}    ${holidayRicName}    get DST and holiday RICs from EXL    ${feedTimeExlFile}    ${feedTimeRicName}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    Go into feed time and check stat    ${feedTimeExlFile}    ${feedTimeRicName}    ${domain}    ${localVenueDateTime}
    \    Go outside feed time and check stat    ${feedTimeExlFile}    ${feedTimeRicName}    ${domain}    ${localVenueDateTime}
    \    Go into feed time and check stat    ${feedTimeExlFile}    ${feedTimeRicName}    ${domain}    ${localVenueDateTime}

Go into feed time and check stat
    [Arguments]    ${feedTimeExlFile}    ${feedTimeRicName}    ${feedTimeDomainName}    ${localVenueDateTime}
    [Documentation]    Sets the box so it goes into feed time and verifies ${feedTimeStatField} is set to 1.
    ${weekDay}    get day of week from date    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}
    ${feedTimeExlFileOnly}    Fetch From Right    ${feedTimeExlFile}    \\
    ${feedTimeExlFileModified} =    set variable    ${LOCAL_TMP_DIR}/${feedTimeExlFileOnly}_modified.exl
    ${feedTimeStartTime}    ${feedTimeEndTime}    Set times for IN state    ${localVenueDateTime[3]}    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    Set Feed Time In EXL    ${feedTimeExlFile}    ${feedTimeExlFileModified}    ${feedTimeRicName}    ${feedTimeDomainName}    ${feedTimeStartTime}    ${feedTimeEndTime}
    ...    ${weekDay}
    Load EXL and check stat    ${feedTimeExlFileModified}    ${serviceName}    ${connectTimesIdentifier}    ${feedTimeRicName}    ${feedTimeStatField}    1
    remove files    ${feedTimeExlFileModified}

Go outside feed time and check stat
    [Arguments]    ${feedTimeExlFile}    ${feedTimeRicName}    ${feedTimeDomainName}    ${localVenueDateTime}
    [Documentation]    Sets the box so it goes outside of feed time and verifies ${feedTimeStatField} is set to 0.
    ${weekDay}    get day of week from date    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}
    ${feedTimeExlFileOnly}    Fetch From Right    ${feedTimeExlFile}    \\
    ${feedTimeExlFileModified} =    set variable    ${LOCAL_TMP_DIR}/${feedTimeExlFileOnly}_modified.exl
    ${feedTimeStartTime}    ${feedTimeEndTime}    Set times for OUT state    ${localVenueDateTime[3]}    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    Set Feed Time In EXL    ${feedTimeExlFile}    ${feedTimeExlFileModified}    ${feedTimeRicName}    ${feedTimeDomainName}    ${feedTimeStartTime}    ${feedTimeEndTime}
    ...    ${weekDay}
    Load EXL and check stat    ${feedTimeExlFileModified}    ${serviceName}    ${connectTimesIdentifier}    ${feedTimeRicName}    ${feedTimeStatField}    0
    remove files    ${feedTimeExlFileModified}

Go into feed time for all feed time RICs
    [Documentation]    Sets the box so it goes into feed time for all @{feedTimeRicList} and verifies ${feedTimeStatField} is set to 1.
    : FOR    ${feedTimeRicName}    IN    @{feedTimeRicList}
    \    ${feedTimeExlFile}    get state EXL file    ${feedTimeRicName}    ${domain}    ${serviceName}    Feed Time
    \    Append to list    ${processedFeedTimeExlFiles}    ${feedTimeExlFile}
    \    ${dstRicName}    ${holidayRicName}    get DST and holiday RICs from EXL    ${feedTimeExlFile}    ${feedTimeRicName}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    Go into feed time and check stat    ${feedTimeExlFile}    ${feedTimeRicName}    ${domain}    ${localVenueDateTime}

Go outside feed time for all feed time RICs
    [Documentation]    Sets the box so it goes outside of feed time for all @{feedTimeRicList} and verifies ${feedTimeStatField} is set to 0.
    : FOR    ${feedTimeRicName}    IN    @{feedTimeRicList}
    \    ${feedTimeExlFile}    get state EXL file    ${feedTimeRicName}    ${domain}    ${serviceName}    Feed Time
    \    Append to list    ${processedFeedTimeExlFiles}    ${feedTimeExlFile}
    \    ${dstRicName}    ${holidayRicName}    get DST and holiday RICs from EXL    ${feedTimeExlFile}    ${feedTimeRicName}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    Go outside feed time and check stat    ${feedTimeExlFile}    ${feedTimeRicName}    ${domain}    ${localVenueDateTime}

Go into holiday and check stat
    [Arguments]    ${holidayExlFile}    ${holidayRicName}    ${holidayDomainName}    ${gmtDateTime}
    [Documentation]    Sets the box so it goes into a holiday and verifies ${holidayStatField} is set to 1.
    ${holidayExlFileOnly}    Fetch From Right    ${holidayExlFile}    \\
    ${holidayExlFileModified} =    set variable    ${LOCAL_TMP_DIR}/${holidayExlFileOnly}_modified.exl
    ${holidayStartDatetime}    ${holidayEndDatetime}    Set datetimes for IN state    ${gmtDateTime[0]}    ${gmtDateTime[1]}    ${gmtDateTime[2]}    ${gmtDateTime[3]}
    ...    ${gmtDateTime[4]}    ${gmtDateTime[5]}
    ${startDatetime}    set variable    ${holidayStartDatetime[0]}-${holidayStartDatetime[1]}-${holidayStartDatetime[2]}T${holidayStartDatetime[3]}:${holidayStartDatetime[4]}:${holidayStartDatetime[5]}.0
    ${endDatetime}    set variable    ${holidayEndDatetime[0]}-${holidayEndDatetime[1]}-${holidayEndDatetime[2]}T${holidayEndDatetime[3]}:${holidayEndDatetime[4]}:${holidayEndDatetime[5]}.0
    Set Holiday Datetime In EXL    ${holidayExlFile}    ${holidayExlFileModified}    ${holidayRicName}    ${holidayDomainName}    ${startDatetime}    ${endDatetime}
    Load EXL and check stat    ${holidayExlFileModified}    ${serviceName}    ${connectTimesIdentifier}    ${feedTimeRicName}    ${holidayStatField}    1
    remove files    ${holidayExlFileModified}

Go outside holiday and check stat
    [Arguments]    ${holidayExlFile}    ${holidayRicName}    ${holidayDomainName}    ${gmtDateTime}
    [Documentation]    Sets the box so it goes outside of a holiday and verifies ${holidayStatField} is set to 0.
    ${holidayExlFileOnly}    Fetch From Right    ${holidayExlFile}    \\
    ${holidayExlFileModified} =    set variable    ${LOCAL_TMP_DIR}/${holidayExlFileOnly}_modified.exl
    ${holidayStartDatetime}    ${holidayEndDatetime}    Set datetimes for OUT state    ${gmtDateTime[0]}    ${gmtDateTime[1]}    ${gmtDateTime[2]}    ${gmtDateTime[3]}
    ...    ${gmtDateTime[4]}    ${gmtDateTime[5]}
    ${startDatetime}    set variable    ${holidayStartDatetime[0]}-${holidayStartDatetime[1]}-${holidayStartDatetime[2]}T${holidayStartDatetime[3]}:${holidayStartDatetime[4]}:${holidayStartDatetime[5]}.0
    ${endDatetime}    set variable    ${holidayEndDatetime[0]}-${holidayEndDatetime[1]}-${holidayEndDatetime[2]}T${holidayEndDatetime[3]}:${holidayEndDatetime[4]}:${holidayEndDatetime[5]}.0
    Set Holiday Datetime In EXL    ${holidayExlFile}    ${holidayExlFileModified}    ${holidayRicName}    ${holidayDomainName}    ${startDatetime}    ${endDatetime}
    Load EXL and check stat    ${holidayExlFileModified}    ${serviceName}    ${connectTimesIdentifier}    ${feedTimeRicName}    ${holidayStatField}    0
    remove files    ${holidayExlFileModified}

Run Trade Time test
    : FOR    ${tradeTimeRicName}    IN    @{tradeTimeRicList}
    \    Append to list    ${processedTradeTimeRics}    ${tradeTimeRicName}
    \    ${tradeTimeExlFile}    get state EXL file    ${tradeTimeRicName}    ${domain}    ${serviceName}    Trade Time
    \    Append to list    ${processedTradeTimeExlFiles}    ${tradeTimeExlFile}
    \    ${dstRicName}    ${holidayRicName}    get DST and holiday RICs from EXL    ${tradeTimeExlFile}    ${tradeTimeRicName}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    Go into trade time and check stat    ${tradeTimeExlFile}    ${tradeTimeRicName}    ${domain}    ${localVenueDateTime}
    \    Go outside trade time and check stat    ${tradeTimeExlFile}    ${tradeTimeRicName}    ${domain}    ${localVenueDateTime}
    \    Go into trade time and check stat    ${tradeTimeExlFile}    ${tradeTimeRicName}    ${domain}    ${localVenueDateTime}

Go into trade time and check stat
    [Arguments]    ${tradeTimeExlFile}    ${tradeTimeRicName}    ${tradeTimeDomainName}    ${localVenueDateTime}
    [Documentation]    Sets the box so it goes into trade time and verifies ${tradeTimeStatField} is set to 1.
    ${weekDay}    get day of week from date    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}
    ${tradeTimeExlFileOnly}    Fetch From Right    ${tradeTimeExlFile}    \\
    ${tradeTimeExlFileModified} =    set variable    ${LOCAL_TMP_DIR}/${tradeTimeExlFileOnly}_modified.exl
    ${tradeTimeStartTime}    ${tradeTimeEndTime}    Set times for IN state    ${localVenueDateTime[3]}    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    Set Trade Time In EXL    ${tradeTimeExlFile}    ${tradeTimeExlFileModified}    ${tradeTimeRicName}    ${tradeTimeDomainName}    ${tradeTimeStartTime}    ${tradeTimeEndTime}
    ...    ${weekDay}
    Load EXL and check stat    ${tradeTimeExlFileModified}    ${serviceName}    ${highactTimesIdentifier}    ${tradeTimeRicName}    ${tradeTimeStatField}    1
    remove files    ${tradeTimeExlFileModified}

Go outside trade time and check stat
    [Arguments]    ${tradeTimeExlFile}    ${tradeTimeRicName}    ${tradeTimeDomainName}    ${localVenueDateTime}
    [Documentation]    Sets the box so it goes outside of trade time and verifies ${tradeTimeStatField} is set to 0.
    ${weekDay}    get day of week from date    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}
    ${tradeTimeExlFileOnly}    Fetch From Right    ${tradeTimeExlFile}    \\
    ${tradeTimeExlFileModified} =    set variable    ${LOCAL_TMP_DIR}/${tradeTimeExlFileOnly}_modified.exl
    ${tradeTimeStartTime}    ${tradeTimeEndTime}    Set times for OUT state    ${localVenueDateTime[3]}    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    Set Trade Time In EXL    ${tradeTimeExlFile}    ${tradeTimeExlFileModified}    ${tradeTimeRicName}    ${tradeTimeDomainName}    ${tradeTimeStartTime}    ${tradeTimeEndTime}
    ...    ${weekDay}
    Load EXL and check stat    ${tradeTimeExlFileModified}    ${serviceName}    ${highactTimesIdentifier}    ${tradeTimeRicName}    ${tradeTimeStatField}    0
    remove files    ${tradeTimeExlFileModified}

Go into trade time for all trade time RICs
    [Documentation]    Sets the box so it goes into trade time for all @{tradeTimeRicList} and verifies ${tradeTimeStatField} is set to 1.
    : FOR    ${tradeTimeRicName}    IN    @{tradeTimeRicList}
    \    Append to list    ${processedTradeTimeRics}    ${tradeTimeRicName}
    \    ${tradeTimeExlFile}    get state EXL file    ${tradeTimeRicName}    ${domain}    ${serviceName}    Trade Time
    \    Append to list    ${processedTradeTimeExlFiles}    ${tradeTimeExlFile}
    \    ${dstRicName}    ${holidayRicName}    get DST and holiday RICs from EXL    ${tradeTimeExlFile}    ${tradeTimeRicName}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    Go into trade time and check stat    ${tradeTimeExlFile}    ${tradeTimeRicName}    ${domain}    ${localVenueDateTime}

Verify trade time stats updated
    [Arguments]    ${expectedTradeTimeStatValue}
    [Documentation]    Verifies ${tradeTimeStatField} is set to ${expectedTradeTimeStatValue}.
    : FOR    ${tradeTimeRicName}    IN    @{tradeTimeRicList}
    \    Check input port stats    ${highactTimesIdentifier}    ${tradeTimeRicName}    ${tradeTimeStatField}    ${expectedTradeTimeStatValue}

Scheduling Suite Setup
    suite setup
    ${serviceName}    Get FMS Service Name
    Set Suite Variable    ${serviceName}

DST Initialize Variables
    ${dstStartDateStatField} =    set variable    dstStartDate
    Set Suite Variable    ${dstStartDateStatField}
    ${dstEndDateStatField} =    set variable    dstEndDate
    Set Suite Variable    ${dstEndDateStatField}

DST Setup
    [Documentation]    Setup for DST test. Gets initial DST datetimes from statblock to make sure it reverts after test is complete.
    DST Initialize Variables
    ${currentDateTime}    get date and time
    Set Suite Variable    ${currentDateTime}
    ${mteConfigFile}=    Get MTE Config File
    ${feedTimeRicName}    Get ConnectTimesIdentifier    ${mteConfigFile}
    Set Suite Variable    ${feedTimeRicName}
    ${tradeTimeRicName}    Get HighActivityTimesIdentifier    ${mteConfigFile}
    Set Suite Variable    ${tradeTimeRicName}
    ${domain}    Get Preferred Domain    MARKET_PRICE
    Set Suite Variable    ${domain}
    ${feedTimeEXL}    get state EXL file    ${feedTimeRicName}    ${domain}    ${serviceName}    Feed Time
    ${tradeTimeEXL}    get state EXL file    ${tradeTimeRicName}    ${domain}    ${serviceName}    Trade Time
    ${feedDstRic}    ${feedHolidayRic}    Get DST And Holiday RICs From EXL    ${feedTimeEXL}    ${feedTimeRicName}
    Set Suite Variable    ${feedDstRic}
    ${tradeDstRic}    ${tradeHolidayRic}    Get DST And Holiday RICs From EXL    ${tradeTimeEXL}    ${tradeTimeRicName}
    Set Suite Variable    ${tradeDstRic}
    ${feedDstEXL}    get state EXL file    ${feedDstRic}    ${domain}    ${serviceName}    DST
    Set Suite Variable    ${feedDstEXL}
    ${tradeDstEXL}    get state EXL file    ${tradeDstRic}    ${domain}    ${serviceName}    DST
    Set Suite Variable    ${tradeDstEXL}

DST Teardown
    [Documentation]    Reverts orginal EXL and verifies DST start and end datetime stats also get reverted to original state.
    Load Single EXL File    ${feedDstEXL}    ${serviceName}    ${CHE_IP}
    Load Single EXL File    ${tradeDstEXL}    ${serviceName}    ${CHE_IP}

Feed Time Initialize Variables
    ${connectTimesIdentifier} =    set variable    connectTimesIdentifier
    Set Suite Variable    ${connectTimesIdentifier}
    ${feedTimeStatField} =    set variable    shouldBeOpen
    Set Suite Variable    ${feedTimeStatField}
    @{processedFeedTimeExlFiles} =    create list
    Set Suite Variable    @{processedFeedTimeExlFiles}
    @{processedFeedTimeRics} =    create list
    Set Suite Variable    @{processedFeedTimeRics}
    @{feedTimeRicList}    Get RIC List From StatBlock    Feed Time
    Sort List    ${feedTimeRicList}
    Set Suite Variable    @{feedTimeRicList}

Feed Time Setup
    [Documentation]    Setup for Feed Time test. Puts box in non-holiday mode to ensure feed times can happen. Gets initial feed and holiday stats from statblock to make sure they revert after test is complete.
    Feed Time Initialize Variables
    Holiday Initialize Variables
    ${currentDateTime}    get date and time
    Set Suite Variable    ${currentDateTime}
    ${mteConfigFile}=    Get MTE Config File
    ${feedTimeRicName}    Get ConnectTimesIdentifier    ${mteConfigFile}
    Set Suite Variable    ${feedTimeRicName}
    ${tradeTimeRicName}    Get HighActivityTimesIdentifier    ${mteConfigFile}
    Set Suite Variable    ${tradeTimeRicName}
    ${domain}    Get Preferred Domain    MARKET_PRICE
    Set Suite Variable    ${domain}
    ${feedTimeEXL}    get state EXL file    ${feedTimeRicName}    ${domain}    ${serviceName}    Feed Time
    ${tradeTimeEXL}    get state EXL file    ${tradeTimeRicName}    ${domain}    ${serviceName}    Trade Time
    ${feedDstRic}    ${feedHolidayRic}    Get DST And Holiday RICs From EXL    ${feedTimeEXL}    ${feedTimeRicName}
    Set Suite Variable    ${feedHolidayRic}
    ${tradeDstRic}    ${tradeHolidayRic}    Get DST And Holiday RICs From EXL    ${tradeTimeEXL}    ${tradeTimeRicName}
    Set Suite Variable    ${tradeHolidayRic}
    ${feedHolidayEXL}    get state EXL file    ${feedHolidayRic}    ${domain}    ${serviceName}    Holiday
    Set Suite Variable    ${feedHolidayEXL}
    ${tradeHolidayEXL}    get state EXL file    ${tradeHolidayRic}    ${domain}    ${serviceName}    Holiday
    Set Suite Variable    ${tradeHolidayEXL}
    Go outside holiday and check stat    ${feedHolidayEXL}    ${feedHolidayRic}    ${domain}    ${currentDateTime}
    Go outside holiday and check stat    ${tradeHolidayEXL}    ${tradeHolidayRic}    ${domain}    ${currentDateTime}

Feed Time Cleanup
    [Documentation]    Reverts orginal EXL and verifies feed and holiday stats also get reverted to original state.
    : FOR    ${feedTimeExlFile}    IN    @{processedFeedTimeExlFiles}
    \    Load Single EXL File    ${feedTimeExlFile}    ${serviceName}    ${CHE_IP}

Feed Time Teardown
    [Documentation]    Reverts orginal EXL and verifies feed and holiday stats also get reverted to original state.
    Feed Time Cleanup
    Holiday Cleanup

Holiday Initialize Variables
    ${holidayStatField} =    set variable    holidayStatus
    Set Suite Variable    ${holidayStatField}
    ${connectTimesIdentifier} =    set variable    connectTimesIdentifier
    Set Suite Variable    ${connectTimesIdentifier}

Holiday Setup
    [Documentation]    Setup for Holiday test. Gets initial holiday and feed stats from statblock to make sure they revert after test is complete.
    Holiday Initialize Variables
    ${currentDateTime}    get date and time
    Set Suite Variable    ${currentDateTime}
    ${mteConfigFile}=    Get MTE Config File
    ${feedTimeRicName}    Get ConnectTimesIdentifier    ${mteConfigFile}
    Set Suite Variable    ${feedTimeRicName}
    ${tradeTimeRicName}    Get HighActivityTimesIdentifier    ${mteConfigFile}
    Set Suite Variable    ${tradeTimeRicName}
    ${domain}    Get Preferred Domain    MARKET_PRICE
    Set Suite Variable    ${domain}
    ${feedTimeEXL}    get state EXL file    ${feedTimeRicName}    ${domain}    ${serviceName}    Feed Time
    ${tradeTimeEXL}    get state EXL file    ${tradeTimeRicName}    ${domain}    ${serviceName}    Trade Time
    ${feedDstRic}    ${feedHolidayRic}    Get DST And Holiday RICs From EXL    ${feedTimeEXL}    ${feedTimeRicName}
    Set Suite Variable    ${feedHolidayRic}
    ${tradeDstRic}    ${tradeHolidayRic}    Get DST And Holiday RICs From EXL    ${tradeTimeEXL}    ${tradeTimeRicName}
    Set Suite Variable    ${tradeHolidayRic}
    ${feedHolidayEXL}    get state EXL file    ${feedHolidayRic}    ${domain}    ${serviceName}    Holiday
    Set Suite Variable    ${feedHolidayEXL}
    ${tradeHolidayEXL}    get state EXL file    ${tradeHolidayRic}    ${domain}    ${serviceName}    Holiday
    Set Suite Variable    ${tradeHolidayEXL}

Holiday Cleanup
    [Documentation]    Reverts orginal EXL and verifies holiday and feed stats also get reverted to original state.
    Load Single EXL File    ${feedHolidayEXL}    ${serviceName}    ${CHE_IP}
    Load Single EXL File    ${tradeHolidayEXL}    ${serviceName}    ${CHE_IP}

Holiday Teardown
    [Documentation]    Reverts orginal EXL and verifies holiday and feed stats also get reverted to original state.
    Holiday Cleanup

Trade Time Initialize Variables
    ${highactTimesIdentifier} =    set variable    highactTimesIdentifier
    Set Suite Variable    ${highactTimesIdentifier}
    ${tradeTimeStatField} =    set variable    inHighActivity
    Set Suite Variable    ${tradeTimeStatField}
    @{processedTradeTimeExlFiles} =    create list
    Set Suite Variable    @{processedTradeTimeExlFiles}
    @{processedTradeTimeRics} =    create list
    Set Suite Variable    @{processedTradeTimeRics}
    @{tradeTimeRicList}    Get RIC List From StatBlock    Trade Time
    Sort List    ${tradeTimeRicList}
    Set Suite Variable    @{tradeTimeRicList}

Trade Time Setup
    [Documentation]    Setup for Trade Time test. Puts box in non-holiday mode and during feed time to ensure trade times can happen. Gets initial stats from statblock to make sure they revert after test is complete.
    Feed Time Initialize Variables
    Trade Time Initialize Variables
    Holiday Initialize Variables
    ${currentDateTime}    get date and time
    Set Suite Variable    ${currentDateTime}
    ${mteConfigFile}=    Get MTE Config File
    ${feedTimeRicName}    Get ConnectTimesIdentifier    ${mteConfigFile}
    Set Suite Variable    ${feedTimeRicName}
    ${tradeTimeRicName}    Get HighActivityTimesIdentifier    ${mteConfigFile}
    Set Suite Variable    ${tradeTimeRicName}
    ${domain}    Get Preferred Domain    MARKET_PRICE
    Set Suite Variable    ${domain}
    ${feedTimeEXL}    get state EXL file    ${feedTimeRicName}    ${domain}    ${serviceName}    Feed Time
    ${tradeTimeEXL}    get state EXL file    ${tradeTimeRicName}    ${domain}    ${serviceName}    Trade Time
    ${feedDstRic}    ${feedHolidayRic}    Get DST And Holiday RICs From EXL    ${feedTimeEXL}    ${feedTimeRicName}
    Set Suite Variable    ${feedHolidayRic}
    ${tradeDstRic}    ${tradeHolidayRic}    Get DST And Holiday RICs From EXL    ${tradeTimeEXL}    ${tradeTimeRicName}
    Set Suite Variable    ${tradeHolidayRic}
    ${feedHolidayEXL}    get state EXL file    ${feedHolidayRic}    ${domain}    ${serviceName}    Holiday
    Set Suite Variable    ${feedHolidayEXL}
    ${tradeHolidayEXL}    get state EXL file    ${tradeHolidayRic}    ${domain}    ${serviceName}    Holiday
    Set Suite Variable    ${tradeHolidayEXL}
    Go outside holiday and check stat    ${feedHolidayEXL}    ${feedHolidayRic}    ${domain}    ${currentDateTime}
    Go outside holiday and check stat    ${tradeHolidayEXL}    ${tradeHolidayRic}    ${domain}    ${currentDateTime}
    : FOR    ${feedTimeRicName}    IN    @{feedTimeRicList}
    \    ${feedTimeExlFile}    get state EXL file    ${feedTimeRicName}    ${domain}    ${serviceName}    Feed Time
    \    Append to list    ${processedFeedTimeExlFiles}    ${feedTimeExlFile}
    \    ${dstRicName}    ${holidayRicName}    get DST and holiday RICs from EXL    ${feedTimeExlFile}    ${feedTimeRicName}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    Go into feed time and check stat    ${feedTimeExlFile}    ${feedTimeRicName}    ${domain}    ${localVenueDateTime}

Trade Time Cleanup
    [Documentation]    Reverts orginal EXLs and verifies stats also gets reverted to original state.
    : FOR    ${tradeTimeExlFile}    IN    @{processedTradeTimeExlFiles}
    \    Load Single EXL File    ${tradeTimeExlFile}    ${serviceName}    ${CHE_IP}

Trade Time Teardown
    [Documentation]    Reverts orginal EXLs and verifies stats also gets reverted to original state.
    Trade Time Cleanup
    Holiday Cleanup
    Feed Time Cleanup

Go Into Closing Run Time For All Closing Run RICs
    [Arguments]    @{closingrunRicList}
    @{processedClosingrunRicName}    create list
    @{closingRunExlFiles}    create list
    set suite variable    @{closingRunExlFiles}
    : FOR    ${closingrunRicName}    IN    @{closingrunRicList}
    \    ${closingRunExlFile}    get state EXL file    ${closingrunRicName}    ${domain}    ${serviceName}    Closing Run
    \    ${dstRicName}    get ric fields from EXL    ${closingRunExlFile}    ${closingrunRicName}    DST_REF
    \    Append to list    ${processedClosingrunRicName}    ${closingrunRicName}
    \    ${dt}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName[0]}
    \    ${weekDay}    get day of week from date    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}
    \    ${closingRunTimeStartTime}    add time to date    ${localVenueDateTime[0]}-${localVenueDateTime[1]}-${localVenueDateTime[2]} ${localVenueDateTime[3]}:${localVenueDateTime[4]}:${localVenueDateTime[5]}    120 second    result_format=%H:%M:%S
    \    ${closingRunExlFileOnly}    Fetch From Right    ${closingRunExlFile}    \\
    \    ${closingRunExlfileModified}=    set variable    ${LOCAL_TMP_DIR}/${closingRunExlFileOnly}_modified.exl
    \    modify EXL    ${closingRunExlFile}    ${closingRunExlfileModified}    ${closingrunRicName}    ${domain}    <it:SCHEDULE_${weekDay}>\n<it:TIME>${closingRunTimeStartTime}</it:TIME>\n</it:SCHEDULE_${weekDay}>
    \    Append to list    @{closingRunExlFiles}    ${closingRunExlFile}
    \    Load Single EXL File    ${closingRunExlfileModified}    ${serviceName}    ${CHE_IP}
    \    remove files    ${closingRunExlfileModified}
    \    sleep    1 minutes 20 seconds
    \    wait smf log message after time    ClosingRunEventHandler for [0-9]*.*?TRIGGERING    ${dt}    5    120
    [Return]    @{processedClosingrunRicName}

Initialize for Closing Run
    @{closingrunRicList}    Get RIC List From StatBlock    Closing Run
    Sort List    ${closingrunRicList}
    set suite variable    @{closingrunRicList}
    ${mteconfigfile}    Get MTE Config File
    ${domain}    Get Preferred Domain
    set suite variable    ${domain}
    ${serviceName}    Get FMS Service Name
    set suite variable    ${serviceName}
    ${closingRunExlFile}    get state EXL file    ${closingrunRicList[0]}    ${domain}    ${serviceName}    Closing Run
    ${closingRunDstRic}    ${closingRunHolidayRic}    Get DST And Holiday RICs From EXL    ${closingRunExlFile}    ${closingrunRicList[0]}
    ${currentDateTime}    get date and time
    ${closingRunHolidayEXL}    get state EXL file    ${closingRunHolidayRic}    ${domain}    ${serviceName}    Holiday
    set suite variable    ${closingRunHolidayEXL}
    Holiday Initialize Variables
    ${feedTimeRicName}    Get ConnectTimesIdentifier    ${mteconfigfile}
    set suite variable    ${feedTimeRicName}
    Go outside holiday and check stat    ${closingRunHolidayEXL}    ${closingRunHolidayRic}    ${domain}    ${currentDateTime}

Re-schedule Closing Run teardown
    Load Single EXL File    ${closingRunHolidayEXL}    ${serviceName}    ${CHE_IP}
    : FOR    ${closingRunExlFile}    IN    @{closingRunExlFiles}
    \    Load Single EXL File    ${closingRunExlFile}    ${serviceName}    ${CHE_IP}

Manual ClosingRun for the EXL File including target Ric
    [Arguments]    ${sampleRic}    ${publishKey}    ${domain}
    ${sampleExlFile}    get_EXL_for_RIC    ${domain}    ${serviceName}    ${sampleRic}
    Start Capture MTE Output
    ${currentDateTime}    get date and time
    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd    ${CHE_IP}    Close    --Services ${serviceName}
    ...    --BypassFiltering ${True}    --SendOrphanedToAllHeadends ${True}    --ClosingRunRule 1000    --InputFile "${sampleExlFile}"
    wait SMF log message after time    Closing RIC:    ${currentDateTime}    2    60
    Stop Capture MTE Output
    ${localcapture}    set variable    ${LOCAL_TMP_DIR}/capture_local.pcap
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${localcapture}
    Run Keyword And Continue On Failure    verify ClosingRun message in messages    ${localcapture}    ${publishKey}
    remove files    ${localcapture}
    delete remote files    ${REMOTE_TMP_DIR}/capture.pcap
