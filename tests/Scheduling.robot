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
    Run DST test
    Sort List    ${processedDstRics}
    Lists Should Be Equal    ${dstRicList}    ${processedDstRics}
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
    Run Holiday test
    Sort List    ${processedHolidayRics}
    Lists Should Be Equal    ${holidayRicList}    ${processedHolidayRics}
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

*** Keywords ***
Check input port stats
    [Arguments]    ${identifierName}    ${statIdentifier}    ${statField}    ${statValue}
    [Documentation]    Note that all input port stats blocks (that have ${identifierName} set to ${statIdentifier}) will be checked here.
    : FOR    ${index}    IN RANGE    0    255
    \    ${identifier}    get stat block field    ${mte}    InputPortStatsBlock_${index}    ${identifierName}
    \    run keyword if    '${identifier}' == '${statIdentifier}'    wait for statBlock    ${mte}    InputPortStatsBlock_${index}    ${statField}
    \    ...    ${statValue}    waittime=2    timeout=300

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
    [Documentation]    For start datetime, uses: ${year}-${month}-${day}T${hour}:${min}:${sec}.${ms}
    ...
    ...    For end datetime, adds a day from given: ${year}, ${month}, ${day}, ${hour}, ${min}, ${sec}
    ${startDatetime}    set variable    ${year}-${month}-${day}T${hour}:${min}:${sec}.${ms}
    ${endDatetimeYear}    ${endDatetimeMonth}    ${endDatetimeDay}    ${endDatetimeHour}    ${endDatetimeMin}    ${endDatetimeSec}    add seconds to date
    ...    ${year}    ${month}    ${day}    ${hour}    ${min}    ${sec}
    ...    86400
    ${endDatetime}    set variable    ${endDatetimeYear}-${endDatetimeMonth}-${endDatetimeDay}T${endDatetimeHour}:${endDatetimeMin}:${endDatetimeSec}.00
    [Return]    ${startDatetime}    ${endDatetime}

Set datetimes for holiday IN state
    [Arguments]    ${year}    ${month}    ${day}    ${hour}    ${min}    ${sec}
    ...    ${ms}=00
    [Documentation]    For start datetime, subtracts 3 days from given: ${year}-${month}-${day}T${hour}:${min}:${sec}.${ms}
    ...
    ...    For end datetime, adds 3 days from given: ${year}, ${month}, ${day}, ${hour}, ${min}, ${sec}
    ...
    ...    Note that the above is needed to cover max possible GMT offset cases.
    ${startDatetimeYear}    ${startDatetimeMonth}    ${startDatetimeDay}    ${startDatetimeHour}    ${startDatetimeMin}    ${startDatetimeSec}    add seconds to date
    ...    ${year}    ${month}    ${day}    ${hour}    ${min}    ${sec}
    ...    -259200
    ${startDatetime}    set variable    ${startDatetimeYear}-${startDatetimeMonth}-${startDatetimeDay}T${startDatetimeHour}:${startDatetimeMin}:${startDatetimeSec}.${ms}
    ${endDatetimeYear}    ${endDatetimeMonth}    ${endDatetimeDay}    ${endDatetimeHour}    ${endDatetimeMin}    ${endDatetimeSec}    add seconds to date
    ...    ${year}    ${month}    ${day}    ${hour}    ${min}    ${sec}
    ...    259200
    ${endDatetime}    set variable    ${endDatetimeYear}-${endDatetimeMonth}-${endDatetimeDay}T${endDatetimeHour}:${endDatetimeMin}:${endDatetimeSec}.00
    [Return]    ${startDatetime}    ${endDatetime}

Set datetimes for OUT state
    [Arguments]    ${year}    ${month}    ${day}    ${hour}    ${min}    ${sec}
    ...    ${ms}=00
    [Documentation]    For start datetime, subtracts a day from given: ${year}, ${month}, ${day}, ${hour}, ${min}, ${sec}
    ...
    ...    For end datetime, uses: ${year}-${month}-${day}T${hour}:${min}:${sec}.${ms}
    ${startDatetimeYear}    ${startDatetimeMonth}    ${startDatetimeDay}    ${startDatetimeHour}    ${startDatetimeMin}    ${startDatetimeSec}    add seconds to date
    ...    ${year}    ${month}    ${day}    ${hour}    ${min}    ${sec}
    ...    -86400
    ${startDatetime}    set variable    ${startDatetimeYear}-${startDatetimeMonth}-${startDatetimeDay}T${startDatetimeHour}:${startDatetimeMin}:${startDatetimeSec}.00
    ${endDatetime}    set variable    ${year}-${month}-${day}T${hour}:${min}:${sec}.${ms}
    [Return]    ${startDatetime}    ${endDatetime}

