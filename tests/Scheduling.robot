*** Settings ***
Documentation     Verify scheduling of events by modifying EXL files and processing them.
...
...               Note that test cases will transition to IN, OUT, and IN states to cover all state cases without worrying about its current state.
Suite Setup       Scheduling Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Variables ***

*** Test Cases ***
Verify Daylight Savings Time processing
    [Documentation]    Verify Daylight Savings Time processing:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1643
    [Setup]
    Run DST Test
    [Teardown]    DST Cleanup

Verify Feed Time processing
    [Documentation]    Verify Feed Time processing:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1644
    [Setup]
    Run Feed Time Test
    [Teardown]    Feed Time Cleanup

Verify Half Day Holiday
    [Documentation]    Verify that TD can handle half day holiday properly.
    ...    1. Verify that TD goes outside holiday
    ...    2. Set holiday open time to current time and close time to 2 minutes later
    ...    3. Verify that TD is inside holiday
    ...    4. Sleep 2 minutes
    ...    5. Verify that TD goes outside holiday
    ...
    ...    http://jirag.int.thomsonreuters.com/browse/CATF-2242
    ${feedTimeRic}    Set Variable    ${feedTimeRics[0]}
    ${contents}    Set Variable    ${feedTimeRicsDict['${feedTimeRic}']}
    ${feedTimeExl}    Set Variable    ${contents[0]}
    ${feedHolidayRic}    Set Variable    ${contents[2]}
    ${contents}    Set Variable    ${feedHolidayRicsDict['${feedHolidayRic}']}
    ${feedHolidayEXL}    Set Variable    ${contents[0]}
    @{dstRic}=    Get Ric Fields from EXL    ${feedTimeExl}    ${feedTimeRic}    DST_REF
    @{tdBoxDateTime}=    Get Date and Time
    @{localDateTime}    Get GMT Offset And Apply To Datetime    @{dstRic}[0]    @{tdBoxDateTime}[0]    @{tdBoxDateTime}[1]    @{tdBoxDateTime}[2]    @{tdBoxDateTime}[3]
    ...    @{tdBoxDateTime}[4]    @{tdBoxDateTime}[5]
    ${startDateTime}=    Set Variable    @{localDateTime}[0]-@{localDateTime}[1]-@{localDateTime}[2] @{localDateTime}[3]:@{localDateTime}[4]:@{localDateTime}[5]
    ${endDateTime}=    add time to date    ${startDateTime}    2 minute    exclude_millis=yes
    Go Into Datetime    HOL    ${holidayStatField}    ${feedHolidayEXL}    ${feedHolidayRic}    ${connectTimesIdentifier}    ${feedTimeRic}
    ...    ${startDateTime}    ${endDateTime}
    Sleep    120
    Check InputPortStatsBlock    ${connectTimesIdentifier}    ${feedTimeRic}    ${holidayStatField}    0
    [Teardown]    Holiday Cleanup

Verify Holiday Removal
    [Documentation]    Verify that holiday can be removed properly.
    ...    1. Set current day inside holiday
    ...    2. Remove the holiday from the holiday RIC
    ...    3. Verify that the TD goes outside holiday based on holidayStatus stat block
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2212
    Comment    Feed Time Holiday
    ${feedTimeRic}    Set Variable    ${feedTimeRics[0]}
    ${contents}    Set Variable    ${feedTimeRicsDict['${feedTimeRic}']}
    ${feedHolidayRic}    Set Variable    ${contents[2]}
    ${contents}    Set Variable    ${feedHolidayRicsDict['${feedHolidayRic}']}
    ${feedHolidayEXL}    Set Variable    ${contents[0]}
    Go Into Datetime    HOL    ${holidayStatField}    ${feedHolidayEXL}    ${feedHolidayRic}    ${connectTimesIdentifier}    ${feedTimeRic}
    Load Single EXL File    ${feedHolidayEXL}    ${serviceName}    ${CHE_IP}
    Check InputPortStatsBlock    ${connectTimesIdentifier}    ${feedTimeRic}    ${holidayStatField}    0
    Comment    Trade Time Holiday
    ${tradeTimeRic}    Set Variable    ${tradeTimeRics[0]}
    ${contents}    Set Variable    ${tradeTimeRicsDict['${tradeTimeRic}']}
    ${tradeHolidayRic}    Set Variable    ${contents[2]}
    ${contents}    Set Variable    ${tradeHolidayRicsDict['${tradeHolidayRic}']}
    ${tradeHolidayEXL}    Set Variable    ${contents[0]}
    Go Into Datetime    HOL    ${holidayStatField}    ${tradeHolidayEXL}    ${tradeHolidayRic}    ${connectTimesIdentifier}    ${feedTimeRic}
    Load Single EXL File    ${tradeHolidayEXL}    ${serviceName}    ${CHE_IP}
    Check InputPortStatsBlock    ${connectTimesIdentifier}    ${feedTimeRic}    ${holidayStatField}    0
    [Teardown]    Holiday Cleanup

Verify Holiday RIC processing
    [Documentation]    Verify Holiday RIC processing:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1640
    [Setup]
    Run Holiday Test
    [Teardown]    Holiday Cleanup

Verify MTE Events Times
    [Documentation]    Rollover system time StartOfDayTime,EndOfDayTime,RolloverTime,CacheRolloverTime.\ Verify those events happened via check the SMF logs.
    ...    Test Case - Verify MTE Events Times
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2142
    [Setup]    Disable MTE Clock Sync
    ${MTETimeOffset}=    Get MTE Machine Time Offset
    @{configList}    Create List    StartOfDayTime    EndOfDayTime    RolloverTime    CacheRolloverTime
    ${ConfigValuesList}    Get Configure Values    @{configList}
    ${feedTimeRic}    Set Variable    ${feedTimeRics[0]}
    ${contents}    Set Variable    ${feedTimeRicsDict['${feedTimeRic}']}
    ${dstRicName}    Set Variable    ${contents[1]}
    ${currentGmtOffset}    get stat block field    ${MTE}    ${dstRicName}    currentGMTOffset
    @{tdBoxDateTime}=    get date and time
    ${AllTimesDict}    get future config times    ${configList}    ${ConfigValuesList}    ${currentGmtOffset}    ${tdBoxDateTime}
    Rollover Time Check SMF log    ${AllTimesDict}
    [Teardown]    Restore MTE Machine Time    ${MTETimeOffset}

