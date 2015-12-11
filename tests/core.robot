*** Settings ***
Documentation     The common set of Robot imports and keywords for Thunderdome.
...               This file should be imported as a Resource in each Thunderdome test suite.
Library           GATSNG
Library           LinuxCoreUtilities
Library           LinuxToolUtilities
Library           LinuxFSUtilities
Library           Collections
Library           OperatingSystem
Library           FMUtilities
Library           LocalBoxUtilities
Library           String

*** Keywords ***
Suite Setup
    [Documentation]    Do test suite level setup, e.g. things that take time and do not need to be repeated for each test case.
    open connection    host=${CHE_IP}    port=${CHE_PORT}    timeout=6
    login    ${USERNAME}    ${PASSWORD}
    start smf
    setUtilPath    ${BASE_DIR}
    Start MTE    ${MTE}

Suite Teardown
    [Documentation]    Do test suite level teardown, e.g. closing ssh connections.
    close all connections

Case Teardown
    [Arguments]    @{tmpfiles}
    [Documentation]    Do test case teardown, e.g. remove temp files.
    Run Keyword if Test Passed    Remove Files    @{tmpfiles}

Delete Persist Files
    [Arguments]    ${mte}    ${venue}
    delete remote files matching pattern    ${venue}    PERSIST_${mte}.DAT*    recurse=${True}
    ${res}=    search remote files    ${venue}    PERSIST_${mte}.DAT    recurse=${True}
    Should Be Empty    ${res}
    Comment    Currently, GATS does not provide the Venue name, so the pattern matching Keywords must be used. If GATS provides the Venue name, then "delete remote file" and "remote file should not exist" Keywords could be used here.

Disable PE Mangling
    [Arguments]    ${mte}    ${configFile}=manglingConfiguration.xml
    [Documentation]    Disable the PE mangling for MTE
    @{files}=    backup cfg file    ${VENUE_DIR}    ${configFile}
    set PE mangling value    ${False}    @{files}[0]
    Stop MTE    ${mte}
    Start MTE    ${mte}
    restore cfg file    @{files}

Dumpcache And Copyback Result
    [Arguments]    ${mte}    ${destfile}    # where will the csv be copied back
    [Documentation]    Dump the MTE cache to a file and copy the file to the local temp directory.
    ${remotedumpfile}=    dump cache    ${mte}    ${VENUE_DIR}
    get remote file    ${remotedumpfile}    ${destfile}
    delete remote files    ${remotedumpfile}

Get ConnectTimesIdentifier
    [Arguments]    ${mteConfigFile}
    [Documentation]    get the ConnectTimesIdentifier (feed times RIC) from venue config file.
    ...    returns ConnectTimesIdentifier.
    ...
    ...    Note that there are currently 2 different config file formats - MFDS and HKFE. MFDS may be the "old" way so will check that format if the initial search attempt fails.
    ...
    ...    Config file examples:
    ...
    ...    HKFE:
    ...    <Inputs>
    ...    <Channels type="multistring">
    ...    <Z>HKF02M</Z>
    ...    </Channels>
    ...    <HKF02M>
    ...    <DictionaryFile>/ThomsonReuters/config/EDFFieldDictionary</DictionaryFile>
    ...    <FHRealtimeLine>
    ...    <ConnectTimesIdentifier>HKF%FD01</ConnectTimesIdentifier>
    ...    <HighActivityTimesIdentifier>HKF%TRD01</HighActivityTimesIdentifier>
    ...
    ...
    ...    MFDS:
    ...    <!-- Input Channels -->
    ...    <ConnectTimesRIC>MUT%FD01</ConnectTimesRIC>
    ...    <HighActivityTimesRIC>MUT%TRD01</HighActivityTimesRIC>
    ...    <Inputs>
    ${connectTimesIdentifier}=    get MTE config value    ${mteConfigFile}    Inputs    ${MTE}    FHRealtimeLine    ConnectTimesIdentifier
    return from keyword if    '${connectTimesIdentifier}' != 'NOT FOUND'    ${connectTimesIdentifier}
    ${connectTimesIdentifier}=    get MTE config value    ${mteConfigFile}    ConnectTimesRIC
    return from keyword if    '${connectTimesIdentifier}' != 'NOT FOUND'    ${connectTimesIdentifier}
    FAIL    No ConnectTimesIdentifier found in venue config file: ${mteConfigFile}
    [Return]    ${connectTimesIdentifier}

