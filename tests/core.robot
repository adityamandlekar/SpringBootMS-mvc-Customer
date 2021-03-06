*** Settings ***
Documentation     The common set of Robot imports and keywords for Thunderdome.
...               This file should be imported as a Resource in each Thunderdome test suite.
Library           Collections
Library           OperatingSystem
Library           String
Library           DateTime
Library           linuxtools/dataview.py
Library           linuxtools/hostmanager.py
Library           localtools/das.py
Library           localtools/fmscmd.py
Library           localtools/pmat.py
Library           localtools/scwcli.py
Library           cache
Library           CHEprocess
Library           configfiles
Library           exlfiles
Library           fidfilterfile
Library           LinuxCoreUtilities
Library           LinuxFSUtilities
Library           logfiles
Library           messages
Library           persistfiles
Library           statblock
Library           WinFSUtilities
Library           utilpath
Library           xmlutilities

*** Keywords ***
Case Teardown
    [Arguments]    @{tmpfiles}
    [Documentation]    Do test case teardown, e.g. remove temp files.
    Run Keyword if Test Passed    Remove Files    @{tmpfiles}

Config Change For Recon On MTE
    [Documentation]    Some production setting in MTE config file need to be adjusted before we could successfully carry out functional test.
    ...
    ...
    ...    Remark:
    ...    Need to restart MTE before the changes become effective
    ${remoteCfgFile}    ${backupCfgFile}    backup remote cfg file    ${REMOTE_MTE_CONFIG_DIR}    ${MTE_CONFIG}
    Set Suite Variable    ${LOCAL_MTE_CONFIG_FILE}    ${None}
    ${localCfgFile}=    Get MTE Config File
    set value in MTE cfg    ${localCfgFile}    HiActTimeLimit    ${999999}
    set value in MTE cfg    ${localCfgFile}    LoActTimeLimit    ${999999}
    set value in MTE cfg    ${localCfgFile}    HiActTimeOut    ${999999}    skip    Inputs    *
    set value in MTE cfg    ${localCfgFile}    LoActTimeOut    ${999999}    skip    Inputs    *
    Comment    set value in MTE cfg    ${localCfgFile}    ResendFM    ${0}    add    FMS
    set value in MTE cfg    ${localCfgFile}    FailoverPublishRate    ${0}    add    BackgroundRebuild
    Put Remote File    ${localCfgFile}    ${remoteCfgFile}

Create Unique RIC Name
    [Arguments]    ${text}=
    [Documentation]    Create a unique RIC name. Format is 'TEST' + text param + current datetime string (YYYYMMDDHHMMSS}.
    ...    Max length of text param is 14 (18 chars are added and RIC max length is 32 chars)
    Run Keyword If    len('${text}')>14    FAIL    Max length for text string is 14
    ${dt}=    get date and time
    ${ric}=    set variable    TEST${text}${dt[0]}${dt[1]}${dt[2]}${dt[3]}${dt[4]}${dt[5]}
    [Return]    ${ric}

Delete Persist Files
    delete remote files matching pattern    ${VENUE_DIR}    PERSIST_${MTE}.DAT*    recurse=${True}
    ${res}=    search remote files    ${VENUE_DIR}    PERSIST_${MTE}.DAT    recurse=${True}
    Should Be Empty    ${res}
    Comment    Currently, GATS does not provide the Venue name, so the pattern matching Keywords must be used. If GATS provides the Venue name, then "delete remote file" and "remote file should not exist" Keywords could be used here.

Dictionary of Dictionaries Should Be Equal
    [Arguments]    ${dict1}    ${dict2}
    [Documentation]    Verify that two dictionaries, where the values are also dictionaries, match.
    ...    First verify the keys between the two dictionaries match, then loop through each sub-dictionary and verify they match.
    ...    Although the Robot 'Should Be Equal' KW works for nested dictionaries, the error message generated when they do not match does not pinpoint the differences.
    @{keys1}=    Get Dictionary Keys    ${dict1}
    @{keys2}=    Get Dictionary Keys    ${dict2}
    Should Be Equal    ${keys1}    ${keys2}
    : FOR    ${key}    IN    @{keys1}
    \    Dictionaries Should Be Equal    ${dict1['${key}']}    ${dict2['${key}']}

Disable MTE Clock Sync
    [Documentation]    If running on a vagrant VirtualBox, disable the VirtualBox Guest Additions service. \ This will allow the test to change the clock on the VM. \ Otherwise, VirtualBox will immediately reset the VM clock to keep it in sync with the host machine time.
    ${result}=    Execute Command    if [ -f /etc/init.d/vboxadd-service ]; then service vboxadd-service stop; fi

Dump Persist File To Text
    [Arguments]    @{optargs}
    [Documentation]    Run PMAT on control PC and return the \ persist text dump file.
    ...    optarg could be ---ric <ric> | --sic <sic> | --domain <domain> |--fids <comma-delimited-fid-list> | --meta <meta> | --encode <0|1. \ Default to 0 > | --ffile <path to XQuery-syntax-FilterFile>
    ...
    ...    Note: <domain> = 0 for MarketByOrder, 1 for MarketByPrice, 2 for MarketMaker, 3 for MarketPrice, 4 for symbolList.
    ...    \ \ \ \ <ric> = a single ric or a wide-card
    ...
    ...    PMAT Guide: https://thehub.thomsonreuters.com/docs/DOC-110727
    ${localPersistFile}=    set variable    ${LOCAL_TMP_DIR}${/}local_persist.dat
    ${remotePersist}=    search remote files    ${VENUE_DIR}    PERSIST_${MTE}.DAT    ${True}
    Should Be True    len(${remotePersist}) ==1
    get remote file    ${remotePersist[0]}    ${localPersistFile}
    ${random}=    Generate Random String    4    [NUMBERS]
    ${pmatDumpfile}=    set variable    ${LOCAL_TMP_DIR}${/}pmatDump${random}.txt
    Run PMAT    dump    --dll Schema_v7.dll    --db ${localPersistFile}    --oformat text    --outf ${pmatDumpfile}    @{optargs}
    Remove Files    ${localPersistFile}
    [Return]    ${pmatDumpfile}

Dump Persist File To XML
    [Arguments]    @{optargs}
    [Documentation]    Run PMAT on control PC and return the \ persist xml dump file.
    ...    optarg could be ---ric <ric> | --sic <sic> | --domain <domain> |--fids <comma-delimited-fid-list> | --meta <meta> | --encode <0|1. \ Default to 0 > | --ffile <path to XQuery-syntax-FilterFile>
    ...
    ...    Note: <domain> = 0 for MarketByOrder, 1 for MarketByPrice, 2 for MarketMaker, 3 for MarketPrice, 4 for symbolList.
    ...    \ \ \ \ <ric> = a single ric or a wide-card
    ...
    ...    PMAT Guide: https://thehub.thomsonreuters.com/docs/DOC-110727
    ${localPersistFile}=    set variable    ${LOCAL_TMP_DIR}${/}local_persist.dat
    ${remotePersist}=    search remote files    ${VENUE_DIR}    PERSIST_${MTE}.DAT    ${True}
    Should Be True    len(${remotePersist}) ==1
    get remote file    ${remotePersist[0]}    ${localPersistFile}
    ${random}=    Generate Random String    4    [NUMBERS]
    ${pmatXmlDumpfile}=    set variable    ${LOCAL_TMP_DIR}${/}pmatDump${random}.xml
    Run PMAT    dump    --dll Schema_v7.dll    --db ${localPersistFile}    --outf ${pmatXmlDumpfile}    @{optargs}
    Remove Files    ${localPersistFile}
    [Return]    ${pmatXmlDumpfile}

Extract ICF
    [Arguments]    ${ric}    ${domain}    ${extractFile}    ${serviceName}
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    extract    --RIC ${ric}
    ...    --Domain ${domain}    --ExcludeNullFields true    --HandlerName ${MTE}    --OutputFile ${extractFile}    --Services ${serviceName}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Generate PCAP File Name
    [Arguments]    ${service}    ${testCase}    ${playbackBindSide}=A    @{keyValuePairs}
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/RECON-19
    ...
    ...    Generate the file name based on service name, test case, input key/value pairs and playback side designation --- default to A side
    ...
    ...    Example:
    ...    MFDS-Testcase-B.pcap
    ...    TDDS_BDDS-TransientGap-domain=MARKET_PRICE-A.pcap
    ${pcapFileName}=    Catenate    SEPARATOR=-    ${service}    ${testCase}    @{keyValuePairs}    ${playbackBindSide}
    ${pcapFileName} =    Catenate    SEPARATOR=    ${PLAYBACK_PCAP_DIR}    ${pcapFileName}    .pcap
    ${pcapFileName} =    Replace String    ${pcapFileName}    ${space}    _
    [Return]    ${pcapFileName}

Get All State Processing RICs
    ${closingrunRicList}=    Get RIC List From StatBlock    Closing Run
    ${DSTRicList}=    Get RIC List From StatBlock    DST
    ${feedTimeRicList}=    Get RIC List From StatBlock    Feed Time
    ${holidayRicList}=    Get RIC List From StatBlock    Holiday
    ${tradeTimeRicList}=    Get RIC List From StatBlock    Trade Time
    ${StateProcessRicList}    Combine Lists    ${closingrunRicList}    ${DSTRicList}    ${feedTimeRicList}    ${holidayRicList}    ${tradeTimeRicList}
    [Return]    ${StateProcessRicList}

Get Configure Values
    [Arguments]    @{configList}
    [Documentation]    Get configure items value from MTE config file like StartOfDayTime, EndOfDayTime, RolloverTime....
    ...    Returns a array with configure item value.
    ${mteConfigFile}=    Get MTE Config File
    ${retArray}=    Create List
    : FOR    ${configName}    IN    @{configList}
    \    ${configValue}=    get MTE config value    ${mteConfigFile}    ${configName}
    \    Append To List    ${retArray}    ${configValue}
    [Return]    ${retArray}