Verify Trade Time processing
    [Documentation]    Verify Trade Time processing:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1644
    [Setup]
    Run Trade Time Test
    [Teardown]    Trade Time Cleanup

Verify Re-schedule ClosingRun through modifying EXL
    [Documentation]    In EXL file for Closing Run, if the time is changed, the Closing Run will be triggered at new time
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1846
    [Setup]    ClosingRun Setup
    Run Re-schedule ClosingRun Test
    [Teardown]    Re-schedule ClosingRun Cleanup

Verify Manual ClosingRun
    [Documentation]    Test Case - Verify Manual Closing Runs
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1886
    ...
    ...    The test case is used to verify the manual closing run, including doing a Closing Run for a specific RIC, a Closing Run for a specific Exl file and a Closing Run for a specific Closing Run RIC
    ${sampleRic}    ${publishKey}    Get RIC From MTE Cache
    ${domain}    Get Preferred Domain
    Manual ClosingRun for a RIC    ${sampleRic}    ${publishKey}    ${domain}
    Manual ClosingRun for the EXL File including target Ric    ${sampleRic}    ${publishKey}    ${domain}
    Manual ClosingRun for ClosingRun Rics    ${serviceName}

Verify ES persists State Processing RICs
    [Documentation]    Verify the EventScheduler persists the list of state processing RICs and on restart loads all of the saved RICs even if they are removed from FMS.
    ...
    ...    http://jirag.int.thomsonreuters.com/browse/CATF-2506
    ${servicename}    Get FMS Service Name
    ${stateRicList}=    Get All State Processing RICs
    @{stateFiles}=    Get All State EXL Files
    ${savedStateFiles}=    Rename Files    .exl    .exl.txt    @{stateFiles}
    ${remoteCfgFile}    ${backupCfgFile}    backup remote cfg file    ${REMOTE_MTE_CONFIG_DIR}    ${MTE_CONFIG}
    ${localCfgFile}=    Get MTE Config File
    Set Value in MTE cfg    ${localCfgFile}    ResendFM    ${0}    add    FMS
    Put Remote File    ${localCfgFile}    ${remoteCfgFile}
    Stop SMF
    Start SMF
    ${remoteRicListFile}=    set variable    ${BASE_DIR}/EventScheduler/dump_ric.txt
    ${fileContent}=    Execute Command    cat ${remoteRicListFile}
    ${ricsFromFile}=    Split To Lines    ${fileContent}
    Remove Values From List    ${ricsFromFile}    ${EMPTY}
    Sort List    ${stateRicList}
    Sort List    ${ricsFromFile}
    Lists Should Be Equal    ${stateRicList}    ${ricsFromFile}
    [Teardown]    Run Keywords    Restore Files    ${StateFiles}    ${savedStateFiles}
    ...    AND    Load All EXL Files    ${servicename}    ${CHE_IP}
    ...    AND    Restore remote cfg file    ${remoteCfgFile}    ${backupCfgFile}

*** Keywords ***
Scheduling Setup
    [Documentation]    1. Calling KW : Suite Setup
    ...    2. Setup Variables that need in Scheduling test suite
    ...    3. Setup Dictionary that need in Scheduling test suite
    Suite Setup
    Scheduling Variables
    Scheduling Mapping

Scheduling Variables
    [Documentation]    1. Set some common usage value into Suite Variable before test case start
    Comment    Feed Time
    Set Suite Variable    ${connectTimesIdentifier}    connectTimesIdentifier
    Set Suite Variable    ${feedTimeStatField}    shouldBeOpen
    @{processedFeedTimeExlFiles}    create list
    Set Suite Variable    @{processedFeedTimeExlFiles}
    Comment    Trade time
    Set Suite Variable    ${highactTimesIdentifier}    highactTimesIdentifier
    Set Suite Variable    ${tradeTimeStatField}    inHighActivity
    @{processedTradeTimeExlFiles}    create list
    Set Suite Variable    @{processedTradeTimeExlFiles}
    Comment    DST
    Set Suite Variable    ${dstStartDateStatField}    dstStartDate
    Set Suite Variable    ${dstEndDateStatField}    dstEndDate
    Comment    FMS
    ${serviceName}    Get FMS Service Name
    Set Suite Variable    ${serviceName}
    Set Suite Variable    ${statRicDomain}    MARKET_PRICE
    Comment    Holiday
    Set Suite Variable    ${holidayStatField}    holidayStatus
    Comment    DST
    @{processedDSTExlFiles}    create list
    Set Suite Variable    @{processedDSTExlFiles}
    Comment    EXLs
    ${modifiedExlFilesDic}    Create Dictionary
    Set Suite Variable    ${modifiedExlFilesDic}
    Set Suite Variable    ${ricDomain}    ${statRicDomain}