Get HighActivityTimesIdentifier
    [Arguments]    ${mteConfigFile}
    [Documentation]    get the HighActivityTimesIdentifier (trade times RIC) from venue config file.
    ...    returns HighActivityTimesIdentifier.
    ...
    ...    Note that there are currently 2 different config file formats - MFDS and HKFE. MFDS may be the "old" way so will check that format if the initial search attempt fails.
    ...
    ...    Config file examples:
    ...
    ...    HKFE:
    ...    <Inputs>
    ...    <Channels type="multistring">
    ...    <Z>HKF02M</Z>
    ...    </Channels>
    ...    <HKF02M>
    ...    <DictionaryFile>/ThomsonReuters/config/EDFFieldDictionary</DictionaryFile>
    ...    <FHRealtimeLine>
    ...    <ConnectTimesIdentifier>HKF%FD01</ConnectTimesIdentifier>
    ...    <HighActivityTimesIdentifier>HKF%TRD01</HighActivityTimesIdentifier>
    ...
    ...
    ...    MFDS:
    ...    <!-- Input Channels -->
    ...    <ConnectTimesRIC>MUT%FD01</ConnectTimesRIC>
    ...    <HighActivityTimesRIC>MUT%TRD01</HighActivityTimesRIC>
    ...    <Inputs>
    ${highActivityTimesIdentifier}=    get MTE config value    ${mteConfigFile}    Inputs    ${MTE}    FHRealtimeLine    HighActivityTimesIdentifier
    return from keyword if    '${highActivityTimesIdentifier}' != 'NOT FOUND'    ${highActivityTimesIdentifier}
    ${highActivityTimesIdentifier}=    get MTE config value    ${mteConfigFile}    HighActivityTimesRIC
    return from keyword if    '${highActivityTimesIdentifier}' != 'NOT FOUND'    ${highActivityTimesIdentifier}
    FAIL    No HighActivityTimesIdentifier found in venue config file: ${mteConfigFile}
    [Return]    ${highActivityTimesIdentifier}

Get Domain Names
    [Arguments]    ${mteConfigFile}
    [Documentation]    get the Domain names from venue config file.
    ...    returns a list of Domain names.
    ${serviceName}    Get FMS Service Name    ${MTE}
    ${domainList}    get MTE config list    ${mteConfigFile}    FMS    ${serviceName}    Domain    Z
    [Return]    @{domainList}

Get FMS Service Name
    [Arguments]    ${mte}
    [Documentation]    get the Service name from statBlock
    ${categories}=    get stat blocks for category    ${mte}    FMS
    ${services}=    get matches workaround    ${categories}    Service_*
    ${serviceName}    get stat block field    ${mte}    ${services[0]}    serviceName
    [Return]    ${serviceName}

Get GMT Offset And Apply To Datetime
    [Arguments]    ${dstRicName}    ${year}    ${month}    ${day}    ${hour}    ${min}
    ...    ${sec}
    [Documentation]    Get GMT Offset and apply to datetime:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1698
    ${normalGmtOffset}    get stat block field    ${MTE}    ${dstRicName}    normalGMTOffset
    ${localDatetimeYear}    ${localDatetimeMonth}    ${localDatetimeDay}    ${localDatetimeHour}    ${localDatetimeMin}    ${localDatetimeSec}    add seconds to date
    ...    ${year}    ${month}    ${day}    ${hour}    ${min}    ${sec}
    ...    ${normalGmtOffset}
    [Return]    ${localDatetimeYear}    ${localDatetimeMonth}    ${localDatetimeDay}    ${localDatetimeHour}    ${localDatetimeMin}    ${localDatetimeSec}

Get MTE Config File
    [Arguments]    ${venue_dir}    ${mte_config_file}    ${dst_config_file}
    ${lowercase_filename}    convert to lowercase workaround    ${mte_config_file}
    ${res}=    search remote files    ${venue_dir}    ${lowercase_filename}    recurse=${True}
    Length Should Be    ${res}    1    ${lowercase_filename} file not found (or multiple files found).
    get remote file    ${res[0]}    ${dst_config_file}

Get Preferred Domain
    [Arguments]    ${mteConfigFile}    @{preferenceOrder}
    [Documentation]    return the first Domain in the preferenceOrder list that exists in the venue config file.
    ...
    ...    If the caller does not specify a list, the following default list is used:
    ...    MARKET_BY_ORDER, MARKET_BY_PRICE, MARKET_PRICE
    ...
    ...    Examples:
    ...    ${domain}= | get preferred Domain
    ...    ${domain}= | get preferred Domain | MARKET_BY_PRICE | MARKET_PRICE | MARKET_BY_ORDER
    Run Keyword If    len(${preferenceOrder})==0    append to list    ${preferenceOrder}    MARKET_BY_ORDER    MARKET_BY_PRICE    MARKET_PRICE
    ${domainList}=    Get Domain Names    ${mteConfigFile}
    : FOR    ${domain}    IN    @{preferenceOrder}
    \    ${match}=    get matches workaround    ${domainList}    ${domain}
    \    Return From Keyword If    ${match}    ${domain}
    FAIL    No preferred domain ${preferenceOrder} found in domain list ${domainList}
    [Return]    ${domain}