Set datetimes for holiday OUT state
    [Arguments]    ${year}    ${month}    ${day}    ${hour}    ${min}    ${sec}
    ...    ${ms}=00
    [Documentation]    For start datetime, adds 3 days from given: ${year}-${month}-${day}T${hour}:${min}:${sec}.${ms}
    ...
    ...    For end datetime, adds 4 days from given: ${year}, ${month}, ${day}, ${hour}, ${min}, ${sec}
    ...
    ...    Note that the above is needed to cover max possible GMT offset cases.
    ${startDatetimeYear}    ${startDatetimeMonth}    ${startDatetimeDay}    ${startDatetimeHour}    ${startDatetimeMin}    ${startDatetimeSec}    add seconds to date
    ...    ${year}    ${month}    ${day}    ${hour}    ${min}    ${sec}
    ...    259200
    ${startDatetime}    set variable    ${startDatetimeYear}-${startDatetimeMonth}-${startDatetimeDay}T${startDatetimeHour}:${startDatetimeMin}:${startDatetimeSec}.${ms}
    ${endDatetimeYear}    ${endDatetimeMonth}    ${endDatetimeDay}    ${endDatetimeHour}    ${endDatetimeMin}    ${endDatetimeSec}    add seconds to date
    ...    ${year}    ${month}    ${day}    ${hour}    ${min}    ${sec}
    ...    345600
    ${endDatetime}    set variable    ${endDatetimeYear}-${endDatetimeMonth}-${endDatetimeDay}T${endDatetimeHour}:${endDatetimeMin}:${endDatetimeSec}.00
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

Run DST test
    : FOR    ${dstExlFile}    IN    @{dstExlFiles}
    \    Append to list    ${processedDstExlFiles}    ${dstExlFile}
    \    ${dstRicName}    ${dstDomain}    get ric and domain from EXL    ${dstExlFile}
    \    Append to list    ${processedDstRics}    ${dstRicName}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    ${normalGMTOffsetInitialStatValue}    get stat block field    ${mte}    ${dstRicName}    normalGMTOffset
    \    Set Test Variable    ${normalGMTOffsetInitialStatValue}
    \    ${dstGMTOffsetInitialStatValue}    get stat block field    ${mte}    ${dstRicName}    dstGMTOffset
    \    Set Test Variable    ${dstGMTOffsetInitialStatValue}
    \    @{foundMatches}    get matches workaround    ${dstRicList}    ${dstRicName}
    \    ${foundMatchesLength}    get length    ${foundMatches}
    \    run keyword if    '${foundMatchesLength}' == '1'    Go into DST and check stats    ${dstExlFile}    ${dstRicName}    ${dstDomain}
    \    ...    ${localVenueDateTime}
    \    run keyword if    '${foundMatchesLength}' == '1'    Go outside DST and check stats    ${dstExlFile}    ${dstRicName}    ${dstDomain}
    \    ...    ${localVenueDateTime}
    \    run keyword if    '${foundMatchesLength}' == '1'    Go into DST and check stats    ${dstExlFile}    ${dstRicName}    ${dstDomain}
    \    ...    ${localVenueDateTime}