Get ConnectTimesIdentifier
    [Documentation]    Get the combined list of ConnectTimesIdentifier (feed times RIC) from all of the InputPortStatsBlock_* blocks.
    ...
    ...    Returns a list of ConnectTimesIdentifier(s).
    ${allConnectTimeIdentifiers}=    Create List
    @{blocks}=    Get Stat Blocks For Category    ${MTE}    InputLineStats
    : FOR    ${block}    IN    @{blocks}
    \    ${connectTimesIdentifier}=    Get Stat Block Field    ${MTE}    ${block}    connectTimesIdentifier
    \    @{retList}=    Split String    ${connectTimesIdentifier}    ,
    \    Append To List    ${allConnectTimeIdentifiers}    @{retList}
    ${allConnectTimeIdentifiers}=    Remove Duplicates    ${allConnectTimeIdentifiers}
    Should Not Be Empty    ${allConnectTimeIdentifiers}    No ConnectTimesIdentifier found.
    [Return]    ${allConnectTimeIdentifiers}

Get Critical Process Config Info
    [Documentation]    Get the configuration information for the list of processes monitored by CritProcMon.
    ...
    ...    Returns a two dimensional array with process name, DownTime threshold and UpTime threshold, e.g.
    ...    [FMSClient,0,20], [NetConStat,0, 20], ...
    ${fileName}=    Set Variable    CritProcMon.xml
    ${remoteFile}=    Search Remote Files    ${BASE_DIR}    ${fileName}    recurse=${True}
    Length Should Be    ${remoteFile}    1    ${filename} file not found (or multiple files found).
    ${localFile}=    Set Variable    ${LOCAL_TMP_DIR}${/}${fileName}
    Get Remote File    ${remoteFile[0]}    ${localFile}
    @{critProcInfo}=    Get XML Text For Node    ${localFile}    CriticalProcesses
    Remove File    ${localFile}
    Should Not Be Empty    ${critProcInfo}
    ${retArray}=    Create List
    : FOR    ${procInfo}    IN    @{critProcInfo}
    \    ${info}=    Split String    ${procInfo}    |
    \    Append To List    ${retArray}    ${info}
    [Return]    ${retArray}

Get Domain Names
    [Arguments]    ${mteConfigFile}
    [Documentation]    get the Domain names from venue config file.
    ...    returns a list of Domain names.
    ${serviceName}    Get FMS Service Name
    ${domainList}    get MTE config list by path    ${mteConfigFile}    FMS    ${serviceName}    Domain
    [Return]    @{domainList}

Get FID Values From Refresh Request
    [Arguments]    ${ricList}    ${domain}
    [Documentation]    Get the value for all non-blank FIDs for the RICs listed in the specfied file on the remote machine.
    ...
    ...    Returns a dictionary with key=RIC, value = {sub-dictionary with key=FID NAME and value=FID value}
    ${result}=    Send TRWF2 Refresh Request No Blank FIDs    ${ricList}    ${domain}    -RL 1
    ${ricDict}=    Convert DataView Response to MultiRIC Dictionary    ${result}
    [Return]    ${ricDict}

Get FIDFilter File
    [Documentation]    Get the FIDFilter.txt for this venue from the TD Box.
    ...
    ...    There are separate FIDFilter.txt files for each venue on machines with multiple venues.
    ...    We do not have the venue name, so we use the FIDFilter.txt file in the same directory as the MTE configuration file.
    ...
    ...    1. The file will be saved at Control PC and only removed at Suite Teardown
    ...    2. Suite Variable ${LOCAL_FIDFILTER_FILE} has created to store the fullpath of the config file at Control PC
    ${localFile}=    Get Variable Value    ${LOCAL_FIDFILTER_FILE}
    Return From Keyword If    r'${localFile}' != 'None'    ${localFile}
    ${fidfilterFile}=    Set Variable    FIDFilter.txt
    Remote File Should Exist    ${REMOTE_MTE_CONFIG_DIR}/${fidfilterFile}
    ${localFile}=    Set Variable    ${LOCAL_TMP_DIR}${/}${fidfilterFile}
    get remote file    ${REMOTE_MTE_CONFIG_DIR}/${fidfilterFile}    ${localFile}
    Set Suite Variable    ${LOCAL_FIDFILTER_FILE}    ${localFile}
    [Return]    ${localFile}

Get FMS Service Name
    [Documentation]    get the Service name from statBlock
    ${categories}=    get stat blocks for category    ${MTE}    FMS
    ${services}=    Get Matches    ${categories}    Service_*
    ${serviceName}    get stat block field    ${MTE}    ${services[0]}    serviceName
    [Return]    ${serviceName}

Get GMT Offset And Apply To Datetime
    [Arguments]    ${dstRicName}    ${year}    ${month}    ${day}    ${hour}    ${min}
    ...    ${sec}
    [Documentation]    Get GMT Offset and apply to datetime:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1698
    ${currentGmtOffset}    get stat block field    ${MTE}    ${dstRicName}    currentGMTOffset
    ${newdate}    add time to date    ${year}-${month}-${day} ${hour}:${min}:${sec}    ${currentGmtOffset} second
    ${localDatetimeYear}    ${localDatetimeMonth}    ${localDatetimeDay}    ${localDatetimeHour}    ${localDatetimeMin}    ${localDatetimeSec}    get Time
    ...    year month day hour min sec    ${newdate}
    [Return]    ${localDatetimeYear}    ${localDatetimeMonth}    ${localDatetimeDay}    ${localDatetimeHour}    ${localDatetimeMin}    ${localDatetimeSec}

Get HighActivityTimesIdentifier
    [Documentation]    Get the combined list of HighActivityTimesIdentifier (trade times RIC) from all of the InputPortStatsBlock_* blocks.
    ...
    ...    Returns a list of HighActivityTimesIdentifier(s).
    ${allHighActivityTimesIdentifiers}=    Create List
    @{blocks}=    Get Stat Blocks For Category    ${MTE}    InputLineStats
    : FOR    ${block}    IN    @{blocks}
    \    ${HighActivityTimesIdentifier}=    Get Stat Block Field    ${MTE}    ${block}    highactTimesIdentifier
    \    @{retList}=    Split String    ${HighActivityTimesIdentifier}    ,
    \    Append To List    ${allHighActivityTimesIdentifiers}    @{retList}
    ${allHighActivityTimesIdentifiers}=    Remove Duplicates    ${allHighActivityTimesIdentifiers}
    Should Not Be Empty    ${allHighActivityTimesIdentifiers}    No highactTimesIdentifier found.
    [Return]    ${allHighActivityTimesIdentifiers}

Get Label IDs
    [Documentation]    Get the list of labelIDs from MTE config file on current machine.
    ...    The LabelID may be different across machines, so use config files from current machine.
    Set Suite Variable    ${LOCAL_MTE_CONFIG_FILE}    ${None}
    ${localVenueConfig}=    get MTE config file
    @{labelIDs}=    get MTE config list by section    ${localVenueConfig}    Publishing    LabelID
    [Return]    @{labelIDs}

Get Mangling Config File
    [Documentation]    Get the manglingConfiguration.xml for this venue from the TD Box.
    ...
    ...    There are separate manglingConfiguration.xml files for each venue on machines with multiple venues.
    ...    We do not have the venue name, so we use the manglingConfiguration.xml file in the same directory as the MTE configuration file.
    ...
    ...    1. The file will be saved at Control PC and only removed at Suite Teardown
    ...    2. Suite Variable ${LOCAL_MANGLING_CONFIG_FILE} has created to store the fullpath of the config file at Control PC
    ${localFile}=    Get Variable Value    ${LOCAL_MANGLING_CONFIG_FILE}
    Return From Keyword If    r'${localFile}' != 'None'    ${localFile}
    ${manglingFile}=    Set Variable    manglingConfiguration.xml
    Remote File Should Exist    ${REMOTE_MTE_CONFIG_DIR}/${manglingFile}
    ${localFile}=    Set Variable    ${LOCAL_TMP_DIR}${/}${manglingFile}
    get remote file    ${REMOTE_MTE_CONFIG_DIR}/${manglingFile}    ${localFile}
    Set Suite Variable    ${LOCAL_MANGLING_CONFIG_FILE}    ${localFile}
    [Return]    ${localFile}

Get MTE Config File
    [Documentation]    Get the MTE config file from the remote machine and save it as a local file.
    ...    If we already have the local file, just return the file name without copying the remote file again.
    ${localFile}=    Get Variable Value    ${LOCAL_MTE_CONFIG_FILE}
    Return From Keyword If    r'${localFile}' != 'None'    ${localFile}
    ${localFile}=    Set Variable    ${LOCAL_TMP_DIR}${/}${MTE_CONFIG}
    get remote file    ${REMOTE_MTE_CONFIG_DIR}/${MTE_CONFIG}    ${localFile}
    Set Suite Variable    ${LOCAL_MTE_CONFIG_FILE}    ${localFile}
    [Return]    ${localFile}

Get MTE Machine Time Offset
    [Documentation]    Get the offset from local machine for the current time on the MTE machine. Recon changes the machine time to start of feed time, so MTE machine time may not equal real time. this local time can be not GMT time, since the only offset will be used, if local machine time is real life time, then MTE machine time can be restored to real life time by the offset.
    ${currDateTime}=    get date and time
    ${localTime}=    Get Current Date    exclude_millis=True
    ${MTEtime}=    Convert Date    ${currDateTime[0]}-${currDateTime[1]}-${currDateTime[2]} ${currDateTime[3]}:${currDateTime[4]}:${currDateTime[5]}    result_format=datetime
    ${MTETimeOffset}=    Subtract Date From Date    ${MTEtime}    ${localTime}
    [Return]    ${MTETimeOffset}