Scheduling Mapping
    [Documentation]    1. Getting Feed Time and Trade Time related information
    ...
    ...    2. Create Dictionary for Feed Time Rics and Trade Time Rics
    ...
    ...    3. Structure of dictionary for Feed Time and Trade Time
    ...    3.1 Key = Feed Time Ric name or Trade Time Ric name
    ...    3.2 Value = a List item with [0] = EXL file path , [1] DST Ric Name, [2] Holiday Ric Name
    ...
    ...    4. Structure of dictionary for Holiday Ric
    ...    4.1 Key =Holiday Ric name
    ...    4.2 Value = a List item with [0] = EXL file path , [1] DST Ric Name
    ${allHolidayEXLs}    Create List
    Set Suite Variable    ${allHolidayEXLs}
    Comment    Feed Time
    ${feedTimeRics}    Get ConnectTimesIdentifier
    Set Suite Variable    ${feedTimeRics}
    ${feedTimeRicsDict}    Create Dictionary
    ${feedHolidayRicsDict}    Create Dictionary
    Set Suite Variable    ${feedTimeRicsDict}
    Set Suite Variable    ${feedHolidayRicsDict}
    : FOR    ${feedTimeRic}    IN    @{feedTimeRics}
    \    ${feedTimeEXL}    get state EXL file    ${feedTimeRic}    ${statRicDomain}    ${serviceName}    Feed Time
    \    ${feedDstRic}    ${feedHolidayRic}    Get DST And Holiday RICs From EXL    ${feedTimeEXL}    ${feedTimeRic}
    \    ${feedHolidayEXL}    get state EXL file    ${feedHolidayRic}    ${statRicDomain}    ${serviceName}    Holiday
    \    ${infoList}    Create List    ${feedTimeEXL}    ${feedDstRic}    ${feedHolidayRic}
    \    Set To Dictionary    ${feedTimeRicsDict}    ${feedTimeRic}    ${infoList}
    \    ${infoList}    Create List    ${feedHolidayEXL}    ${feedDstRic}
    \    Set To Dictionary    ${feedHolidayRicsDict}    ${feedHolidayRic}    ${infoList}
    \    Append To List    ${allHolidayEXLs}    ${feedHolidayEXL}
    Comment    Trade Time
    ${tradeTimeRics}    Get HighActivityTimesIdentifier
    Set Suite Variable    ${tradeTimeRics}
    ${tradeTimeRicsDict}    Create Dictionary
    ${tradeHolidayRicsDict}    Create Dictionary
    Set Suite Variable    ${tradeTimeRicsDict}
    Set Suite Variable    ${tradeHolidayRicsDict}
    : FOR    ${tradeTimeRic}    IN    @{tradeTimeRics}
    \    ${tradeTimeEXL}    get state EXL file    ${tradeTimeRic}    ${statRicDomain}    ${serviceName}    Trade Time
    \    ${tradeDstRic}    ${tradeHolidayRic}    Get DST And Holiday RICs From EXL    ${tradeTimeEXL}    ${tradeTimeRic}
    \    ${tradeHolidayEXL}    get state EXL file    ${tradeHolidayRic}    ${statRicDomain}    ${serviceName}    Holiday
    \    ${infoList}    Create List    ${tradeTimeEXL}    ${tradeDstRic}    ${tradeHolidayRic}
    \    Set To Dictionary    ${tradeTimeRicsDict}    ${tradeTimeRic}    ${infoList}
    \    ${infoList}    Create List    ${tradeHolidayEXL}    ${tradeDstRic}
    \    Set To Dictionary    ${tradeHolidayRicsDict}    ${tradeHolidayRic}    ${infoList}
    \    Append To List    ${allHolidayEXLs}    ${tradeHolidayEXL}
    ${allHolidayEXLs}    Remove Duplicates    ${allHolidayEXLs}

Calculate DST Start Date And Check Stat
    [Arguments]    ${dstRicName}    ${dstStartDatetime}
    ${normalGMTOffset}    get stat block field    ${MTE}    ${dstRicName}    normalGMTOffset
    ${startDatetime}    subtract time from date    ${dstStartDatetime}    ${normalGMTOffset} second    result_format=%Y-%m-%dT%H:%M:%S.0
    ${expectedStartDatetime}    convert EXL datetime to statblock format    ${startDatetime}
    wait for statBlock    ${MTE}    ${dstRicName}    ${dstStartDateStatField}    ${expectedStartDatetime}    waittime=2    timeout=120

Calculate DST End Date And Check Stat
    [Arguments]    ${dstRicName}    ${dstEndDatetime}
    ${dstGMTOffset}    get stat block field    ${MTE}    ${dstRicName}    dstGMTOffset
    ${endDatetime}    subtract time from date    ${dstEndDatetime}    ${dstGMTOffset} second    result_format=%Y-%m-%dT%H:%M:%S.0
    ${expectedEndDatetime}    convert EXL datetime to statblock format    ${endDatetime}
    wait for statBlock    ${MTE}    ${dstRicName}    ${dstEndDateStatField}    ${expectedEndDatetime}    waittime=2    timeout=120

Load EXL and Check Stat For DST
    [Arguments]    ${exlFile}    ${ricName}    ${statField}    ${startDatetime}    ${endDatetime}
    Load Single EXL File    ${exlFile}    ${serviceName}    ${CHE_IP}
    Calculate DST start date and check stat    ${ricName}    ${startDatetime}
    Calculate DST end date and check stat    ${ricName}    ${endDatetime}
    ${expectedDstGMTOffset}    get stat block field    ${MTE}    ${ricName}    ${statField}
    wait for statBlock    ${MTE}    ${ricName}    currentGMTOffset    ${expectedDstGMTOffset}    waittime=2    timeout=120

Run DST Test
    [Documentation]    Remark : If there are multiples feed time/trade time rics, we only pick one of them and test on its corresponding DST ric
    Comment    Feed Time DST
    ${feedTimeRic}    Set Variable    ${feedTimeRics[0]}
    ${contents}    Set Variable    ${feedTimeRicsDict['${feedTimeRic}']}
    ${feedDstRic}    Set Variable    ${contents[1]}
    ${feedDstEXL}    get state EXL file    ${feedDstRic}    ${statRicDomain}    ${serviceName}    DST
    Append To List    ${processedDSTExlFiles}    ${feedDstEXL}
    Go Into Datetime    DST    ${EMPTY}    ${feedDstEXL}    ${feedDstRic}    ${EMPTY}    ${EMPTY}
    Go outside Datetime    DST    ${EMPTY}    ${feedDstEXL}    ${feedDstRic}    ${EMPTY}    ${EMPTY}
    Go Into Datetime    DST    ${EMPTY}    ${feedDstEXL}    ${feedDstRic}    ${EMPTY}    ${EMPTY}
    Comment    Trade Time DST
    ${tradeTimeRic}    Set Variable    ${tradeTimeRics[0]}
    ${contents}    Set Variable    ${tradeTimeRicsDict['${tradeTimeRic}']}
    ${tradeDstRic}    Set Variable    ${contents[1]}
    ${tradeDstEXL}    get state EXL file    ${tradeDstRic}    ${statRicDomain}    ${serviceName}    DST
    Append To List    ${processedDSTExlFiles}    ${tradeDstEXL}
    Go Into Datetime    DST    ${EMPTY}    ${tradeDstEXL}    ${tradeDstRic}    ${EMPTY}    ${EMPTY}
    Go outside Datetime    DST    ${EMPTY}    ${tradeDstEXL}    ${tradeDstRic}    ${EMPTY}    ${EMPTY}
    Go Into Datetime    DST    ${EMPTY}    ${tradeDstEXL}    ${tradeDstRic}    ${EMPTY}    ${EMPTY}