Calculate DST start date and check stat
    [Arguments]    ${dstRicName}    ${startYear}    ${startMonth}    ${startDay}    ${startHour}    ${startMin}
    ...    ${startSec}
    ${applyNormalGmtOffset}    Evaluate    0 - int(${normalGMTOffsetInitialStatValue})
    ${startYear}    ${startMonth}    ${startDay}    ${startHour}    ${startMin}    ${startSec}    add seconds to date
    ...    ${startYear}    ${startMonth}    ${startDay}    ${startHour}    ${startMin}    ${startSec}
    ...    ${applyNormalGmtOffset}
    ${expectedStartDatetime}    set variable    ${startYear}-${startMonth}-${startDay}T${startHour}:${startMin}:${startSec}.00
    ${expectedStartDatetime}    convert EXL datetime to statblock format    ${expectedStartDatetime}
    wait for statBlock    ${mte}    ${dstRicName}    ${dstStartDateStatField}    ${expectedStartDatetime}    waittime=2    timeout=120
    [Return]    ${expectedStartDatetime}

Calculate DST end date and check stat
    [Arguments]    ${dstRicName}    ${endYear}    ${endMonth}    ${endDay}    ${endHour}    ${endMin}
    ...    ${endSec}
    ${applyDstGmtOffset}    Evaluate    0 - int(${dstGMTOffsetInitialStatValue})
    ${endYear}    ${endMonth}    ${endDay}    ${endHour}    ${endMin}    ${endSec}    add seconds to date
    ...    ${endYear}    ${endMonth}    ${endDay}    ${endHour}    ${endMin}    ${endSec}
    ...    ${applyDstGmtOffset}
    ${expectedEndDatetime}    set variable    ${endYear}-${endMonth}-${endDay}T${endHour}:${endMin}:${endSec}.00
    ${expectedEndDatetime}    convert EXL datetime to statblock format    ${expectedEndDatetime}
    wait for statBlock    ${mte}    ${dstRicName}    ${dstEndDateStatField}    ${expectedEndDatetime}    waittime=2    timeout=120
    [Return]    ${expectedEndDatetime}

Go into DST and check stats
    [Arguments]    ${dstExlFile}    ${dstRicName}    ${domainName}    ${localVenueDateTime}
    [Documentation]    Sets the box so it goes into DST and verifies ${dstStartDateField} and ${dstEndDateField} are set appropriately.
    ${dstExlFileModified} =    set variable    ${dstExlFile}_modified.exl
    ${dstStartDatetime}    ${dstEndDatetime}    Set datetimes for IN state    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}    ${localVenueDateTime[3]}
    ...    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    Set DST Datetime In EXL    ${dstExlFile}    ${dstExlFileModified}    ${dstRicName}    ${domainName}    ${dstStartDatetime}    ${dstEndDatetime}
    Load Single EXL File    ${dstExlFileModified}    ${serviceName}    ${CHE_IP}
    ${expectedStartDatetime}    Calculate DST start date and check stat    ${dstRicName}    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}    ${localVenueDateTime[3]}
    ...    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    ${endYear}    ${endMonth}    ${endDay}    ${endHour}    ${endMin}    ${endSec}    add seconds to date
    ...    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}    ${localVenueDateTime[3]}    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    ...    86400
    ${expectedEndDatetime}    Calculate DST end date and check stat    ${dstRicName}    ${endYear}    ${endMonth}    ${endDay}    ${endHour}
    ...    ${endMin}    ${endSec}
    ${expectedDstGMTOffset}    get stat block field    ${mte}    ${dstRicName}    dstGMTOffset
    wait for statBlock    ${mte}    ${dstRicName}    currentGMTOffset    ${expectedDstGMTOffset}    waittime=2    timeout=120

Go outside DST and check stats
    [Arguments]    ${dstExlFile}    ${dstRicName}    ${domainName}    ${localVenueDateTime}
    [Documentation]    Sets the box so it goes outside of DST and verifies ${dstStartDateField} and ${dstEndDateField} are set appropriately.
    ${dstExlFileModified} =    set variable    ${dstExlFile}_modified.exl
    ${dstStartDatetime}    ${dstEndDatetime}    Set datetimes for OUT state    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}    ${localVenueDateTime[3]}
    ...    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    Set DST Datetime In EXL    ${dstExlFile}    ${dstExlFileModified}    ${dstRicName}    ${domainName}    ${dstStartDatetime}    ${dstEndDatetime}
    Load Single EXL File    ${dstExlFileModified}    ${serviceName}    ${CHE_IP}
    ${startYear}    ${startMonth}    ${startDay}    ${startHour}    ${startMin}    ${startSec}    add seconds to date
    ...    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}    ${localVenueDateTime[3]}    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    ...    -86400
    ${expectedStartDatetime}    Calculate DST start date and check stat    ${dstRicName}    ${startYear}    ${startMonth}    ${startDay}    ${startHour}
    ...    ${startMin}    ${startSec}
    ${expectedEndDatetime}    Calculate DST end date and check stat    ${dstRicName}    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}    ${localVenueDateTime[3]}
    ...    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    ${expectedNormalGMTOffset}    get stat block field    ${mte}    ${dstRicName}    normalGMTOffset
    wait for statBlock    ${mte}    ${dstRicName}    currentGMTOffset    ${expectedNormalGMTOffset}    waittime=2    timeout=120