Get Playback NIC For PCAP File
    [Arguments]    ${pcapFile}
    ${partialFile}=    Fetch From Right    ${pcapFile}    -
    ${sideInfo}    Fetch From Left    ${partialFile}    .
    ${uppercaseName} =    Convert To Uppercase    ${sideInfo}
    ${nicBindTo}    Run Keyword If    '${uppercaseName}' == 'A'    set variable    ${PLAYBACK_BIND_IP_A}
    ...    ELSE IF    '${uppercaseName}' == 'B'    set variable    ${PLAYBACK_BIND_IP_B}
    ...    ELSE    Fail    pcap file name must end with Side designation, e.g. service-testcase-A.pcap or service-testcase-B.pcap
    ${intfName}=    get interface name by ip    ${nicBindTo}
    Should Not be Empty    ${intfName}
    [Return]    ${intfName}

Get Preferred Domain
    [Arguments]    @{preferenceOrder}
    [Documentation]    return the first Domain in the preferenceOrder list that exists in the venue config file.
    ...
    ...    If the caller does not specify a list, the following default list is used:
    ...    MARKET_BY_ORDER, MARKET_BY_PRICE, MARKET_PRICE, MARKET_MAKER
    ...
    ...    Examples:
    ...    ${domain}= | get preferred Domain
    ...    ${domain}= | get preferred Domain | MARKET_BY_PRICE | MARKET_PRICE | MARKET_BY_ORDER | MARKET_MAKER
    Run Keyword If    len(${preferenceOrder})==0    append to list    ${preferenceOrder}    MARKET_BY_ORDER    MARKET_BY_PRICE    MARKET_PRICE
    ...    MARKET_MAKER
    ${mteConfigFile}=    Get MTE Config File
    ${domainList}=    Get Domain Names    ${mteConfigFile}
    : FOR    ${domain}    IN    @{preferenceOrder}
    \    ${match}=    Get Matches    ${domainList}    ${domain}
    \    Return From Keyword If    ${match}    ${domain}
    FAIL    No preferred domain ${preferenceOrder} found in domain list ${domainList}
    [Return]    ${domain}

Get RIC From MTE Cache
    [Arguments]    ${requestedDomain}=${EMPTY}    ${contextID}=${EMPTY}
    [Documentation]    Get a single RIC name (SIC and Publish Key) \ from MTE cache for the specified Domain and contextID.
    ...    If no Domain is specified it will call Get Preferred Domain to get the domain name to use.
    ...    If no contextID is specified, it will use any contextID
    ${preferredDomain}=    Run Keyword If    '${requestedDomain}'=='${EMPTY}' and '${contextID}' =='${EMPTY}'    Get Preferred Domain
    ${domain}=    Set Variable If    '${requestedDomain}'=='${EMPTY}' and '${contextID}' =='${EMPTY}'    ${preferredDomain}    ${requestedDomain}
    ${result}    get RIC fields from cache    1    ${domain}    ${contextID}
    ${ric}=    set variable    ${result[0]['RIC']}
    ${publishKey}=    set variable    ${result[0]['PUBLISH_KEY']}
    [Teardown]
    [Return]    ${ric}    ${publishKey}

Get RIC List From Remote PCAP
    [Arguments]    ${remoteCapture}    ${domain}
    [Documentation]    Extract the unique set of non-system RICs that exist in a remote capture.
    ...
    ...    Returns: The list of RICs.
    ${localCapture}=    set variable    ${LOCAL_TMP_DIR}/local_capture.pcap
    get remote file    ${remoteCapture}    ${localCapture}
    ${ricList}=    Get RICs From PCAP    ${localCapture}    ${domain}
    Should Not Be Empty    ${ricList}    Injected file produced no published RICs
    Remove Files    ${localCapture}
    [Return]    ${ricList}

Get RIC List From StatBlock
    [Arguments]    ${ricType}
    [Documentation]    Get RIC name from statBlock.
    ...    Valid choices are: 'Closing Run', 'DST', 'Feed Time', 'Holiday', 'Trade Time'
    ${ricList}=    Run Keyword if    '${ricType}'=='Closing Run'    get stat blocks for category    ${MTE}    ClosingRun
    Return from keyword if    '${ricType}'=='Closing Run'    ${ricList}
    ${ricList}=    Run Keyword if    '${ricType}'=='DST'    get stat blocks for category    ${MTE}    DST
    Return from keyword if    '${ricType}'=='DST'    ${ricList}
    ${ricList}=    Run Keyword if    '${ricType}'=='Feed Time'    get stat blocks for category    ${MTE}    FeedTimes
    Return from keyword if    '${ricType}'=='Feed Time'    ${ricList}
    ${ricList}=    Run Keyword if    '${ricType}'=='Holiday'    get stat blocks for category    ${MTE}    Holidays
    Return from keyword if    '${ricType}'=='Holiday'    ${ricList}
    ${ricList}=    Run Keyword if    '${ricType}'=='Trade Time'    get stat blocks for category    ${MTE}    TradeTimes
    Return from keyword if    '${ricType}'=='Trade Time'    ${ricList}
    FAIL    RIC not found. Valid choices are: 'Closing Run', 'DST', 'Feed Time', 'Holiday', 'Trade Time'

Get RIC Sample
    [Arguments]    ${domain}
    [Documentation]    Get a single RIC name (SIC and Publish Key) \ exist in both MTE cache and local EXL Files for the specified domain
    ...
    ...
    ...    Remark:
    ...    ${REORG_FROM_FMS_SERVER} is Suite Variable which will be created and initialize in Suite Setup to ${True}
    ...    Every call of "Start MTE" will also reset this variable to ${True}
    ...    ${REORG_FROM_FMS_SERVER} = ${True} indicate that MTE has been sync up its cache from FMS server before.
    ...
    ...    ${REORG_FROM_FMS_SERVER} will set to ${False} after Get RIC Sample as a call of "Load All EXL Files" will used within the KW to sync up the MTE cache with local EXL files.
    ${serviceName}=    Get FMS Service Name
    Run Keyword If    ${REORG_FROM_FMS_SERVER}    Run Keywords    Load All EXL Files    ${serviceName}    ${CHE_IP}
    ...    AND    Wait For FMS Reorg
    ${ric}    ${publishKey}    Get RIC From MTE Cache    ${domain}
    ${EXLfullpath}    Get EXL For RIC    ${domain}    ${serviceName}    ${ric}
    Set Suite Variable    ${REORG_FROM_FMS_SERVER}    ${False}
    [Return]    ${EXLfullpath}    ${ric}    ${publishKey}

Get Sorted Cache Dump
    [Arguments]    ${destfile}    # where will the csv be copied back
    [Documentation]    Dump the MTE cache to a file, sort lines 2 thru end of file, and copy the sorted file to the local temp directory.
    ${remotedumpfile}=    dump cache
    ${sortedfile}=    Set Variable    ${REMOTE_TMP_DIR}/sortedcache.csv
    Execute Command    head -1 ${remotedumpfile} > ${sortedfile}; tail -n +2 ${remotedumpfile} | sort -t',' -k2 >> ${sortedfile}
    get remote file    ${sortedfile}    ${destfile}
    delete remote files    ${remotedumpfile}    ${sortedfile}

Go Into End Feed Time
    [Arguments]    ${serviceName}
    [Documentation]    For all feeds, set end of feed time in 2 minutes. Wait for end of feed time to occur.
    ...    The returned EXL file lists should be used to call Restore EXL Changes at the end of the test.
    ...
    ...    Return:
    ...    ${exlFiles} : list of the exlFiles that were modified by this KW
    ...    ${modifiedExlFiles} : list of the modified exlFiles
    ${secondsBeforeFeedEnd}=    set variable    120
    ${connectTimeRicDomain}=    set variable    MARKET_PRICE
    @{connectTimesIdentifierList}=    Get ConnectTimesIdentifier
    @{modifiedExlFiles}=    Create List
    @{exlFiles}=    Create List
    : FOR    ${connectTimesIdentifier}    IN    @{connectTimesIdentifierList}
    \    ${exlFile}=    get state EXL file    ${connectTimesIdentifier}    ${connectTimeRicDomain}    ${serviceName}    Feed Time
    \    ${exlBasename}=    Fetch From Right    ${exlFile}    ${/}
    \    ${modifiedExlFile}=    set variable    ${LOCAL_TMP_DIR}${/}${exlBasename}
    \    ${count}=    Get Count    ${exlFiles}    ${exlFile}
    \    Run Keyword if    ${count} == 0    append to list    ${exlFiles}    ${exlFile}
    \    Run Keyword if    ${count} == 0    append to list    ${modifiedExlFiles}    ${modifiedExlFile}
    \    Comment    If the file was already modified (multiple RICs in same file), update the modified file.
    \    ${useFile}=    Set Variable If    ${count} == 0    ${exlFile}    ${modifiedExlFile}
    \    @{dstRic}=    get ric fields from EXL    ${exlFile}    ${connectTimesIdentifier}    DST_REF
    \    @{tdBoxDateTime}=    get date and time
    \    @{localDateTime}    Get GMT Offset And Apply To Datetime    @{dstRic}[0]    @{tdBoxDateTime}[0]    @{tdBoxDateTime}[1]    @{tdBoxDateTime}[2]
    \    ...    @{tdBoxDateTime}[3]    @{tdBoxDateTime}[4]    @{tdBoxDateTime}[5]
    \    ${startTime}=    set variable    @{localDateTime}[3]:@{localDateTime}[4]:@{localDateTime}[5]
    \    ${endDateTime}    add time to date    @{localDateTime}[0]-@{localDateTime}[1]-@{localDateTime}[2] ${startTime}    ${secondsBeforeFeedEnd} second
    \    ${endDateTime}    get Time    year month day hour min sec    ${endDateTime}
    \    ${endWeekDay}=    get day of week from date    @{endDateTime}[0]    @{endDateTime}[1]    @{endDateTime}[2]
    \    ${endTime}=    set variable    @{endDateTime}[3]:@{endDateTime}[4]:@{endDateTime}[5]
    \    Set Feed Time In EXL    ${useFile}    ${modifiedExlFile}    ${connectTimesIdentifier}    ${connectTimeRicDomain}    ${EMPTY}
    \    ...    ${endTime}    ${endWeekDay}
    : FOR    ${modifiedExlFile}    IN    @{modifiedExlFiles}
    \    Load Single EXL File    ${modifiedExlFile}    ${serviceName}    ${CHE_IP}
    sleep    ${secondsBeforeFeedEnd}
    [Teardown]
    [Return]    ${exlFiles}    ${modifiedExlFiles}