DST Cleanup
    Comment    DST Cleanup
    : FOR    ${processedDSTExlFile}    IN    @{processedDSTExlFiles}
    \    Load Single EXL File    ${processedDSTExlFile}    ${serviceName}    ${CHE_IP}

Run Feed Time Test
    [Documentation]    Remark : We test all Feed Time Rics that we found in MTE
    Blank Out All Holiday EXLs
    Go Outside All Times    Feed Time    ${feedTimeStatField}    ${connectTimesIdentifier}    ${feedTimeRicsDict}    ${feedTimeRics}
    Comment    Feed Time Test
    ${type}    Set Variable    Feed Time
    : FOR    ${feedTimeRic}    IN    @{feedTimeRics}
    \    ${contents}    Set Variable    ${feedTimeRicsDict['${feedTimeRic}']}
    \    ${feedTimeExlFile}    Set Variable    ${contents[0]}
    \    ${dstRicName}    Set Variable    ${contents[1]}
    \    ${tdBoxDateTime}    ${localVenueDateTime}    Get Venue Local Datetime From MTE    ${dstRicName}
    \    Go Into Time    ${type}    ${feedTimeExlFile}    ${feedTimeRic}    ${feedTimeStatField}    ${connectTimesIdentifier}
    \    ...    ${feedTimeRic}    ${localVenueDateTime}
    \    Go Outside Time    ${type}    ${feedTimeExlFile}    ${feedTimeRic}    ${feedTimeStatField}    ${connectTimesIdentifier}
    \    ...    ${feedTimeRic}    ${localVenueDateTime}    True    1 minute
    \    Go Into Time    ${type}    ${feedTimeExlFile}    ${feedTimeRic}    ${feedTimeStatField}    ${connectTimesIdentifier}
    \    ...    ${feedTimeRic}    ${localVenueDateTime}    True    1 minute

Feed Time Cleanup
    Comment    Restore all feed time
    : FOR    ${feedTimeRic}    IN    @{feedTimeRics}
    \    ${contents}    Set Variable    ${feedTimeRicsDict['${feedTimeRic}']}
    \    ${feedTimeExlFile}    Set Variable    ${contents[0]}
    \    Load Single EXL File    ${feedTimeExlFile}    ${serviceName}    ${CHE_IP}
    Comment    Restore all holiday
    Holiday Cleanup
    Comment    Remove all modified EXLs
    ${modifiedEXLFiles}    Get Dictionary Values    ${modifiedExlFilesDic}
    ${count}    Get Length    ${modifiedEXLFiles}
    Run Keyword If    ${count} > 0    remove files    @{modifiedEXLFiles}
    ${modifiedExlFilesDic}    Create Dictionary
    Set Suite Variable    ${modifiedExlFilesDic}

Run Trade Time Test
    [Documentation]    Remark : If there are multiples trade time rics, we only pick one of them for testing
    Blank Out All Holiday EXLs
    Comment    Go Into feed time
    ${type}    Set Variable    Feed Time
    ${feedTimeRic}    Set Variable    ${feedTimeRics[0]}
    ${contents}    Set Variable    ${feedTimeRicsDict['${feedTimeRic}']}
    ${feedTimeExlFile}    Set Variable    ${contents[0]}
    ${dstRicName}    Set Variable    ${contents[1]}
    ${tdBoxDateTime}    ${localVenueDateTime}    Get Venue Local Datetime From MTE    ${dstRicName}
    Go Into Time    ${type}    ${feedTimeExlFile}    ${feedTimeRic}    ${feedTimeStatField}    ${connectTimesIdentifier}    ${feedTimeRic}
    ...    ${localVenueDateTime}
    Go Outside All Times    Trade Time    ${tradeTimeStatField}    ${highactTimesIdentifier}    ${tradeTimeRicsDict}    ${tradeTimeRics}
    Comment    Trade Time Test
    ${type}    Set Variable    Trade Time
    ${tradeTimeRic}    Set Variable    ${tradeTimeRics[0]}
    ${contents}    Set Variable    ${tradeTimeRicsDict['${tradeTimeRic}']}
    ${tradeTimeExlFile}    Set Variable    ${contents[0]}
    ${dstRicName}    Set Variable    ${contents[1]}
    ${tdBoxDateTime}    ${localVenueDateTime}    Get Venue Local Datetime From MTE    ${dstRicName}
    Go Into Time    ${type}    ${tradeTimeExlFile}    ${tradeTimeRic}    ${tradeTimeStatField}    ${highactTimesIdentifier}    ${tradeTimeRic}
    ...    ${localVenueDateTime}
    Check ConfigurationStatsBlock    ${tradeTimeStatField}    1
    Go Outside Time    ${type}    ${tradeTimeExlFile}    ${tradeTimeRic}    ${tradeTimeStatField}    ${highactTimesIdentifier}    ${tradeTimeRic}
    ...    ${localVenueDateTime}    True    1 minute
    Check ConfigurationStatsBlock    ${tradeTimeStatField}    0
    Go Into Time    ${type}    ${tradeTimeExlFile}    ${tradeTimeRic}    ${tradeTimeStatField}    ${highactTimesIdentifier}    ${tradeTimeRic}
    ...    ${localVenueDateTime}    True    1 minute
    Check ConfigurationStatsBlock    ${tradeTimeStatField}    1