Run Feed Time test
    : FOR    ${feedTimeRicName}    IN    @{feedTimeRicList}
    \    Append to list    ${processedFeedTimeRics}    ${feedTimeRicName}
    \    ${feedTimeExlFile}    get EXL from RIC and domain    ${feedTimeRicName}    ${domain}    ${LOCAL_FMS_DIR}    Feed Time
    \    Append to list    ${processedFeedTimeExlFiles}    ${feedTimeExlFile}
    \    ${dstRicName}    ${holidayRicName}    get DST and holiday RICs from EXL    ${feedTimeExlFile}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    Go into feed time and check stat    ${feedTimeExlFile}    ${feedTimeRicName}    ${domain}    ${localVenueDateTime}
    \    Go outside feed time and check stat    ${feedTimeExlFile}    ${feedTimeRicName}    ${domain}    ${localVenueDateTime}
    \    Go into feed time and check stat    ${feedTimeExlFile}    ${feedTimeRicName}    ${domain}    ${localVenueDateTime}

Go into feed time and check stat
    [Arguments]    ${feedTimeExlFile}    ${feedTimeRicName}    ${feedTimeDomainName}    ${localVenueDateTime}
    [Documentation]    Sets the box so it goes into feed time and verifies ${feedTimeStatField} is set to 1.
    ${weekDay}    get day of week from date    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}
    ${feedTimeExlFileModified} =    set variable    ${feedTimeExlFile}_modified.exl
    ${feedTimeStartTime}    ${feedTimeEndTime}    Set times for IN state    ${localVenueDateTime[3]}    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    Set Feed Time In EXL    ${feedTimeExlFile}    ${feedTimeExlFileModified}    ${feedTimeRicName}    ${feedTimeDomainName}    ${feedTimeStartTime}    ${feedTimeEndTime}
    ...    ${weekDay}
    Load EXL and check stat    ${feedTimeExlFileModified}    ${serviceName}    ${connectTimesIdentifier}    ${feedTimeRicName}    ${feedTimeStatField}    1

Go outside feed time and check stat
    [Arguments]    ${feedTimeExlFile}    ${feedTimeRicName}    ${feedTimeDomainName}    ${localVenueDateTime}
    [Documentation]    Sets the box so it goes outside of feed time and verifies ${feedTimeStatField} is set to 0.
    ${weekDay}    get day of week from date    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}
    ${feedTimeExlFileModified} =    set variable    ${feedTimeExlFile}_modified.exl
    ${feedTimeStartTime}    ${feedTimeEndTime}    Set times for OUT state    ${localVenueDateTime[3]}    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    Set Feed Time In EXL    ${feedTimeExlFile}    ${feedTimeExlFileModified}    ${feedTimeRicName}    ${feedTimeDomainName}    ${feedTimeStartTime}    ${feedTimeEndTime}
    ...    ${weekDay}
    Load EXL and check stat    ${feedTimeExlFileModified}    ${serviceName}    ${connectTimesIdentifier}    ${feedTimeRicName}    ${feedTimeStatField}    0

Go into feed time for all feed time RICs
    [Documentation]    Sets the box so it goes into feed time for all @{feedTimeRicList} and verifies ${feedTimeStatField} is set to 1.
    : FOR    ${feedTimeRicName}    IN    @{feedTimeRicList}
    \    ${feedTimeExlFile}    get EXL from RIC and domain    ${feedTimeRicName}    ${domain}    ${LOCAL_FMS_DIR}    Feed Time
    \    Append to list    ${processedFeedTimeExlFiles}    ${feedTimeExlFile}
    \    ${dstRicName}    ${holidayRicName}    get DST and holiday RICs from EXL    ${feedTimeExlFile}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    Go into feed time and check stat    ${feedTimeExlFile}    ${feedTimeRicName}    ${domain}    ${localVenueDateTime}