Inject PCAP File In Background
    [Arguments]    @{pcapFileList}
    [Documentation]    Inject a list of PCAP files in the background on either UDP or TCP transport based on VenueVariables PROTOCOL value.
    ...    Start the injection, but do not wait for it to complete.
    ...    If multiple files are specified, they will run in parallel.
    Run Keyword If    '${PROTOCOL}' == 'UDP'    Inject PCAP File on UDP    no wait    @{pcapFileList}
    ...    ELSE IF    '${PROTOCOL}' == 'TCP'    Inject PCAP File on TCP    no wait    @{pcapFileList}
    ...    ELSE    FAIL    PROTOCOL in VenueVariables must be UDP or TCP.

Inject PCAP File and Wait For Output
    [Arguments]    @{pcapFileList}
    [Documentation]    Inject a list of PCAP files on either UDP or TCP transport based on VenueVariables PROTOCOL value and wait for the resulting message publication to complete.
    ...    If multiple files are specified, they will run in parallel.
    ${remoteCapture}=    set variable    ${REMOTE_TMP_DIR}/capture.pcap
    Start Capture MTE Output    ${remoteCapture}
    Run Keyword If    '${PROTOCOL}' == 'UDP'    Inject PCAP File on UDP    wait    @{pcapFileList}
    ...    ELSE IF    '${PROTOCOL}' == 'TCP'    Inject PCAP File on TCP    wait    @{pcapFileList}
    ...    ELSE    FAIL    PROTOCOL in VenueVariables must be UDP or TCP.
    Stop Capture MTE Output
    [Return]    ${remoteCapture}

Inject PCAP File on TCP
    [Arguments]    ${waitOrNot}    @{pcapFileList}
    [Documentation]    Switch to playback box and start injection of the specified PCAP files on TCP transport. \ Switch back to original box in KW teardown.
    ...    If waitOrNot=='wait', inject the files in sequence, and return after all playback is complete.
    ...    Otherwise start the playback for each file in parallel and return without waiting for the playback to complete.
    ...
    ...    Tests should not call this Keyword directly, they should call 'Inject PCAP File In Background' or 'Inject PCAP File and Wait For Output'.
    ${host}=    get current connection index
    Switch Connection    ${Playback_Session}
    ${cmd}=    Set Variable If    '${waitOrNot}' == 'wait'    Execute Command    Start Command
    : FOR    ${pcapFile}    IN    @{pcapFileList}
    \    remote file should exist    ${pcapFile}
    \    Run Keyword    ${cmd}    PCapPlybk -ifile ${pcapFile} -intf ${PLAYBACK_BIND_IP_A} -port ${TCP_PORT} -pps ${PLAYBACK_PPS} -sendmode tcp -tcptimeout 10
    [Teardown]    Switch Connection    ${host}

Inject PCAP File on UDP
    [Arguments]    ${waitOrNot}    @{pcapFileList}
    [Documentation]    Switch to playback box and start injection of the specified PCAP files on UDP transport. \ Switch back to original box in KW teardown.
    ...    If waitOrNot=='wait', inject the files in sequence, and return after all playback is complete.
    ...    Otherwise start the playback for each file in parallel and return without waiting for the playback to complete.
    ...
    ...    Tests should not call this Keyword directly, they should call 'Inject PCAP File In Background' or 'Inject PCAP File and Wait For Output'.
    ${host}=    get current connection index
    Switch Connection    ${Playback_Session}
    ${cmd}=    Set Variable If    '${waitOrNot}' == 'wait'    Execute Command    Start Command
    : FOR    ${pcapFile}    IN    @{pcapFileList}
    \    remote file should exist    ${pcapFile}
    \    ${intfName}    Get Playback NIC For PCAP File    ${pcapFile}
    \    Run Keyword    ${cmd}    tcpreplay-edit --enet-vlan=del --pps ${PLAYBACK_PPS} --intf1=${intfName} '${pcapFile}'
    [Teardown]    Switch Connection    ${host}

Insert ICF
    [Arguments]    ${insertFile}    ${serviceName}
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    insert    --InputFile ${insertFile}
    ...    --HandlerName ${MTE}    --Services ${serviceName}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Load All EXL Files
    [Arguments]    ${service}    ${headendIP}    @{optargs}
    [Documentation]    Loads all EXL files for a given service using FMSCMD. The FMS files for the given service must be on the local machine. The input parameters to this keyword are the FMS service name and headend's IP.
    wait for HealthCheck    ${MTE}    IsConnectedToFMSClient
    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd    ${headendIP}    Recon    --Services ${service}
    ...    @{optargs}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS files \ ${returnedStdOut}

Load All State EXL Files
    [Arguments]    ${headendIP}=${CHE_IP}
    [Documentation]    Load the state EXL Files (Feed, Trade, and Holiday).
    ...
    ...    If Recon is changed to set ResendFM=0 in the MTE config file, this KW will no longer be needed, as Start MTE will need to load all the EXL files on startup, which will include the state EXL files.
    ${statRicDomain}=    Set Variable    MARKET_PRICE
    ${serviceName}=    get FMS service name
    @{connectTimesIdentifierList}=    Get ConnectTimesIdentifier
    @{highActivityIdentifierList}=    Get HighActivityTimesIdentifier
    @{feedEXLFiles}=    Create List
    @{holidayEXLFiles}=    Create List
    @{tradeEXLFiles}=    Create List
    Comment    Feed Time
    : FOR    ${ric}    IN    @{connectTimesIdentifierList}
    \    ${exlFile}    get state EXL file    ${ric}    ${statRicDomain}    ${serviceName}    Feed Time
    \    Append To List    ${feedEXLFiles}    ${exlFile}
    \    Comment    Get associated holiday EXL
    \    ${unused}    ${holidayRic}    Get DST And Holiday RICs From EXL    ${exlFile}    ${ric}
    \    ${holidayEXL}=    get state EXL file    ${holidayRic}    ${statRicDomain}    ${serviceName}    Holiday
    \    Append To List    ${holidayEXLFiles}    ${holidayEXL}
    Comment    Trade Time
    : FOR    ${ric}    IN    @{highActivityIdentifierList}
    \    ${exlFile}    get state EXL file    ${ric}    ${statRicDomain}    ${serviceName}    Trade Time
    \    Append To List    ${tradeEXLFiles}    ${exlFile}
    \    Comment    Get associated holiday EXL
    \    ${unused}    ${holidayRic}    Get DST And Holiday RICs From EXL    ${exlFile}    ${ric}
    \    ${holidayEXL}=    get state EXL file    ${holidayRic}    ${statRicDomain}    ${serviceName}    Holiday
    \    Append To List    ${holidayEXLFiles}    ${holidayEXL}
    ${feedEXLFiles}    Remove Duplicates    ${feedEXLFiles}
    ${tradeEXLFiles}    Remove Duplicates    ${tradeEXLFiles}
    ${holidayEXLFiles}    Remove Duplicates    ${holidayEXLFiles}
    : FOR    ${exlFile}    IN    @{feedEXLFiles}
    \    Load Single EXL File    ${exlFile}    ${serviceName}    ${headendIP}
    : FOR    ${exlFile}    IN    @{tradeEXLFiles}
    \    Load Single EXL File    ${exlFile}    ${serviceName}    ${headendIP}
    : FOR    ${exlFile}    IN    @{holidayEXLFiles}
    \    Load Single EXL File    ${exlFile}    ${serviceName}    ${headendIP}
    [Teardown]

Load List of EXL Files
    [Arguments]    ${exlFiles}    ${serviceName}    ${headendIP}    @{optargs}
    : FOR    ${exlFiles}    IN    @{exlFiles}
    \    Load Single EXL File    ${exlFiles}    ${serviceName}    ${CHE_IP}    @{optargs}

Load Mangling Settings
    Run Commander    linehandler    lhcommand ${MTE} mangling:refresh_settings
    wait SMF log does not contain    Drop message sent for    waittime=10    timeout=600

Load Single EXL File
    [Arguments]    ${exlFile}    ${service}    ${headendIP}    @{optargs}
    [Documentation]    Loads a single EXL file using FMSCMD. The EXL file must be on the local machine. Inputs for this keyword are the EXL Filename including the path, the FMS service and the headend's IP.
    wait for HealthCheck    ${MTE}    IsConnectedToFMSClient
    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd    ${headendIP}    Process    --Services ${service}
    ...    --InputFile "${exlFile}"    --AllowSICChange true    --AllowRICChange true    @{optargs}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Manual ClosingRun for ClosingRun Rics
    [Arguments]    ${servicename}
    @{closingrunRicList}    Get RIC List From StatBlock    Closing Run
    : FOR    ${closingrunRicName}    IN    @{closingrunRicList}
    \    ${currentDateTime}    get date and time
    \    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd    ${CHE_IP}    ClsRun
    \    ...    --RIC ${closingrunRicName}    --Services ${serviceName}    --Domain MARKET_PRICE    --ClosingRunOperation Invoke    --HandlerName ${MTE}
    \    wait SMF log message after time    ClosingRun.*?CloseItemGroup.*?Found [0-9]* closeable items out of [0-9]* items    ${currentDateTime}    waittime=2    timeout=60