Trade Time Cleanup
    Comment    Restore all feed time
    ${feedTimeRic}    Set Variable    ${feedTimeRics[0]}
    ${contents}    Set Variable    ${feedTimeRicsDict['${feedTimeRic}']}
    ${feedTimeExlFile}    Set Variable    ${contents[0]}
    Load Single EXL File    ${feedTimeExlFile}    ${serviceName}    ${CHE_IP}
    Comment    Restore all trade time
    : FOR    ${tradeTimeRic}    IN    @{tradeTimeRics}
    \    ${contents}    Set Variable    ${tradeTimeRicsDict['${tradeTimeRic}']}
    \    ${tradeTimeExlFile}    Set Variable    ${contents[0]}
    \    Load Single EXL File    ${tradeTimeExlFile}    ${serviceName}    ${CHE_IP}
    Comment    Restore all holiday
    Holiday Cleanup
    Comment    Remove all modified EXLs
    ${modifiedEXLFiles}    Get Dictionary Values    ${modifiedExlFilesDic}
    ${count}    Get Length    ${modifiedEXLFiles}
    Run Keyword If    ${count} > 0    remove files    @{modifiedEXLFiles}
    ${modifiedExlFilesDic}    Create Dictionary
    Set Suite Variable    ${modifiedExlFilesDic}

Run Holiday Test
    [Documentation]    Remark : If there are multiples feed time/trade time rics, we only pick one of them and test on its corresponding Holiday ric
    Blank Out All Holiday EXLs
    Comment    Feed Time Holiday
    ${feedTimeRic}    Set Variable    ${feedTimeRics[0]}
    ${contents}    Set Variable    ${feedTimeRicsDict['${feedTimeRic}']}
    ${feedHolidayRic}    Set Variable    ${contents[2]}
    ${contents}    Set Variable    ${feedHolidayRicsDict['${feedHolidayRic}']}
    ${feedHolidayEXL}    Set Variable    ${contents[0]}
    Go Into Datetime    HOL    ${holidayStatField}    ${feedHolidayEXL}    ${feedHolidayRic}    ${connectTimesIdentifier}    ${feedTimeRic}
    Go Outside Datetime    HOL    ${holidayStatField}    ${feedHolidayEXL}    ${feedHolidayRic}    ${connectTimesIdentifier}    ${feedTimeRic}
    Go Into Datetime    HOL    ${holidayStatField}    ${feedHolidayEXL}    ${feedHolidayRic}    ${connectTimesIdentifier}    ${feedTimeRic}
    Comment    Trade Time Holiday
    ${tradeTimeRic}    Set Variable    ${tradeTimeRics[0]}
    ${contents}    Set Variable    ${tradeTimeRicsDict['${tradeTimeRic}']}
    ${tradeHolidayRic}    Set Variable    ${contents[2]}
    ${contents}    Set Variable    ${tradeHolidayRicsDict['${tradeHolidayRic}']}
    ${tradeHolidayEXL}    Set Variable    ${contents[0]}
    Go Into Datetime    HOL    ${holidayStatField}    ${tradeHolidayEXL}    ${tradeHolidayRic}    ${connectTimesIdentifier}    ${feedTimeRic}
    Go Outside Datetime    HOL    ${holidayStatField}    ${tradeHolidayEXL}    ${tradeHolidayRic}    ${connectTimesIdentifier}    ${feedTimeRic}
    Go Into Datetime    HOL    ${holidayStatField}    ${tradeHolidayEXL}    ${tradeHolidayRic}    ${connectTimesIdentifier}    ${feedTimeRic}

Holiday Cleanup
    : FOR    ${holidayEXL}    IN    @{allHolidayEXLs}
    \    Load Single EXL File    ${holidayEXL}    ${serviceName}    ${CHE_IP}

ClosingRun Setup
    @{closingRunRics}    Get RIC List From StatBlock    Closing Run
    Sort List    ${closingRunRics}
    set suite variable    @{closingRunRics}
    @{closingRunExlFiles}    create list
    Set Suite Variable    @{closingRunExlFiles}

Run Re-schedule ClosingRun Test
    [Documentation]    Remark : If there are multiples closingRun rics, we only pick one of them and test on it
    Blank Out All Holiday EXLs
    ${closingRunRic}    Set Variable    ${closingRunRics[0]}
    ${closingRunExlFile}    get state EXL file    ${closingRunRic}    ${statRicDomain}    ${serviceName}    Closing Run
    ${closingRunDstRic}    ${closingRunHolidayRic}    Get DST And Holiday RICs From EXL    ${closingRunExlFile}    ${closingRunRic}
    ${tdBoxDateTime}    ${localVenueDateTime}    Get Venue Local Datetime From MTE    ${closingRunDstRic}
    ${weekDay}    get day of week from date    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}
    ${closingRunTimeStartTime}    add time to date    ${localVenueDateTime[0]}-${localVenueDateTime[1]}-${localVenueDateTime[2]} ${localVenueDateTime[3]}:${localVenueDateTime[4]}:${localVenueDateTime[5]}    120 second    result_format=%H:%M:%S
    ${closingRunExlFileOnly}    Fetch From Right    ${closingRunExlFile}    \\
    ${closingRunExlfileModified}=    set variable    ${LOCAL_TMP_DIR}/${closingRunExlFileOnly}_modified.exl
    modify EXL    ${closingRunExlFile}    ${closingRunExlfileModified}    ${closingrunRic}    ${statRicDomain}    <it:SCHEDULE_${weekDay}>\n<it:TIME>${closingRunTimeStartTime}</it:TIME>\n</it:SCHEDULE_${weekDay}>
    Append to list    ${closingRunExlFiles}    ${closingRunExlFile}
    Load Single EXL File    ${closingRunExlfileModified}    ${serviceName}    ${CHE_IP}
    remove files    ${closingRunExlfileModified}
    Sleep    1 minutes 20 seconds
    wait smf log message after time    ClosingRunEventHandler for [0-9]*.*?TRIGGERING    ${tdBoxDateTime}    waittime=5    timeout=120