Get RIC From MTE Cache
    [Arguments]    ${mte}    ${no_ric}=1    ${domain}=MarketPrice
    [Documentation]    Getting a list of ric names from MTE cache dump given no. of ric and domain required
    Dumpcache And Copyback Result    ${mte}    ${LOCAL_TMP_DIR}/cache_dump.csv
    @{rics_list}=    get ric names from cachedump    ${LOCAL_TMP_DIR}/cache_dump.csv    ${no_ric}    ${domain}
    Remove Files    ${LOCAL_TMP_DIR}/cache_dump.csv
    [Return]    @{rics_list}

Get RIC List From StatBlock
    [Arguments]    ${mte}    ${ricType}
    [Documentation]    Get RIC name from statBlock.
    ...    Valid choices are: 'Closing Run', 'DST', 'Feed Time', 'Holiday', 'Trade Time'
    ${ricList}=    Run Keyword if    '${ricType}'=='Closing Run'    get stat blocks for category    ${mte}    ClosingRun
    Return from keyword if    '${ricType}'=='Closing Run'    ${ricList}
    ${ricList}=    Run Keyword if    '${ricType}'=='DST'    get stat blocks for category    ${mte}    DST
    Return from keyword if    '${ricType}'=='DST'    ${ricList}
    ${ricList}=    Run Keyword if    '${ricType}'=='Feed Time'    get stat blocks for category    ${mte}    FeedTimes
    Return from keyword if    '${ricType}'=='Feed Time'    ${ricList}
    ${ricList}=    Run Keyword if    '${ricType}'=='Holiday'    get stat blocks for category    ${mte}    Holidays
    Return from keyword if    '${ricType}'=='Holiday'    ${ricList}
    ${ricList}=    Run Keyword if    '${ricType}'=='Trade Time'    get stat blocks for category    ${mte}    TradeTimes
    Return from keyword if    '${ricType}'=='Trade Time'    ${ricList}
    FAIL    RIC not found. Valid choices are: 'Closing Run', 'DST', 'Feed Time', 'Holiday', 'Trade Time'

Persist File Should Exist
    [Arguments]    ${mte}    ${venuedir}
    ${res}=    search remote files    ${venuedir}    PERSIST_${mte}.DAT    recurse=${True}
    Length Should Be    ${res}    1    PERSIST_${mte}.DAT file not found (or multiple files found).
    Comment    Currently, GATS does not provide the Venue name, so the pattern matching Keywords must be used. If GATS provides the Venue name, then "remote file should not exist" Keywords could be used here.

Set DST Datetime In EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${ric}    ${domain}    ${startDateTime}    ${endDateTime}
    [Documentation]    Set DST datetime in EXL:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1642
    modify EXL    ${srcFile}    ${dstFile}    ${ric}    ${domain}    <it:DS_START>${startDateTime}</it:DS_START>
    modify EXL    ${dstFile}    ${dstFile}    ${ric}    ${domain}    <it:DS_END>${endDateTime}</it:DS_END>

Set Feed Time In EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${ric}    ${domain}    ${startTime}    ${endTime}
    ...    ${feedDay}=THU
    [Documentation]    Set feed time in EXL:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1646
    modify EXL    ${srcFile}    ${dstFile}    ${ric}    ${domain}    <it:${feedDay}_FD_OPEN>${startTime}</it:${feedDay}_FD_OPEN>
    modify EXL    ${dstFile}    ${dstFile}    ${ric}    ${domain}    <it:${feedDay}_FD_CLOSE>${endTime}</it:${feedDay}_FD_CLOSE>

Set Holiday Datetime In EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${ric}    ${domain}    ${startDateTime}    ${endDateTime}
    ...    ${holidayIndex}=00
    [Documentation]    Set holiday datetime in EXL:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1639
    blank out holidays    ${srcFile}    ${dstFile}
    modify EXL    ${dstFile}    ${dstFile}    ${ric}    ${domain}    <it:HLY${holidayIndex}_START_TIME>${startDateTime}</it:HLY${holidayIndex}_START_TIME>
    modify EXL    ${dstFile}    ${dstFile}    ${ric}    ${domain}    <it:HLY${holidayIndex}_END_TIME>${endDateTime}</it:HLY${holidayIndex}_END_TIME>

Set RIC In EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${ric}    ${domain}    ${newRIC}
    [Documentation]    Set RIC in EXL:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1649
    modify EXL    ${srcFile}    ${dstFile}    ${ric}    ${domain}    <it:RIC>${newRIC}</it:RIC>