Manual ClosingRun for a RIC
    [Arguments]    ${sampleRic}    ${publishKey}    ${domain}
    Start Capture MTE Output
    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd    ${CHE_IP}    Close    --RIC ${sampleRic}
    ...    --Domain ${domain}
    Wait For Persist File Update
    Stop Capture MTE Output
    ${localcapture}    set variable    ${LOCAL_TMP_DIR}/capture_local.pcap
    get remote file    ${REMOTE_TMP_DIR}/capture.pcap    ${localcapture}
    Run Keyword And Continue On Failure    verify ClosingRun message in messages    ${localcapture}    ${publishKey}
    remove files    ${localcapture}
    delete remote files    ${REMOTE_TMP_DIR}/capture.pcap

MTE Machine Setup
    [Arguments]    ${ip}
    [Documentation]    Create ssh connection to an MTE machine and start the components.
    ${ret}    open connection    host=${ip}    port=${CHE_PORT}    timeout=6
    login    ${USERNAME}    ${PASSWORD}
    Set Common Suite Variables    ${ip}
    setUtilPath
    Config Change For Recon On MTE
    Comment    stop smf
    Comment    Delete Persist Files
    start smf
    Set 24x7 Feed And Trade Time And No Holidays
    Stop MTE
    Start MTE
    ${memUsage}    get memory usage
    Run Keyword If    ${memUsage} > 90    Fail    Memory usage > 90%. This would make the system become instable during testing.
    [Return]    ${ret}

MTE or FTE
    [Documentation]    Determine if this venue has an MTE or FTE.
    ...    Return either 'MTE' or 'FTE'.
    ...    Fail if neither MTE nor FTE is found.
    ${result}=    find processes by pattern    FTE -c ${MTE}
    Return From Keyword If    len('${result}')    FTE
    ${result}=    find processes by pattern    MTE -c ${MTE}
    Return From Keyword If    len('${result}')    MTE
    Fail    Neither FTE nor MTE process is running

Persist File Should Exist
    ${res}=    search remote files    ${VENUE_DIR}    PERSIST_${MTE}.DAT    recurse=${True}
    Length Should Be    ${res}    1    PERSIST_${MTE}.DAT file not found (or multiple files found).
    Comment    Currently, GATS does not provide the Venue name, so the pattern matching Keywords must be used. If GATS provides the Venue name, then "remote file should not exist" Keywords could be used here.

Purge RIC
    [Arguments]    ${ric}    ${domain}    ${serviceName}
    [Documentation]    Purge a RIC by FMSCmd.
    ...    HandlerDropType: \ Purge
    ${currDateTime}    get date and time
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    drop    --RIC ${ric}
    ...    --Domain ${domain}    --HandlerName ${MTE}    --HandlerDropType Purge
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}
    wait smf log message after time    Drop    ${currDateTime}

Rename Files
    [Arguments]    ${oldstring}    ${newstring}    @{files}
    ${newFileList}=    Create List
    : FOR    ${file}    IN    @{files}
    \    ${newfile}=    Replace String    ${file}    ${oldstring}    ${newstring}
    \    Move File    ${file}    ${newfile}
    \    Append To List    ${newFileList}    ${newfile}
    [Return]    @{newFileList}

Reset Sequence Numbers
    [Arguments]    @{mach_ip_list}
    [Documentation]    Reset the FTE sequence numbers on each specified machine (default is current machine).
    ...    Currently this is done by stopping and starting the component and deleting the PERSIST files.
    ...    If/when a hook is provided to reset the sequence numbers without restarting the component, it should be used.
    ...    For peer testing, stop processes and delete files on all machines before restarting processes to avoid peer recovery of sequence numbers.
    ...
    ...    This KW also waits for any publishing due to the MTE restart/reorg to complete.
    ...
    ...    Note: several test cases need to stop and restart MTE to load new configuration file, for example 'Empty Payload Detection with Blank FIDFilter'
    ...    'Empty Payload Detection with Blank TCONF'. Stopping MTE, deleting persist file, and starting MTE need to be added to those test cases when the new 'reset sequence numbers' is implemented.
    ${host}=    get current connection index
    @{new_list}    Run Keyword If    len(${mach_ip_list}) == 0    Create List    ${host}
    ...    ELSE    Create List    @{mach_ip_list}
    Comment    First, stop everything
    : FOR    ${mach}    IN    @{new_list}
    \    Run Keyword If    '${mach}' != '${host}'    Switch To TD Box    ${mach}
    \    Stop MTE
    \    Delete Persist Files
    Comment    Then, restart everything
    : FOR    ${mach}    IN    @{new_list}
    \    Run Keyword If    '${mach}' != '${host}'    Switch To TD Box    ${mach}
    \    ${currDateTime}    get date and time
    \    Start MTE
    \    Wait SMF Log Message After Time    Finished Startup, Begin Regular Execution    ${currDateTime}
    \    Comment    We don't capture the output file, but this waits for any publishing to complete
    \    Wait For MTE Capture To Complete    5    600
    [Teardown]    Switch Connection    ${host}

Restart SMF
    Stop SMF
    Start SMF
    Start MTE

Restore EXL Changes
    [Arguments]    ${serviceName}    ${exlFiles}
    [Documentation]    Reload the original version of the EXL files using Fmscmd.
    : FOR    ${file}    IN    @{exlFiles}
    \    Load Single EXL File    ${file}    ${serviceName}    ${CHE_IP}
    [Teardown]

Restore Files
    [Arguments]    ${origFiles}    ${currFiles}
    ${numFiles}=    Get Length    ${currFiles}
    : FOR    ${i}    IN RANGE    ${numFiles}
    \    Move File    ${currFiles[${i}]}    ${origFiles[${i}]}

Restore MTE Clock Sync
    [Documentation]    If running on a vagrant VirtualBox, re-enable the VirtualBox Guest Additions service. \ This will resync the VM clock to the host machine time.
    ${result}=    Execute Command    if [ -f /etc/init.d/vboxadd-service ]; then service vboxadd-service start; fi

Restore MTE Machine Time
    [Arguments]    ${MTETimeOffset}
    [Documentation]    To correct Linux time and restart SMF, restart SMF because currently FMS client have a bug now, if we change the MTE Machine time when SMF running, FMS client start to report exception like below, and in this case we can't use FMS client correclty:
    ...    FMSClient:SocketException - ClientImpl::connect:connect (111); /ThomsonReuters/EventScheduler/EventScheduler; 18296; 18468; 0000235f; 07:00:00;
    ...
    ...    In addition, on a vagrant VirtualBox, restore the VirtualBox Guest Additions service, which includes clock sync with the host.
    stop smf
    ${RIDEMachineTime}=    Get Current Date    result_format=datetime    exclude_millis=True
    ${MTEMachineTime}=    Add Time To Date    ${RIDEMachineTime}    ${MTETimeOffset}    result_format=datetime
    set date and time    ${MTEMachineTime.year}    ${MTEMachineTime.month}    ${MTEMachineTime.day}    ${MTEMachineTime.hour}    ${MTEMachineTime.minute}    ${MTEMachineTime.second}
    Restore MTE Clock Sync
    start smf

Rewrite PCAP File
    [Arguments]    ${inputFile}    @{optargs}
    remote file should exist    ${inputFile}
    ${random}=    Generate Random String    4    [NUMBERS]
    ${outputFile}=    set variable    ${REMOTE_TMP_DIR}/modified${random}.pcap
    ${optstr} =    Catenate    @{optargs}
    ${stdout}    ${rc}    execute_command    tcprewrite --infile=${inputFile} --outfile=${outputFile} ${optstr}    return_rc=True
    Should Be Equal As Integers    ${rc}    0
    [Return]    ${outputFile}

Send TRWF2 Refresh Request
    [Arguments]    ${ric}    ${domain}    @{optargs}
    [Documentation]    Call DataView to send TRWF2 Refresh Request to MTE.
    ...    The refresh request will be sent to all possible multicast addresses for each labelID defined in venue configuration file.
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1708
    ${ddnreqLabelfilepath}=    Get CHE Config Filepaths    ddnReqLabels.xml
    Length Should Be    ${ddnreqLabelfilepath}    1    ddnReqLabels.xml file not found (or multiple files found).
    ${labelfile}=    set variable    ${LOCAL_TMP_DIR}/reqLabel.xml
    get remote file    ${ddnreqLabelfilepath[0]}    ${labelfile}
    ${updatedlabelfile}=    set variable    ${LOCAL_TMP_DIR}/updated_reqLabel.xml
    remove_xinclude_from_labelfile    ${labelfile}    ${updatedlabelfile}
    @{labelIDs}=    Get Label IDs
    : FOR    ${labelID}    IN    @{labelIDs}
    \    ${reqMsgMultcastAddres}=    get multicast address from label file    ${updatedlabelfile}    ${labelID}
    \    ${lineID}=    get_stat_block_field    ${MTE}    multicast-${labelID}    publishedLineId
    \    ${multcastAddres}=    get_stat_block_field    ${MTE}    multicast-${LabelID}    multicastOutputAddress
    \    ${interfaceAddres}=    get_stat_block_field    ${MTE}    multicast-${LabelID}    primaryOutputAddress
    \    @{multicastIPandPort}=    Split String    ${multcastAddres}    :    1
    \    @{interfaceIPandPort}=    Split String    ${interfaceAddres}    :    1
    \    ${length} =    Get Length    ${multicastIPandPort}
    \    Should Be Equal As Integers    ${length}    2
    \    ${length} =    Get Length    ${interfaceIPandPort}
    \    Should Be Equal As Integers    ${length}    2
    \    ${res}=    Run Dataview    TRWF2    @{multicastIPandPort}[0]    @{interfaceIPandPort}[0]    @{multicastIPandPort}[1]
    \    ...    ${lineID}    ${ric}    ${domain}    -REF    -IMSG ${reqMsgMultcastAddres[0]}
    \    ...    -PMSG ${reqMsgMultcastAddres[1]}    -S 0    -EXITDELAY 10    @{optargs}
    \    ${resLength} =    Get Length    ${res}
    \    Exit For Loop If    ${resLength} > 0
    Remove Files    ${labelfile}    ${updatedlabelfile}
    [Return]    ${res}