Re-schedule ClosingRun Cleanup
    Comment    Restore all closing run
    Remove Duplicates    ${closingRunExlFiles}
    : FOR    ${closingRunExlFile}    IN    @{closingRunExlFiles}
    \    Load Single EXL File    ${closingRunExlFile}    ${serviceName}    ${CHE_IP}
    Comment    Restore all holiday
    Holiday Cleanup

Manual ClosingRun for the EXL File including target Ric
    [Arguments]    ${sampleRic}    ${publishKey}    ${domain}
    ${sampleExlFile}    get_EXL_for_RIC    ${domain}    ${serviceName}    ${sampleRic}
    Start Capture MTE Output
    ${currentDateTime}    get date and time
    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd    ${CHE_IP}    Close    --Services ${serviceName}
    ...    --BypassFiltering ${True}    --SendOrphanedToAllHeadends ${True}    --ClosingRunRule 1000    --InputFile "${sampleExlFile}"
    wait SMF log message after time    Closing RIC:    ${currentDateTime}    waittime=2    timeout=60
    Stop Capture MTE Output
    ${localcapture}    set variable    ${LOCAL_TMP_DIR}/capture_local.pcap
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${localcapture}
    Run Keyword And Continue On Failure    verify ClosingRun message in messages    ${localcapture}    ${publishKey}
    remove files    ${localcapture}
    delete remote files    ${REMOTE_TMP_DIR}/capture.pcap

Get Venue Local Datetime From MTE
    [Arguments]    ${ricName}
    ${currentDateTime}    get date and time
    ${localVenueDateTime}    Get GMT Offset And Apply To Datetime    ${ricName}    ${currentDateTime[0]}    ${currentDateTime[1]}    ${currentDateTime[2]}    ${currentDateTime[3]}
    ...    ${currentDateTime[4]}    ${currentDateTime[5]}
    [Return]    ${currentDateTime}    ${localVenueDateTime}

Load EXL and Check Stat
    [Arguments]    ${exlFile}    ${service}    ${identifierName}    ${identifierValue}    ${statFieldName}    ${statValue}
    ...    ${isCheckStat}=True
    [Documentation]    Note that all input port stats blocks (that have ${identifierName} set to ${statIdentifier}) will be checked here.
    Load Single EXL File    ${exlFile}    ${service}    ${CHE_IP}
    Run Keyword If    '${isCheckStat}'=='True'    Check InputPortStatsBlock    ${identifierName}    ${identifierValue}    ${statFieldName}    ${statValue}

Blank Out All Holiday EXLs
    [Documentation]    Remove all Holiday Entriese from EXLs i.e. enforce NO Holiday for the MTE
    : FOR    ${holidayEXL}    IN    @{allHolidayEXLs}
    \    ${exlFilename}    Fetch From Right    ${holidayEXL}    \\
    \    ${exlFileModified}    Set Variable    ${LOCAL_TMP_DIR}/${eXLFilename}_modified.exl
    \    blank out holidays    ${holidayEXL}    ${exlFileModified}
    \    remove files    ${exlFileModified}

Check InputPortStatsBlock
    [Arguments]    ${identifierFieldName}    ${identifierValue}    ${statFieldName}    ${statValue}
    [Documentation]    Loop through all MTE's InputPortStatsBlock
    ...
    ...    1. Checking if ${identifierValue} == InputPortStatsBlock's ${identifierFieldName} value
    ...    (This actually indicate if the time Ric e.g. feed time ric or trade time ric has influence on this InputPortStatsBlock_x)
    ...
    ...    2. If 1.) is True, verify InputPortStatsBlock's ${statFieldName} == ${statValue}
    @{blocks}=    Get Stat Blocks For Category    ${MTE}    InputLineStats
    : FOR    ${block}    IN    @{blocks}
    \    ${fieldValue}    get stat block field    ${MTE}    ${block}    ${identifierFieldName}
    \    ${fieldValueList}    Split String    ${fieldValue}    ,
    \    ${count}    Count Values In List    ${fieldValueList}    ${identifierValue}
    \    run keyword if    ${count} > 0    wait for statBlock    ${MTE}    ${block}    ${statFieldName}
    \    ...    ${statValue}    waittime=2    timeout=300

Check ConfigurationStatsBlock
    [Arguments]    ${statFieldName}    ${statValue}
    [Documentation]    Checking ConfigurationStatsBlock field value
    wait for statBlock    ${MTE}    ConfigurationStatsBlock    ${statFieldName}    ${statValue}    waittime=2    timeout=300

Set Times For IN State
    [Arguments]    ${hour}    ${min}    ${sec}    ${advOffset}=${EMPTY}
    [Documentation]    For start time, uses values passed in.
    ...
    ...    For end time, sets it to 23:59:59. the advOffset is to add some time in existing time
    ${startTime}=    Set Variable    ${hour}:${min}:${sec}
    ${startTime}=    run keyword if    '${advOffset}'!='${Empty}'    add time to time    ${startTime}    ${advOffset}    timer
    ...    exclude_millis=yes
    ...    ELSE    set variable    ${hour}:${min}:${sec}
    ${endTime}    set variable    23:59:59
    [Return]    ${startTime}    ${endTime}