Go outside feed time for all feed time RICs
    [Documentation]    Sets the box so it goes outside of feed time for all @{feedTimeRicList} and verifies ${feedTimeStatField} is set to 0.
    : FOR    ${feedTimeRicName}    IN    @{feedTimeRicList}
    \    ${feedTimeExlFile}    get EXL from RIC and domain    ${feedTimeRicName}    ${domain}    ${LOCAL_FMS_DIR}    Feed Time
    \    Append to list    ${processedFeedTimeExlFiles}    ${feedTimeExlFile}
    \    ${dstRicName}    ${holidayRicName}    get DST and holiday RICs from EXL    ${feedTimeExlFile}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    Go outside feed time and check stat    ${feedTimeExlFile}    ${feedTimeRicName}    ${domain}    ${localVenueDateTime}

Run Holiday test
    : FOR    ${holidayExlFile}    IN    @{holidayExlFiles}
    \    Append to list    ${processedHolidayExlFiles}    ${holidayExlFile}
    \    ${holidayRicName}    ${holidayDomain}    get ric and domain from EXL    ${holidayExlFile}
    \    Append to list    ${processedHolidayRics}    ${holidayRicName}
    \    @{foundMatches}    get matches workaround    ${holidayRicList}    ${holidayRicName}
    \    ${foundMatchesLength}    get length    ${foundMatches}
    \    run keyword if    '${foundMatchesLength}' == '1'    Go into holiday and check stat    ${holidayExlFile}    ${holidayRicName}    ${holidayDomain}
    \    run keyword if    '${foundMatchesLength}' == '1'    Go outside holiday and check stat    ${holidayExlFile}    ${holidayRicName}    ${holidayDomain}
    \    run keyword if    '${foundMatchesLength}' == '1'    Go into holiday and check stat    ${holidayExlFile}    ${holidayRicName}    ${holidayDomain}

Go into holiday and check stat
    [Arguments]    ${holidayExlFile}    ${holidayRicName}    ${holidayDomainName}
    [Documentation]    Sets the box so it goes into a holiday and verifies ${holidayStatField} is set to 1.
    ${holidayExlFileModified} =    set variable    ${holidayExlFile}_modified.exl
    ${holidayStartDatetime}    ${holidayEndDatetime}    Set datetimes for holiday IN state    ${currentDateTime[0]}    ${currentDateTime[1]}    ${currentDateTime[2]}    ${currentDateTime[3]}
    ...    ${currentDateTime[4]}    ${currentDateTime[5]}
    Set Holiday Datetime In EXL    ${holidayExlFile}    ${holidayExlFileModified}    ${holidayRicName}    ${holidayDomainName}    ${holidayStartDatetime}    ${holidayEndDatetime}
    Load EXL and check stat    ${holidayExlFileModified}    ${serviceName}    ${connectTimesIdentifier}    ${feedTimeRicName}    ${holidayStatField}    1

Go outside holiday and check stat
    [Arguments]    ${holidayExlFile}    ${holidayRicName}    ${holidayDomainName}
    [Documentation]    Sets the box so it goes outside of a holiday and verifies ${holidayStatField} is set to 0.
    ${holidayExlFileModified} =    set variable    ${holidayExlFile}_modified.exl
    ${holidayStartDatetime}    ${holidayEndDatetime}    Set datetimes for holiday OUT state    ${currentDateTime[0]}    ${currentDateTime[1]}    ${currentDateTime[2]}    ${currentDateTime[3]}
    ...    ${currentDateTime[4]}    ${currentDateTime[5]}
    Set Holiday Datetime In EXL    ${holidayExlFile}    ${holidayExlFileModified}    ${holidayRicName}    ${holidayDomainName}    ${holidayStartDatetime}    ${holidayEndDatetime}
    Load EXL and check stat    ${holidayExlFileModified}    ${serviceName}    ${connectTimesIdentifier}    ${feedTimeRicName}    ${holidayStatField}    0