Send TRWF2 Refresh Request No Blank FIDs
    [Arguments]    ${ric}    ${domain}    @{optargs}
    [Documentation]    Call DataView to send TRWF2 Refresh Request to MTE.
    ...    The refresh request will be sent to all possible multicast addresses for each labelID defined in venue configuration file.
    ...    FIDs with blank value will be excluded
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1708
    ${ddnreqLabelfilepath}=    Get CHE Config Filepaths    ddnReqLabels.xml
    Length Should Be    ${ddnreqLabelfilepath}    1    ddnReqLabels.xml file not found (or multiple files found).
    ${labelfile}=    set variable    ${LOCAL_TMP_DIR}/reqLabel.xml
    get remote file    ${ddnreqLabelfilepath[0]}    ${labelfile}
    ${updatedlabelfile}=    set variable    ${LOCAL_TMP_DIR}/updated_reqLabel.xml
    remove_xinclude_from_labelfile    ${labelfile}    ${updatedlabelfile}
    @{labelIDs}=    Get Label IDs
    : FOR    ${labelID}    IN    @{labelIDs}
    \    ${reqMsgMultcastAddres}=    get multicast address from label file    ${updatedlabelfile}    ${labelID}
    \    ${lineID}=    get_stat_block_field    ${MTE}    multicast-${labelID}    publishedLineId
    \    ${multcastAddres}=    get_stat_block_field    ${MTE}    multicast-${LabelID}    multicastOutputAddress
    \    ${interfaceAddres}=    get_stat_block_field    ${MTE}    multicast-${LabelID}    primaryOutputAddress
    \    @{multicastIPandPort}=    Split String    ${multcastAddres}    :    1
    \    @{interfaceIPandPort}=    Split String    ${interfaceAddres}    :    1
    \    ${length} =    Get Length    ${multicastIPandPort}
    \    Should Be Equal As Integers    ${length}    2
    \    ${length} =    Get Length    ${interfaceIPandPort}
    \    Should Be Equal As Integers    ${length}    2
    \    ${res}=    Run Dataview Noblanks    TRWF2    @{multicastIPandPort}[0]    @{interfaceIPandPort}[0]    @{multicastIPandPort}[1]
    \    ...    ${lineID}    ${ric}    ${domain}    -REF    -IMSG ${reqMsgMultcastAddres[0]}
    \    ...    -PMSG ${reqMsgMultcastAddres[1]}    -S 0    -EXITDELAY 10    @{optargs}
    \    ${resLength} =    Get Length    ${res}
    \    Exit For Loop If    ${resLength} > 0
    Remove Files    ${labelfile}    ${updatedlabelfile}
    [Return]    ${res}

Set 24x7 Feed And Trade Time And No Holidays
    [Documentation]    Udate EXL files to define feed time and trade time to always be open and no holidays. This KW does not load the EXL files, just modifies them. Start MTE KW loads the EXL files.
    ...    For all trade time RICs:
    ...    Set start of trade time to 00:00:00 and end of feed time to 23:59:59 for all days of the week.
    ...    For all feed time RICs:
    ...    Set start of feed time to 00:00:00 and end of feed time to 23:59:59 for all days of the week.
    ...    For all holidays:
    ...    Blank out all holidays.
    ${statRicDomain}=    Set Variable    MARKET_PRICE
    ${serviceName}=    get FMS service name
    @{connectTimesIdentifierList}=    Get ConnectTimesIdentifier
    @{highActivityIdentifierList}=    Get HighActivityTimesIdentifier
    @{holidayEXLFiles}=    Create List
    ${start}=    Set Variable    00:00:00
    ${end}=    Set Variable    23:59:59
    @{edits}=    Create List    <it:SUN_FD_OPEN>${start}</it:SUN_FD_OPEN>    <it:SUN_FD_CLOSE>${end}</it:SUN_FD_CLOSE>    <it:MON_FD_OPEN>${start}</it:MON_FD_OPEN>    <it:MON_FD_CLOSE>${end}</it:MON_FD_CLOSE>    <it:TUE_FD_OPEN>${start}</it:TUE_FD_OPEN>
    ...    <it:TUE_FD_CLOSE>${end}</it:TUE_FD_CLOSE>    <it:WED_FD_OPEN>${start}</it:WED_FD_OPEN>    <it:WED_FD_CLOSE>${end}</it:WED_FD_CLOSE>    <it:THU_FD_OPEN>${start}</it:THU_FD_OPEN>    <it:THU_FD_CLOSE>${end}</it:THU_FD_CLOSE>    <it:FRI_FD_OPEN>${start}</it:FRI_FD_OPEN>
    ...    <it:FRI_FD_CLOSE>${end}</it:FRI_FD_CLOSE>    <it:SAT_FD_OPEN>${start}</it:SAT_FD_OPEN>    <it:SAT_FD_CLOSE>${end}</it:SAT_FD_CLOSE>
    Comment    Feed Time
    : FOR    ${ric}    IN    @{connectTimesIdentifierList}
    \    ${exlFile}    get state EXL file    ${ric}    ${statRicDomain}    ${serviceName}    Feed Time
    \    Modify EXL    ${exlFile}    ${exlFile}    ${ric}    ${statRicDomain}    @{edits}
    \    Comment    Get associated holiday EXL
    \    ${unused}    ${holidayRic}    Get DST And Holiday RICs From EXL    ${exlFile}    ${ric}
    \    ${holidayEXL}=    get state EXL file    ${holidayRic}    ${statRicDomain}    ${serviceName}    Holiday
    \    Append To List    ${holidayEXLFiles}    ${holidayEXL}
    Comment    Trade Time
    @{edits}=    Create List    <it:SUN_TR_OPEN>${start}</it:SUN_TR_OPEN>    <it:SUN_TR_CLOSE>${end}</it:SUN_TR_CLOSE>    <it:MON_TR_OPEN>${start}</it:MON_TR_OPEN>    <it:MON_TR_CLOSE>${end}</it:MON_TR_CLOSE>    <it:TUE_TR_OPEN>${start}</it:TUE_TR_OPEN>
    ...    <it:TUE_TR_CLOSE>${end}</it:TUE_TR_CLOSE>    <it:WED_TR_OPEN>${start}</it:WED_TR_OPEN>    <it:WED_TR_CLOSE>${end}</it:WED_TR_CLOSE>    <it:THU_TR_OPEN>${start}</it:THU_TR_OPEN>    <it:THU_TR_CLOSE>${end}</it:THU_TR_CLOSE>    <it:FRI_TR_OPEN>${start}</it:FRI_TR_OPEN>
    ...    <it:FRI_TR_CLOSE>${end}</it:FRI_TR_CLOSE>    <it:SAT_TR_OPEN>${start}</it:SAT_TR_OPEN>    <it:SAT_TR_CLOSE>${end}</it:SAT_TR_CLOSE>
    : FOR    ${ric}    IN    @{highActivityIdentifierList}
    \    ${exlFile}    get state EXL file    ${ric}    ${statRicDomain}    ${serviceName}    Trade Time
    \    Modify EXL    ${exlFile}    ${exlFile}    ${ric}    ${statRicDomain}    @{edits}
    \    Comment    Get associated holiday EXL
    \    ${unused}    ${holidayRic}    Get DST And Holiday RICs From EXL    ${exlFile}    ${ric}
    \    ${holidayEXL}=    get state EXL file    ${holidayRic}    ${statRicDomain}    ${serviceName}    Holiday
    \    Append To List    ${holidayEXLFiles}    ${holidayEXL}
    ${holidayEXLFiles}    Remove Duplicates    ${holidayEXLFiles}
    Comment    Holidays
    : FOR    ${exlFile}    IN    @{holidayEXLFiles}
    \    Blank Out Holidays    ${exlFile}    ${exlFile}
    [Teardown]

Set Common Suite Variables
    [Arguments]    ${ip}
    [Documentation]    Set suite variable that are used by many suites.
    ...    This Keyword is called by the suite setup Keywords.
    ...
    ...    The following varibles are set:
    ...    CHE_IP - address of the current CHE box
    ...    MTE_CONFIG - MTE config file name
    ...    REMOTE_MTE_CONFIG_DIR - path to directory containing the MTE config file on Thunderdome box.
    ...    REORG_FROM_FMS_SERVER = ${True} indicate that MTE has been sync up its cache from FMS server before.
    Set Suite Variable    ${CHE_IP}    ${ip}
    ${MTE_CONFIG}=    convert to lowercase    ${MTE}.json
    Set Suite Variable    ${MTE_CONFIG}
    ${fileList}=    search remote files    ${VENUE_DIR}    ${MTE_CONFIG}    recurse=${True}
    Length Should Be    ${fileList}    1    ${MTE_CONFIG} file not found (or multiple files found).
    ${dirAndFile}=    Split String From Right    ${fileList[0]}    /    max_split=1
    Set Suite Variable    ${REMOTE_MTE_CONFIG_DIR}    ${dirAndFile[0]}
    Set Suite Variable    ${REORG_FROM_FMS_SERVER}    ${True}

Set DST Datetime In EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${ric}    ${domain}    ${startDateTime}    ${endDateTime}
    [Documentation]    Set DST datetime in EXL:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1642
    modify EXL    ${srcFile}    ${dstFile}    ${ric}    ${domain}    <it:DS_START>${startDateTime}</it:DS_START>
    modify EXL    ${dstFile}    ${dstFile}    ${ric}    ${domain}    <it:DS_END>${endDateTime}</it:DS_END>