Set Trade Time In EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${ric}    ${domain}    ${startTime}    ${endTime}
    ...    ${tradeDay}=THU
    [Documentation]    Set trade time in EXL:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1645
    modify EXL    ${srcFile}    ${dstFile}    ${ric}    ${domain}    <it:${tradeDay}_TR_OPEN>${startTime}</it:${tradeDay}_TR_OPEN>
    modify EXL    ${dstFile}    ${dstFile}    ${ric}    ${domain}    <it:${tradeDay}_TR_CLOSE>${endTime}</it:${tradeDay}_TR_CLOSE>

Start Capture MTE Output
    [Arguments]    ${mte}    ${filename}=/tmp/capture.pcap    ${ddn}=DDNA
    [Documentation]    Start capture MTE output
    ${interfaceName}=    get interface name by alias    ${ddn}
    @{IpAndPort}=    get multicast address and port for mte    ${mte}
    start capture packets    ${filename}    ${interfaceName}    @{IpAndPort}

Start MTE
    [Arguments]    ${mte}
    [Documentation]    Start the MTE and wait for initialization to complete.
    ${result}=    find processes by pattern    MTE -c ${mte}
    Run keyword if    '${result}'!=''    wait for HealthCheck    ${mte}    IsLinehandlerStartupComplete    waittime=5    timeout=600
    Return from keyword if    '${result}'!=''
    run commander    process    start ${mte}
    wait for process to exist    MTE -c ${mte}
    wait for HealthCheck    ${mte}    IsLinehandlerStartupComplete    waittime=5    timeout=600

Stop Capture MTE Output
    [Arguments]    ${instanceName}    ${waittime}=5    ${timeout}=300
    [Documentation]    Stop catpure MTE output
    wait for capture to complete    ${instanceName}    ${waittime}    ${timeout}
    stop capture packets

Stop MTE
    [Arguments]    ${mte}
    run commander    process    stop ${mte}
    wait for process to not exist    MTE -c ${mte}

Validate MTE Capture Against FIDFilter
    [Arguments]    ${pcapfile}    ${contextId}    ${constit}
    [Documentation]    validate MTE pcap capture against content in FIDFilter.txt
    get remote file    ${pcapfile}    ${LOCAL_TMP_DIR}/capture_local.pcap
    verify fid in fidfilter by contextId and constit against pcap    ${LOCAL_TMP_DIR}/capture_local.pcap    ${contextId}    ${constit}    ${VENUE_DIR}    ${DAS_DIR}
    delete remote files    ${pcapfile}
    Remove Files    ${LOCAL_TMP_DIR}/capture_local.pcap
    [Teardown]

Validate MTE Capture Within FID Range For Constituent
    [Arguments]    ${pcapfile}    ${constit}    @{fid_range}
    get remote file    ${pcapfile}    ${LOCAL_TMP_DIR}/capture_local.pcap
    verify fid in range by constit against pcap    ${LOCAL_TMP_DIR}/capture_local.pcap    ${DAS_DIR}    ${constit}    @{fid_range}
    delete remote files    ${pcapfile}
    Remove Files    ${LOCAL_TMP_DIR}/capture_local.pcap

Wait For FMS Reorg
    [Arguments]    ${mte}    ${waittime}=5    ${timeout}=600
    [Documentation]    Wait for the MTE to complete the FMS reorg.
    wait for HealthCheck    ${mte}    FMSStartupReorgHasCompleted    ${waittime}    ${timeout}

Load Single EXL File
    [Arguments]    ${exlFile}    ${service}    ${headendIP}    ${headendPort}=25000    @{optargs}
    [Documentation]    Loads a single EXL file using FMSCMD. The EXL file must be on the local machine. Inputs for this keyword are the EXL Filename including the path, the FMS service and the headend's IP and Port. \ The default parameter for the port value is 25000.
    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd    ${headendIP}    ${headendPort}    ${LOCAL_FMS_BIN}
    ...    Process    --Services ${service}    --InputFile "${exlFile}"    @{optargs}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Load All EXL Files
    [Arguments]    ${service}    ${headendIP}    ${headendPort}=25000
    [Documentation]    Loads all EXL files for a given service using FMSCMD. The FMS files for the given service must be on the local machine. The input parameters to this keyword are the FMS service name and headend's IP and Port. \ The default parameter for the port value is 25000.
    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd With Headend    ${headendIP}    ${headendPort}    ${LOCAL_FMS_BIN}
    ...    Recon    ${EMPTY}    ${EMPTY}    ${EMPTY}    ${service}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS files \ ${returnedStdOut}

Verify RIC In MTE Cache Dump
    [Arguments]    ${mte}    ${ric}
    Dumpcache And Copyback Result    ${mte}    ${LOCAL_TMP_DIR}/cache_dump.csv
    verify ric in cachedump    ${LOCAL_TMP_DIR}/cache_dump.csv    ${ric}
    Remove Files    ${LOCAL_TMP_DIR}/cache_dump.csv