Go Into All Times
    [Arguments]    ${type}    ${statFieldName}    ${identifierFieldName}    ${dict}    ${rics}
    [Documentation]    Go into all feed times or trade times
    : FOR    ${ric}    IN    @{rics}
    \    ${contents}    Set Variable    ${dict['${ric}']}
    \    ${exlFile}    Set Variable    ${contents[0]}
    \    ${dstRicName}    Set Variable    ${contents[1]}
    \    ${tdBoxDateTime}    ${localVenueDateTime}    Get Venue Local Datetime From MTE    ${dstRicName}
    \    ${exlFileModified}    Go Into Time    ${type}    ${exlFile}    ${ric}    ${statFieldName}
    \    ...    ${identifierFieldName}    ${ric}    ${localVenueDateTime}    ${False}
    \    ${processedExls}    Get Dictionary Keys    ${modifiedExlFilesDic}
    \    ${count}    Count Values In List    ${processedExls}    ${exlFile}
    \    Run Keyword If    ${count} == 0    Set To Dictionary    ${modifiedExlFilesDic}    ${exlFile}    ${exlFileModified}
    : FOR    ${ric}    IN    @{rics}
    \    Check InputPortStatsBlock    ${identifierFieldName}    ${ric}    ${statFieldName}    1

Go Into Time
    [Arguments]    ${type}    ${exlFile}    ${ricName}    ${statFieldName}    ${identifierFieldName}    ${identifierValue}
    ...    ${localVenueDateTime}    ${isCheckStat}=True    ${advOffset}=${EMPTY}
    [Documentation]    Go into specific feed time or trade time
    Comment    Check if EXLs has been modified before, we would keep using same modified file within one test case
    ${processedExls}    Get Dictionary Keys    ${modifiedExlFilesDic}
    ${count}    Count Values In List    ${processedExls}    ${exlFile}
    ${exlFilename}    Fetch From Right    ${exlFile}    \\
    ${exlFileModified}    Set Variable    ${LOCAL_TMP_DIR}\\${exlFilename}_modified.exl
    ${exlFileUse}    Set Variable If    ${count} > 0    ${exlFileModified}    ${exlFile}
    ${weekDay}    get day of week from date    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}
    ${startTime}    ${endTime}    Set times for IN state    ${localVenueDateTime[3]}    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}    ${advOffset}
    Run Keyword If    '${type}' == 'Feed Time'    Set Feed Time In EXL    ${exlFileUse}    ${exlFileModified}    ${ricName}    ${statRicDomain}
    ...    ${startTime}    ${endTime}    ${weekDay}
    Run Keyword If    '${type}' == 'Trade Time'    Set Trade Time In EXL    ${exlFileUse}    ${exlFileModified}    ${ricName}    ${statRicDomain}
    ...    ${startTime}    ${endTime}    ${weekDay}
    Load Single EXL File    ${exlFileModified}    ${serviceName}    ${CHE_IP}
    @{tdBoxDateTime}=    run keyword if    '${advOffset}'!='${Empty}'    Get Date and Time
    run keyword if    '${advOffset}'!='${Empty}'    Sleep    30s
    Run Keyword If    '${isCheckStat}'=='True'    Check InputPortStatsBlock    ${identifierFieldName}    ${identifierValue}    ${statFieldName}    1
    ${eventName}    Run Keyword If    '${type}' == 'Feed Time'    set variable    StartOfConnect
    ...    ELSE    set variable    StartOfHighActivity
    run keyword if    '${advOffset}'!='${Empty}'    check logfile for event    ${eventName}    ${tdBoxDateTime}
    [Return]    ${exlFileModified}

Set Times For OUT State
    [Arguments]    ${hour}    ${min}    ${sec}    ${advOffset}=${EMPTY}
    [Documentation]    For start time, sets it to 00:00:00.
    ...
    ...    For end time, uses values passed in.
    ${startTime}    set variable    00:00:00
    ${endTime}=    Set Variable    ${hour}:${min}:${sec}
    ${endTime}    run keyword if    '${advOffset}'!='${Empty}'    add time to time    ${endTime}    ${advOffset}    timer
    ...    exclude_millis=yes
    ...    ELSE    set variable    ${hour}:${min}:${sec}
    [Return]    ${startTime}    ${endTime}

Go Outside All Times
    [Arguments]    ${type}    ${statFieldName}    ${identifierFieldName}    ${dict}    ${rics}
    [Documentation]    Go outside all feed times or trade times
    : FOR    ${ric}    IN    @{rics}
    \    ${contents}    Set Variable    ${dict['${ric}']}
    \    ${exlFile}    Set Variable    ${contents[0]}
    \    ${dstRicName}    Set Variable    ${contents[1]}
    \    ${tdBoxDateTime}    ${localVenueDateTime}    Get Venue Local Datetime From MTE    ${dstRicName}
    \    ${exlFileModified}    Go Outside Time    ${type}    ${exlFile}    ${ric}    ${statFieldName}
    \    ...    ${identifierFieldName}    ${ric}    ${localVenueDateTime}    ${False}
    \    ${processedExls}    Get Dictionary Keys    ${modifiedExlFilesDic}
    \    ${count}    Count Values In List    ${processedExls}    ${exlFile}
    \    Run Keyword If    ${count} == 0    Set To Dictionary    ${modifiedExlFilesDic}    ${exlFile}    ${exlFileModified}
    Comment    Checking status only when we go outside all
    : FOR    ${ric}    IN    @{rics}
    \    Check InputPortStatsBlock    ${identifierFieldName}    ${ric}    ${statFieldName}    0