Set Feed Time In EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${ric}    ${domain}    ${startTime}    ${endTime}
    ...    ${feedDay}
    [Documentation]    Set feed time in EXL:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1646
    Run Keyword If    '${startTime}'!='${Empty}'    modify EXL    ${srcFile}    ${dstFile}    ${ric}    ${domain}
    ...    <it:${feedDay}_FD_OPEN>${startTime}</it:${feedDay}_FD_OPEN>
    ${srcFile}    Set Variable If    '${startTime}'!='${Empty}'    ${dstFile}    ${srcFile}
    Run Keyword If    '${endTime}'!='${Empty}'    modify EXL    ${srcFile}    ${dstFile}    ${ric}    ${domain}
    ...    <it:${feedDay}_FD_CLOSE>${endTime}</it:${feedDay}_FD_CLOSE>

Set Field Value in EXL
    [Arguments]    ${exlFile}    ${ric}    ${domain}    ${fieldName}    ${fieldValueNew}
    [Documentation]    This keyword could set the value for specific xml tag that found within <exlObject></exlObject> for specific ric and domain
    @{fieldValueOrg}=    get ric fields from EXL    ${exlFile}    ${ric}    ${fieldName}
    modify exl    ${exlFile}    ${exlFile}    ${ric}    ${domain}    <it:${fieldName}>${fieldValueNew}</it:${fieldName}>
    [Return]    @{fieldValueOrg}[0]

Set Holiday Datetime In EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${ric}    ${domain}    ${startDateTime}    ${endDateTime}
    ...    ${holidayIndex}=00
    [Documentation]    Set holiday datetime in EXL:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1639
    blank out holidays    ${srcFile}    ${dstFile}
    modify EXL    ${dstFile}    ${dstFile}    ${ric}    ${domain}    <it:HLY${holidayIndex}_START_TIME>${startDateTime}</it:HLY${holidayIndex}_START_TIME>
    modify EXL    ${dstFile}    ${dstFile}    ${ric}    ${domain}    <it:HLY${holidayIndex}_END_TIME>${endDateTime}</it:HLY${holidayIndex}_END_TIME>

Set Mangling Rule
    [Arguments]    ${rule}    ${configFile}=manglingConfiguration.xml
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/CATF-1843
    ...
    ...    Remark :
    ...    Current avaliable valid value for \ ${rule} : SOU, BETA, RRG \ or UNMANGLED
    ...    The KW would restore the config file to original value, but it would rely on user to calling KW : Load Mangling Settings to carry out the restore action at the end of their test case
    @{files}=    backup remote cfg file    ${REMOTE_MTE_CONFIG_DIR}    ${configFile}
    ${configFileLocal}=    Get Mangling Config File
    set mangling rule default value    ${rule}    ${configFileLocal}
    set mangling rule parition value    ${rule}    ${Empty}    ${configFileLocal}
    delete remote files    @{files}[0]
    put remote file    ${configFileLocal}    @{files}[0]
    Run Keyword And Continue On Failure    Load Mangling Settings
    restore remote cfg file    @{files}
    Comment    Revert changes in local mangling config file
    Set Suite Variable    ${LOCAL_MANGLING_CONFIG_FILE}    ${None}
    ${configFileLocal}=    Get Mangling Config File

Set RIC In EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${ric}    ${domain}    ${newRIC}
    [Documentation]    Set RIC in EXL:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1649
    modify EXL    ${srcFile}    ${dstFile}    ${ric}    ${domain}    <it:RIC>${newRIC}</it:RIC>

Set Symbol In EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${ric}    ${domain}    ${newSymbol}
    [Documentation]    Set Symbol in EXL, replace the old symbol to ${newSymbol}
    modify EXL    ${srcFile}    ${dstFile}    ${ric}    ${domain}    <it:SYMBOL>${newSymbol}</it:SYMBOL>

Set Trade Time In EXL
    [Arguments]    ${srcFile}    ${dstFile}    ${ric}    ${domain}    ${startTime}    ${endTime}
    ...    ${tradeDay}
    [Documentation]    Set trade time in EXL:
    ...
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1645
    modify EXL    ${srcFile}    ${dstFile}    ${ric}    ${domain}    <it:${tradeDay}_TR_OPEN>${startTime}</it:${tradeDay}_TR_OPEN>
    modify EXL    ${dstFile}    ${dstFile}    ${ric}    ${domain}    <it:${tradeDay}_TR_CLOSE>${endTime}</it:${tradeDay}_TR_CLOSE>

Start Capture MTE Output
    [Arguments]    ${filename}=/tmp/capture.pcap    ${ddn}=DDNA    @{labelID}
    [Documentation]    Start capture MTE output
    ...
    ...    Remark :
    ...    1. If ${labelID} is empty , we assume to capture all multicast ips and ports for all label IDs that available
    ${interfaceName}=    get interface name by alias    ${ddn}
    ${labelIDLength}    Get Length    ${labelID}
    ${labelIDsUse}    Run Keyword If    ${labelIDLength} == 0    Get Label IDs
    ...    ELSE    Create List    @{labelID}
    @{IpAndPort}=    get outputAddress and port for mte    ${labelIDsUse}
    start capture packets    ${filename}    ${interfaceName}    ${IpAndPort}

Start Capture MTE Output By DataView
    [Arguments]    ${ric}    ${domain}    ${labelID}    ${outputFile}    @{optargs}
    [Documentation]    Start DataView to capture TRWF2 MTE update.
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-2104
    ${ddnreqLabelfilepath}=    search remote files    ${BASE_DIR}    ddnReqLabels.xml    recurse=${True}
    Length Should Be    ${ddnreqLabelfilepath}    1    ddnReqLabels.xml file not found (or multiple files found).
    ${labelfile}=    set variable    ${LOCAL_TMP_DIR}/reqLabel.xml
    get remote file    ${ddnreqLabelfilepath[0]}    ${labelfile}
    ${updatedlabelfile}=    set variable    ${LOCAL_TMP_DIR}/updated_reqLabel.xml
    remove_xinclude_from_labelfile    ${labelfile}    ${updatedlabelfile}
    ${reqMsgMultcastAddres}=    get multicast address from label file    ${updatedlabelfile}    ${labelID}
    ${lineID}=    get_stat_block_field    ${MTE}    multicast-${labelID}    publishedLineId
    ${multcastAddres}=    get_stat_block_field    ${MTE}    multicast-${LabelID}    multicastOutputAddress
    ${interfaceAddres}=    get_stat_block_field    ${MTE}    multicast-${LabelID}    primaryOutputAddress
    @{multicastIPandPort}=    Split String    ${multcastAddres}    :    1
    @{interfaceIPandPort}=    Split String    ${interfaceAddres}    :    1
    ${length} =    Get Length    ${multicastIPandPort}
    Should Be Equal As Integers    ${length}    2
    ${length} =    Get Length    ${interfaceIPandPort}
    Should Be Equal As Integers    ${length}    2
    ${pid}=    Start Dataview    TRWF2    @{multicastIPandPort}[0]    @{interfaceIPandPort}[0]    @{multicastIPandPort}[1]    ${lineID}
    ...    ${ric}    ${domain}    ${outputFile}    @{optargs}
    [Return]    ${pid}

Start MTE
    [Documentation]    Start the MTE and wait for initialization to complete.
    ...    Then load the state EXL files (that were modified by suite setup to set 24x7 feed and trade time).
    ...
    ...    If Recon is changed to set ResendFM=0 in the MTE config file, instead of loading just the state EXL files, this will need to load all of the EXL files (if they have not already been loaded). \ With ResendFM=1, we need to wait for FMS reorg to finish, and then load the state EXL files to override the ones loaded from the FMS server.
    ...
    ...    Remark:
    ...    ${REORG_FROM_FMS_SERVER} = ${True} indicate that MTE has been sync up its cache from FMS server before.
    ${result}=    find processes by pattern    [FM]TE -c ${MTE}
    ${len}=    Get Length    ${result}
    Run keyword if    ${len} != 0    Run Keywords    wait for HealthCheck    ${MTE}    IsLinehandlerStartupComplete    waittime=5
    ...    timeout=600
    ...    AND    Load All State EXL Files
    Return from keyword if    ${len} != 0
    run commander    process    start ${MTE}
    wait for process to exist    [FM]TE -c ${MTE}
    wait for HealthCheck    ${MTE}    IsLinehandlerStartupComplete    waittime=5    timeout=600
    Wait For FMS Reorg
    Load All State EXL Files
    Set Suite Variable    ${REORG_FROM_FMS_SERVER}    ${True}

Start Process
    [Arguments]    ${process}
    [Documentation]    Start process, argument is the process name
    run commander    process    start ${process}
    wait for process to exist    ${process}
    wait for StatBlock    CritProcMon    ${process}    m_IsAvailable    1    10    180

Stop Capture MTE Output
    [Arguments]    ${waittime}=5    ${timeout}=300
    [Documentation]    Stop catpure MTE output
    wait for MTE capture to complete    ${waittime}    ${timeout}
    stop capture packets

Stop MTE
    run commander    process    stop ${MTE}
    wait for process to not exist    [FM]TE -c ${MTE}

Stop Process
    [Arguments]    ${process}
    [Documentation]    Stop process, argument is the process name
    run commander    process    stop ${process}
    wait for process to not exist    ${process}

Suite Setup
    [Documentation]    Do test suite level setup, e.g. things that take time and do not need to be repeated for each test case.
    ...    Make sure the CHE_IP machine has the LIVE MTE instance.
    Should Not be Empty    ${CHE_IP}
    Set Suite Variable    ${CHE_A_Session}    ${EMPTY}
    Set Suite Variable    ${CHE_B_Session}    ${EMPTY}
    ${ret}    MTE Machine Setup    ${CHE_IP}
    Set Suite Variable    ${CHE_A_Session}    ${ret}
    [Return]    ${ret}