Run Trade Time test
    : FOR    ${tradeTimeRicName}    IN    @{tradeTimeRicList}
    \    Append to list    ${processedTradeTimeRics}    ${tradeTimeRicName}
    \    ${tradeTimeExlFile}    get EXL from RIC and domain    ${tradeTimeRicName}    ${domain}    ${LOCAL_FMS_DIR}    Trade Time
    \    Append to list    ${processedTradeTimeExlFiles}    ${tradeTimeExlFile}
    \    ${dstRicName}    ${holidayRicName}    get DST and holiday RICs from EXL    ${tradeTimeExlFile}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    Go into trade time and check stat    ${tradeTimeExlFile}    ${tradeTimeRicName}    ${domain}    ${localVenueDateTime}
    \    Go outside trade time and check stat    ${tradeTimeExlFile}    ${tradeTimeRicName}    ${domain}    ${localVenueDateTime}
    \    Go into trade time and check stat    ${tradeTimeExlFile}    ${tradeTimeRicName}    ${domain}    ${localVenueDateTime}

Go into trade time and check stat
    [Arguments]    ${tradeTimeExlFile}    ${tradeTimeRicName}    ${tradeTimeDomainName}    ${localVenueDateTime}
    [Documentation]    Sets the box so it goes into trade time and verifies ${tradeTimeStatField} is set to 1.
    ${weekDay}    get day of week from date    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}
    ${tradeTimeExlFileModified} =    set variable    ${tradeTimeExlFile}_modified.exl
    ${tradeTimeStartTime}    ${tradeTimeEndTime}    Set times for IN state    ${localVenueDateTime[3]}    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    Set Trade Time In EXL    ${tradeTimeExlFile}    ${tradeTimeExlFileModified}    ${tradeTimeRicName}    ${tradeTimeDomainName}    ${tradeTimeStartTime}    ${tradeTimeEndTime}
    ...    ${weekDay}
    Load EXL and check stat    ${tradeTimeExlFileModified}    ${serviceName}    ${highactTimesIdentifier}    ${tradeTimeRicName}    ${tradeTimeStatField}    1

Go outside trade time and check stat
    [Arguments]    ${tradeTimeExlFile}    ${tradeTimeRicName}    ${tradeTimeDomainName}    ${localVenueDateTime}
    [Documentation]    Sets the box so it goes outside of trade time and verifies ${tradeTimeStatField} is set to 0.
    ${weekDay}    get day of week from date    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}
    ${tradeTimeExlFileModified} =    set variable    ${tradeTimeExlFile}_modified.exl
    ${tradeTimeStartTime}    ${tradeTimeEndTime}    Set times for OUT state    ${localVenueDateTime[3]}    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}
    Set Trade Time In EXL    ${tradeTimeExlFile}    ${tradeTimeExlFileModified}    ${tradeTimeRicName}    ${tradeTimeDomainName}    ${tradeTimeStartTime}    ${tradeTimeEndTime}
    ...    ${weekDay}
    Load EXL and check stat    ${tradeTimeExlFileModified}    ${serviceName}    ${highactTimesIdentifier}    ${tradeTimeRicName}    ${tradeTimeStatField}    0

Go into trade time for all trade time RICs
    [Documentation]    Sets the box so it goes into trade time for all @{tradeTimeRicList} and verifies ${tradeTimeStatField} is set to 1.
    : FOR    ${tradeTimeRicName}    IN    @{tradeTimeRicList}
    \    Append to list    ${processedTradeTimeRics}    ${tradeTimeRicName}
    \    ${tradeTimeExlFile}    get EXL from RIC and domain    ${tradeTimeRicName}    ${domain}    ${LOCAL_FMS_DIR}    Trade Time
    \    Append to list    ${processedTradeTimeExlFiles}    ${tradeTimeExlFile}
    \    ${dstRicName}    ${holidayRicName}    get DST and holiday RICs from EXL    ${tradeTimeExlFile}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    Go into trade time and check stat    ${tradeTimeExlFile}    ${tradeTimeRicName}    ${domain}    ${localVenueDateTime}