Go Outside Time
    [Arguments]    ${type}    ${exlFile}    ${ricName}    ${statFieldName}    ${identifierFieldName}    ${identifierValue}
    ...    ${localVenueDateTime}    ${isCheckStat}=True    ${advOffset}=${EMPTY}
    [Documentation]    Go outside specific feed time or trade time
    Comment    Check if EXLs has been modified before, we would keep using same modified file within one test case
    ${processedExls}    Get Dictionary Keys    ${modifiedExlFilesDic}
    ${count}    Count Values In List    ${processedExls}    ${exlFile}
    ${exlFilename}    Fetch From Right    ${exlFile}    \\
    ${exlFileModified}    Set Variable    ${LOCAL_TMP_DIR}\\${exlFilename}_modified.exl
    ${exlFileUse}    Set Variable If    ${count} > 0    ${exlFileModified}    ${exlFile}
    ${weekDay}    get day of week from date    ${localVenueDateTime[0]}    ${localVenueDateTime[1]}    ${localVenueDateTime[2]}
    ${startTime}    ${endTime}    Set times for OUT state    ${localVenueDateTime[3]}    ${localVenueDateTime[4]}    ${localVenueDateTime[5]}    ${advOffset}
    Run Keyword If    '${type}' == 'Feed Time'    Set Feed Time In EXL    ${exlFileUse}    ${exlFileModified}    ${ricName}    ${statRicDomain}
    ...    ${startTime}    ${endTime}    ${weekDay}
    Run Keyword If    '${type}' == 'Trade Time'    Set Trade Time In EXL    ${exlFileUse}    ${exlFileModified}    ${ricName}    ${statRicDomain}
    ...    ${startTime}    ${endTime}    ${weekDay}
    Comment    Load EXL and Check Stat    ${exlFileModified}    ${serviceName}    ${identifierFieldName}    ${identifierValue}    ${statFieldName}
    ...    0    ${isCheckStat}
    Load Single EXL File    ${exlFileModified}    ${serviceName}    ${CHE_IP}
    @{tdBoxDateTime}=    run keyword if    '${advOffset}'!='${Empty}'    Get Date and Time
    run keyword if    '${advOffset}'!='${Empty}'    Sleep    30s
    Run Keyword If    '${isCheckStat}'=='True'    Check InputPortStatsBlock    ${identifierFieldName}    ${identifierValue}    ${statFieldName}    0
    ${eventName}    Run Keyword If    '${type}' == 'Feed Time'    set variable    EndOfConnect
    ...    ELSE    set variable    EndOfHighActivity
    run keyword if    '${advOffset}'!='${Empty}'    check logfile for event    ${eventName}    ${tdBoxDateTime}
    [Return]    ${exlFileModified}

Set Datetimes For IN State
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

Go Into Datetime
    [Arguments]    ${type}    ${statField}    ${exlFile}    ${ricName}    ${identifier}    ${identifierValue}
    ...    ${startDatetime}=${EMPTY}    ${endDatetime}=${EMPTY}
    [Documentation]    Go into holiday or DST dateime
    ...
    ...    If ${startDatetime} or ${endDatetime} is not specified, it will call KW 'Set Datetims FOR IN State' to get the start time and end time.
    ${exlFilename}    Fetch From Right    ${exlFile}    \\
    ${exlFileModified}    Set Variable    ${LOCAL_TMP_DIR}/${exlFilename}_modified.exl
    ${tdBoxDateTime}    get date and time
    ${startDatetime}    ${endDatetime}    Run Keyword If    '${startDateTime}' == '${EMPTY}' or '${endDateTime}' == '${EMPTY}'    Set Datetimes For IN State    ${tdBoxDateTime[0]}    ${tdBoxDateTime[1]}
    ...    ${tdBoxDateTime[2]}    ${tdBoxDateTime[3]}    ${tdBoxDateTime[4]}    ${tdBoxDateTime[5]}
    ...    ELSE    set variable    ${startDatetime}    ${endDatetime}
    ${startDateTimeT}    Replace String    ${startDatetime}    ${SPACE}    T
    ${endDatetimeT}    Replace String    ${endDatetime}    ${SPACE}    T
    Run Keyword If    '${type}' == 'HOL'    Run Keywords    Set Holiday Datetime In EXL    ${exlFile}    ${exlFileModified}    ${ricName}
    ...    ${statRicDomain}    ${startDateTimeT}.00    ${endDatetimeT}.00
    ...    AND    Load EXL and Check Stat    ${exlFileModified}    ${serviceName}    ${identifier}    ${identifierValue}
    ...    ${statField}    1
    Run Keyword If    '${type}' == 'DST'    Run Keywords    Set DST Datetime In EXL    ${exlFile}    ${exlFileModified}    ${ricName}
    ...    ${statRicDomain}    ${startDateTimeT}.00    ${endDatetimeT}.00
    ...    AND    Load EXL and Check Stat For DST    ${exlFileModified}    ${ricName}    dstGMTOffset    ${startDateTimeT}.00
    ...    ${endDatetimeT}.00
    remove files    ${exlFileModified}

Set Datetimes For OUT State
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

Go Outside Datetime
    [Arguments]    ${type}    ${statField}    ${exlFile}    ${ricName}    ${identifier}    ${identifierValue}
    [Documentation]    Go outside holiday or DST datetime
    ${exlFilename}    Fetch From Right    ${exlFile}    \\
    ${exlFileModified}    Set Variable    ${LOCAL_TMP_DIR}/${exlFilename}_modified.exl
    ${tdBoxDateTime}    get date and time
    ${startDatetime}    ${endDatetime}    Set Datetimes For OUT State    ${tdBoxDateTime[0]}    ${tdBoxDateTime[1]}    ${tdBoxDateTime[2]}    ${tdBoxDateTime[3]}
    ...    ${tdBoxDateTime[4]}    ${tdBoxDateTime[5]}
    ${startDateTimeT}    Replace String    ${startDatetime}    ${SPACE}    T
    ${endDatetimeT}    Replace String    ${endDatetime}    ${SPACE}    T
    Run Keyword If    '${type}' == 'HOL'    Run Keywords    Set Holiday Datetime In EXL    ${exlFile}    ${exlFileModified}    ${ricName}
    ...    ${statRicDomain}    ${startDateTimeT}.00    ${endDatetimeT}.00
    ...    AND    Load EXL and Check Stat    ${exlFileModified}    ${serviceName}    ${identifier}    ${identifierValue}
    ...    ${statField}    0
    Run Keyword If    '${type}' == 'DST'    Run Keywords    Set DST Datetime In EXL    ${exlFile}    ${exlFileModified}    ${ricName}
    ...    ${statRicDomain}    ${startDateTimeT}.00    ${endDatetimeT}.00
    ...    AND    Load EXL and Check Stat For DST    ${exlFileModified}    ${ricName}    normalGMTOffset    ${startDateTimeT}.00
    ...    ${endDatetimeT}.00
    remove files    ${exlFileModified}