Suite Setup Two TD Boxes
    [Documentation]    Setup 2 Sessions for 2 Peer Thunderdome Boxes
    Should Not be Empty    ${CHE_A_IP}
    Should Not be Empty    ${CHE_B_IP}
    Set Suite Variable    ${CHE_A_Session}    ${EMPTY}
    Set Suite Variable    ${CHE_B_Session}    ${EMPTY}
    ${ret}    MTE Machine Setup    ${CHE_A_IP}
    Set Suite Variable    ${CHE_A_Session}    ${ret}
    ${ret}    MTE Machine Setup    ${CHE_B_IP}
    Set Suite Variable    ${CHE_B_Session}    ${ret}

Suite Setup Two TD Boxes With Playback
    [Documentation]    Setup 3 Sessions, 2 Peer Thunderdome Boxes, 1 Playback Box
    Should Not be Empty    ${CHE_A_IP}
    Should Not be Empty    ${CHE_B_IP}
    Should Not be Empty    ${PLAYBACK_MACHINE_IP}
    ${plyblk}    open connection    host=${PLAYBACK_MACHINE_IP}    port=${PLAYBACK_PORT}    timeout=5
    login    ${PLAYBACK_USERNAME}    ${PLAYBACK_PASSWORD}
    Set Suite Variable    ${Playback_Session}    ${plyblk}
    ${ret}    MTE Machine Setup    ${CHE_B_IP}
    Set Suite Variable    ${CHE_B_Session}    ${ret}
    ${ret}    MTE Machine Setup    ${CHE_A_IP}
    Set Suite Variable    ${CHE_A_Session}    ${ret}

Suite Setup with Playback
    [Documentation]    Setup Playback box and suit scope variable Playback_Session.
    Should Not be Empty    ${PLAYBACK_MACHINE_IP}
    ${plyblk}    open connection    host=${PLAYBACK_MACHINE_IP}    port=${PLAYBACK_PORT}    timeout=5
    login    ${PLAYBACK_USERNAME}    ${PLAYBACK_PASSWORD}
    Set Suite Variable    ${Playback_Session}    ${plyblk}
    ${ret}    Suite Setup

Suite Teardown
    [Documentation]    Do test suite level teardown, e.g. closing ssh connections.
    Run Keyword If    '${CHE_A_Session}' != '${EMPTY}'    Run Keywords    Switch To TD Box    ${CHE_A_IP}
    ...    AND    stop smf
    Run Keyword If    '${CHE_B_Session}' != '${EMPTY}'    Run Keywords    Switch To TD Box    ${CHE_B_IP}
    ...    AND    stop smf
    close all connections
    ${localCfgFile}=    Get Variable Value    ${LOCAL_MTE_CONFIG_FILE}
    Run Keyword If    r'${localCfgFile}' != 'None'    Remove File    ${localCfgFile}
    ${localCfgFile}=    Get Variable Value    ${LOCAL_MANGLING_CONFIG_FILE}
    Run Keyword If    r'${localCfgFile}' != 'None'    Remove File    ${localCfgFile}
    ${localCfgFile}=    Get Variable Value    ${LOCAL_FIDFILTER_FILE}
    Run Keyword If    r'${localCfgFile}' != 'None'    Remove File    ${localCfgFile}

Switch To TD Box
    [Arguments]    ${ip}
    [Documentation]    To switch the current ssh session to specific CHE_X_IP
    ${switchBox}    Run Keyword If    '${ip}' == '${CHE_A_IP}'    set variable    ${CHE_A_Session}
    ...    ELSE IF    '${ip}' == '${CHE_B_IP}'    set variable    ${CHE_B_Session}
    ...    ELSE IF    '${ip}' == '${PLAYBACK_MACHINE_IP}'    set variable    ${Playback_Session}
    ...    ELSE    Fail    Invaild IP
    Set Suite Variable    ${CHE_IP}    ${ip}
    switch connection    ${switchBox}
    Set Suite Variable    ${LOCAL_MTE_CONFIG_FILE}    ${None}

Verify MTE State In Specific Box
    [Arguments]    ${che_ip}    ${state}    ${waittime}=5    ${timeout}=150
    ${host}=    get current connection index
    Switch To TD Box    ${che_ip}
    verify MTE state    ${state}    ${waittime}    ${timeout}
    [Teardown]    Run Keyword If    '${host}' == '${CHE_A_Session}'    Switch To TD Box    ${CHE_A_IP}
    ...    ELSE IF    '${host}' == '${CHE_B_Session}'    Switch To TD Box    ${CHE_B_IP}
    ...    ELSE    Fail    Current host IP ${host} is not A, B machine IP

Verify RIC In MTE Cache
    [Arguments]    ${ric}    ${domain}
    ${ricFields}=    Get All Fields For RIC From Cache    ${ric}    ${domain}
    Should Not Be Empty    ${ricFields}    RIC ${ric} not found in MTE cache
    ${ric}=    set variable    ${ricFields['RIC']}
    ${publish_key}=    set variable    ${ricFields['PUBLISH_KEY']}
    [Teardown]
    [Return]    ${ric}    ${publish_key}

Verify RIC Not In MTE Cache
    [Arguments]    ${ric}    ${domain}
    ${ricFields}=    Get All Fields For RIC From Cache    ${ric}    ${domain}
    Should Be Empty    ${ricFields}    RIC ${ric} found in MTE cache

Verify RIC Is Dropped In MTE Cache
    [Arguments]    ${ric}    ${domain}
    [Documentation]    If a RIC be dropped, it will be non-publishable and be in InDeletionDelay state
    ${allricFields}=    get all fields for ric from cache    ${ric}    ${domain}
    Should Be Equal    ${allricFields['PUBLISHABLE']}    FALSE
    Should Be True    ${allricFields['NON_PUBLISHABLE_REASONS'].find('InDeletionDelay')} != -1

Verify Item Persisted
    [Arguments]    ${ric}=${EMPTY}    ${sic}=${EMPTY}    ${domain}=${EMPTY}
    [Documentation]    Dump persist file to XML and check if ric, sic and/or domain items exist in MTE persist file.
    ${cacheDomainName}=    Remove String    ${domain}    _
    ${pmatDomain}=    Run Keyword If    '${cacheDomainName}'!='${EMPTY}'    Map to PMAT Numeric Domain    ${cacheDomainName}
    @{pmatOptargs}=    Gen Pmat Cmd Args    ${ric}    ${sic}    ${pmatDomain}
    ${pmatDumpfile}=    Dump Persist File To XML    @{pmatOptargs}
    Verify Item in Persist Dump File    ${pmatDumpfile}    ${ric}    ${sic}    ${cacheDomainName}
    Remove Files    ${pmatDumpfile}

Verify Item Not Persisted
    [Arguments]    ${ric}=${EMPTY}    ${sic}=${EMPTY}    ${domain}=${EMPTY}
    [Documentation]    Dump persist file to XML and check if ric, sic and/or domain items not exist in MTE persist file.
    ${cacheDomainName}=    Remove String    ${domain}    _
    ${pmatDomain}=    Run Keyword If    '${cacheDomainName}'!='${EMPTY}'    Map to PMAT Numeric Domain    ${cacheDomainName}
    @{pmatOptargs}=    Gen Pmat Cmd Args    ${ric}    ${sic}    ${pmatDomain}
    ${pmatDumpfile}=    Dump Persist File To XML    @{pmatOptargs}
    verify_item_not_in_persist_dump_file    ${pmatDumpfile}    ${ric}    ${sic}
    Remove Files    ${pmatDumpfile}

Verify Peers Match
    [Arguments]    ${remoteCapture}    ${deleteRemoteCapture}=${True}
    [Documentation]    For each RIC in the remote capture file, verify the FID values match between A and B instances.
    ${ip_list}    create list    ${CHE_A_IP}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    ${domain}=    Get Preferred Domain
    Switch To TD Box    ${CHE_A_IP}
    ${ricList}=    Get RIC List From Remote PCAP    ${remoteCapture}    ${domain}
    ${remoteRicFile}=    Set Variable    ${REMOTE_TMP_DIR}/ricList.txt
    Create Remote File Content    ${remoteRicFile}    ${ricList}
    Comment    Make sure A is LIVE before running Dataview on A.
    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    verify MTE state    LIVE
    ${A_FIDs}=    Get FID Values From Refresh Request    ${remoteRicFile}    ${domain}
    Run Keyword If    ${deleteRemoteCapture}==${True}    Delete Remote Files    ${remoteCapture}
    Delete Remote Files    ${remoteRicFile}
    Comment    Make B LIVE before running Dataview on B.
    Switch To TD Box    ${CHE_B_IP}
    Create Remote File Content    ${remoteRicFile}    ${ricList}
    switch MTE LIVE STANDBY status    B    LIVE    ${master_ip}
    verify MTE state    LIVE
    ${B_FIDs}=    Get FID Values From Refresh Request    ${remoteRicFile}    ${domain}
    Dictionary of Dictionaries Should Be Equal    ${A_FIDs}    ${B_FIDs}
    Delete Remote Files    ${remoteRicFile}

Wait For FMS Reorg
    [Arguments]    ${waittime}=5    ${timeout}=600
    [Documentation]    Wait for the MTE to complete the FMS reorg.
    wait for HealthCheck    ${MTE}    FMSStartupReorgHasCompleted    ${waittime}    ${timeout}

Wait For Persist File Update
    [Arguments]    ${waittime}=5    ${timeout}=60
    [Documentation]    Wait for the MTE persist file to be updated (it should be updated every 30 seconds)
    ${res}=    search remote files    ${VENUE_DIR}    PERSIST_${MTE}.DAT    recurse=${True}
    Length Should Be    ${res}    1    PERSIST_${MTE}.DAT file not found (or multiple files found).
    wait for file update    ${res[0]}    ${waittime}    ${timeout}