Verify trade time stats updated
    [Arguments]    ${expectedTradeTimeStatValue}
    [Documentation]    Verifies ${tradeTimeStatField} is set to ${expectedTradeTimeStatValue}.
    : FOR    ${tradeTimeRicName}    IN    @{tradeTimeRicList}
    \    Check input port stats    ${highactTimesIdentifier}    ${tradeTimeRicName}    ${tradeTimeStatField}    ${expectedTradeTimeStatValue}

Scheduling Suite Setup
    suite setup
    ${serviceName}    Get FMS Service Name    ${mte}
    Set Suite Variable    ${serviceName}

DST Initialize Variables
    ${dstStartDateStatField} =    set variable    dstStartDate
    Set Suite Variable    ${dstStartDateStatField}
    ${dstEndDateStatField} =    set variable    dstEndDate
    Set Suite Variable    ${dstEndDateStatField}
    @{dstExlFiles}    Get EXL files    ${LOCAL_FMS_DIR}    DST
    Set Suite Variable    @{dstExlFiles}
    @{processedDstExlFiles} =    create list
    Set Suite Variable    @{processedDstExlFiles}
    @{processedDstRics} =    create list
    Set Suite Variable    @{processedDstRics}
    @{dstRicList}    Get RIC List From StatBlock    ${mte}    DST
    Sort List    ${dstRicList}
    Set Suite Variable    @{dstRicList}

DST Setup
    [Documentation]    Setup for DST test. Gets initial DST datetimes from statblock to make sure it reverts after test is complete.
    DST Initialize Variables

DST Teardown
    [Documentation]    Reverts orginal EXL and verifies DST start and end datetime stats also get reverted to original state.
    : FOR    ${dstExlFile}    IN    @{processedDstExlFiles}
    \    Load Single EXL File    ${dstExlFile}    ${serviceName}    ${CHE_IP}

Feed Time Initialize Variables
    ${connectTimesIdentifier} =    set variable    connectTimesIdentifier
    Set Suite Variable    ${connectTimesIdentifier}
    ${feedTimeStatField} =    set variable    shouldBeOpen
    Set Suite Variable    ${feedTimeStatField}
    @{processedFeedTimeExlFiles} =    create list
    Set Suite Variable    @{processedFeedTimeExlFiles}
    @{processedFeedTimeRics} =    create list
    Set Suite Variable    @{processedFeedTimeRics}
    @{feedTimeRicList}    Get RIC List From StatBlock    ${mte}    Feed Time
    Sort List    ${feedTimeRicList}
    Set Suite Variable    @{feedTimeRicList}

Feed Time Setup
    [Documentation]    Setup for Feed Time test. Puts box in non-holiday mode to ensure feed times can happen. Gets initial feed and holiday stats from statblock to make sure they revert after test is complete.
    ${currentDateTime}    get date and time
    Set Suite Variable    ${currentDateTime}
    ${mteConfigFile}=    set variable    ${LOCAL_TMP_DIR}/venue_config.xml
    Get MTE Config File    ${VENUE_DIR}    ${mte}.xml    ${mteConfigFile}
    ${feedTimeRicName}    Get ConnectTimesIdentifier    ${mteConfigFile}
    Set Suite Variable    ${feedTimeRicName}
    ${domain}    Get Preferred Domain    ${mteConfigFile}    MARKET_PRICE
    Set Suite Variable    ${domain}
    Feed Time Initialize Variables
    Holiday Initialize Variables
    : FOR    ${holidayExlFile}    IN    @{holidayExlFiles}
    \    Append to list    ${processedHolidayExlFiles}    ${holidayExlFile}
    \    ${holidayRicName}    ${holidayDomain}    get ric and domain from EXL    ${holidayExlFile}
    \    Go outside holiday and check stat    ${holidayExlFile}    ${holidayRicName}    ${holidayDomain}

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
    @{holidayExlFiles}    Get EXL files    ${LOCAL_FMS_DIR}    Holiday
    Set Suite Variable    @{holidayExlFiles}
    @{processedHolidayExlFiles} =    create list
    Set Suite Variable    @{processedHolidayExlFiles}
    @{processedHolidayRics} =    create list
    Set Suite Variable    @{processedHolidayRics}
    @{holidayRicList}    Get RIC List From StatBlock    ${mte}    Holiday
    Sort List    ${holidayRicList}
    Set Suite Variable    @{holidayRicList}

Holiday Setup
    [Documentation]    Setup for Holiday test. Gets initial holiday and feed stats from statblock to make sure they revert after test is complete.
    ${currentDateTime}    get date and time
    Set Suite Variable    ${currentDateTime}
    ${mteConfigFile}=    set variable    ${LOCAL_TMP_DIR}/venue_config.xml
    Get MTE Config File    ${VENUE_DIR}    ${MTE}.xml    ${mteConfigFile}
    ${feedTimeRicName}    Get ConnectTimesIdentifier    ${mteConfigFile}
    Set Suite Variable    ${feedTimeRicName}
    ${connectTimesIdentifier} =    set variable    connectTimesIdentifier
    Set Suite Variable    ${connectTimesIdentifier}
    Holiday Initialize Variables

Holiday Cleanup
    [Documentation]    Reverts orginal EXL and verifies holiday and feed stats also get reverted to original state.
    : FOR    ${holidayExlFile}    IN    @{processedHolidayExlFiles}
    \    Load Single EXL File    ${holidayExlFile}    ${serviceName}    ${CHE_IP}

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
    @{tradeTimeRicList}    Get RIC List From StatBlock    ${mte}    Trade Time
    Sort List    ${tradeTimeRicList}
    Set Suite Variable    @{tradeTimeRicList}

Trade Time Setup
    [Documentation]    Setup for Trade Time test. Puts box in non-holiday mode and during feed time to ensure trade times can happen. Gets initial stats from statblock to make sure they revert after test is complete.
    ${currentDateTime}    get date and time
    Set Suite Variable    ${currentDateTime}
    ${mteConfigFile}=    set variable    ${LOCAL_TMP_DIR}/venue_config.xml
    Get MTE Config File    ${VENUE_DIR}    ${MTE}.xml    ${mteConfigFile}
    ${feedTimeRicName}    Get ConnectTimesIdentifier    ${mteConfigFile}
    Set Suite Variable    ${feedTimeRicName}
    ${domain}    Get Preferred Domain    ${mteConfigFile}    MARKET_PRICE
    Set Suite Variable    ${domain}
    Feed Time Initialize Variables
    : FOR    ${feedTimeRicName}    IN    @{feedTimeRicList}
    \    ${feedTimeExlFile}    get EXL from RIC and domain    ${feedTimeRicName}    ${domain}    ${LOCAL_FMS_DIR}    Feed Time
    \    Append to list    ${processedFeedTimeExlFiles}    ${feedTimeExlFile}
    \    ${dstRicName}    ${holidayRicName}    get DST and holiday RICs from EXL    ${feedTimeExlFile}
    \    ${currentDateTime}    ${localVenueDateTime}    Get venue local datetime from MTE    ${dstRicName}
    \    Go into feed time and check stat    ${feedTimeExlFile}    ${feedTimeRicName}    ${domain}    ${localVenueDateTime}
    Holiday Initialize Variables
    : FOR    ${holidayExlFile}    IN    @{holidayExlFiles}
    \    Append to list    ${processedHolidayExlFiles}    ${holidayExlFile}
    \    ${holidayRicName}    ${holidayDomain}    get ric and domain from EXL    ${holidayExlFile}
    \    Go outside holiday and check stat    ${holidayExlFile}    ${holidayRicName}    ${holidayDomain}
    ${tradeTimeRicName}    Get HighActivityTimesIdentifier    ${mteConfigFile}
    Set Suite Variable    ${tradeTimeRicName}
    Trade Time Initialize Variables

Trade Time Cleanup
    [Documentation]    Reverts orginal EXLs and verifies stats also gets reverted to original state.
    : FOR    ${tradeTimeExlFile}    IN    @{processedTradeTimeExlFiles}
    \    Load Single EXL File    ${tradeTimeExlFile}    ${serviceName}    ${CHE_IP}

Trade Time Teardown
    [Documentation]    Reverts orginal EXLs and verifies stats also gets reverted to original state.
    Trade Time Cleanup
    Holiday Cleanup
    Feed Time Cleanup
