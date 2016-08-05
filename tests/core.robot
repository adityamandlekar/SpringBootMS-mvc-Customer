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

Create Unique RIC Name
    [Arguments]    ${text}=
    [Documentation]    Create a unique RIC name. Format is 'TEST' + text param + current datetime string (YYYYMMDDHHMMSS}.
    ...    Max length of text param is 14 (18 chars are added and RIC max length is 32 chars)
    Run Keyword If    len('${text}')>14    FAIL    Max length for text string is 14
    ${dt}=    get date and time
    ${ric}=    set variable    TEST${text}${dt[0]}${dt[1]}${dt[2]}${dt[3]}${dt[4]}${dt[5]}
    [Return]    ${ric}

Delete GRS PCAP Files
    [Arguments]    @{mach_ip_list}
    [Documentation]    Delete the PCAP files created by GRS on each of the specified machines. \ If no machine is specified, delete GRS PCAP files on the current machine.
    ${host}=    get current connection index
    @{new_list}    Run Keyword If    len(${mach_ip_list}) == 0    Create List    ${host}
    ...    ELSE    Create List    @{mach_ip_list}
    : FOR    ${mach}    IN    @{new_list}
    \    Run Keyword If    '${mach}' != '${host}'    Switch To TD Box    ${mach}
    \    Delete Remote Files Matching Pattern    ${BASE_DIR}    *.pcap    ${True}
    [Teardown]    Switch Connection    ${host}

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
    Run PMAT    dump    --dll Schema_v6.dll    --db ${localPersistFile}    --oformat text    --outf ${pmatDumpfile}    @{optargs}
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
    Run PMAT    dump    --dll Schema_v6.dll    --db ${localPersistFile}    --outf ${pmatXmlDumpfile}    @{optargs}
    Remove Files    ${localPersistFile}
    [Return]    ${pmatXmlDumpfile}

Extract ICF
    [Arguments]    ${ric}    ${domain}    ${extractFile}    ${serviceName}
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    extract    --RIC ${ric}
    ...    --Domain ${domain}    --ExcludeNullFields true    --HandlerName ${MTE}    --OutputFile ${extractFile}    --Services ${serviceName}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Force Persist File Write
    [Arguments]    ${serviceName}
    [Documentation]    Force the MTE to write all updates to the Persist file.
    ...    This is done by putting all feeds into end of feed time; the MTE writes the Persist file as part of end of feed time processing.
    ...
    ...    There is currently no Commander command to force a Persist file write. \ If one exists in the future, this KW should be updated to use it instead of end of feed time.
    ...
    ...    The returned EXL file lists should be used to call Restore EXL Changes at the end of the test.
    ...
    ...    Return:
    ...    ${exlFiles} : list of exlFiles that were modified by this KW
    ...    ${modifiedExlFiles} : list of the modified exlFiles
    ${currDateTime}=    get date and time
    ${exlFiles}    ${modifiedExlFiles}    Go Into End Feed Time    ${serviceName}
    Wait SMF Log Message After Time    ${MTE}.*Persist cycle completed    ${currDateTime}    10    120
    [Teardown]
    [Return]    ${exlFiles}    ${modifiedExlFiles}

Generate FH PCAP File Name
    [Arguments]    ${service}    ${testCase}    @{keyValuePairs}
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/RECON-19
    ...
    ...    Generate the file name based on service name, test case and input key/value pairs
    ...
    ...    Example:
    ...    MFDS-Testcase.pcap
    ...    TDDS_BDDS-MyTestName-FH=TDDS01F.pcap
    ...    TDDS_BDDS-TransientGap-FH=TDDS01F.pcap
    ${pcapFileName}=    Catenate    SEPARATOR=-    ${service}    ${testCase}    @{keyValuePairs}
    ${pcapFileName} =    Catenate    SEPARATOR=    ${REMOTE_TMP_DIR}/    ${pcapFileName}    .pcap
    ${pcapFileName} =    Replace String    ${pcapFileName}    ${space}    _
    [Return]    ${pcapFileName}

Generate PCAP File Name
    [Arguments]    ${service}    ${testCase}    ${playbackBindSide}=A    @{keyValuePairs}
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/RECON-19
    ...
    ...    Generate the file name based on service name, test case, input key/value pairs and playback side designation --- default to A side
    ...
    ...    Example:
    ...    MFDS-Testcase-B.pcap
    ...    TDDS_BDDS-MyTestName-FH=TDDS01F-A.pcap
    ...    TDDS_BDDS-TransientGap-FH=TDDS01F-A.pcap
    ${pcapFileName}=    Catenate    SEPARATOR=-    ${service}    ${testCase}    @{keyValuePairs}    ${playbackBindSide}
    ${pcapFileName} =    Catenate    SEPARATOR=    ${PLAYBACK_PCAP_DIR}    ${pcapFileName}    .pcap
    ${pcapFileName} =    Replace String    ${pcapFileName}    ${space}    _
    [Return]    ${pcapFileName}

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

Get ConnectTimesIdentifier
    [Arguments]    ${mteConfigFile}    ${fhName}=${FH}
    [Documentation]    get the ConnectTimesIdentifier (feed times RIC) from venue config file.
    ...    returns
    ...    1. list with ConnectTimesIdentifier(s)
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
    ${len}    Get Length    ${fhName}
    ${connectTimesIdentifier}=    Run Keyword If    ${len} > 0    get MTE config value    ${mteConfigFile}    Inputs    ${fhName}
    ...    FHRealtimeLine    ConnectTimesIdentifier
    ...    ELSE    set variable    None
    Comment    Currently 'get MTE config value' will only return a string value. To align all return from 'Get ConnectTimesIdentifier' is a list, adding return value into a list
    @{retList}=    Split String    ${connectTimesIdentifier}    ,
    return from keyword if    '${connectTimesIdentifier}' != 'NOT FOUND' and '${connectTimesIdentifier}' != 'None'    ${retList}
    ${connectTimesIdentifier}=    get MTE config list by path    ${mteConfigFile}    FHRealtimeLine    ConnectTimesIdentifier
    @{retList}=    Remove Duplicates    ${connectTimesIdentifier}
    return from keyword if    len(${retList}) > 0    ${retList}
    ${connectTimesIdentifier}=    get MTE config list by path    ${mteConfigFile}    ConnectTimesRIC
    @{retList}=    Remove Duplicates    ${connectTimesIdentifier}
    return from keyword if    len(${retList}) > 0    ${retList}
    FAIL    No ConnectTimesIdentifier found in venue config file: ${mteConfigFile}

Get HighActivityTimesIdentifier
    [Arguments]    ${mteConfigFile}
    [Documentation]    get the HighActivityTimesIdentifier (trade times RIC) from venue config file.
    ...    returns a list of HighActivityTimesIdentifier.
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
    ${highActivityTimesIdentifier}=    get MTE config value    ${mteConfigFile}    Inputs    ${FH}    FHRealtimeLine    HighActivityTimesIdentifier
    @{retList}=    Split String    ${highActivityTimesIdentifier}    ,
    return from keyword if    '${highActivityTimesIdentifier}' != 'NOT FOUND'    @{retList}
    ${highActivityTimesIdentifier}=    get MTE config value    ${mteConfigFile}    HighActivityTimesRIC
    @{retList}=    Split String    ${highActivityTimesIdentifier}    ,
    return from keyword if    '${highActivityTimesIdentifier}' != 'NOT FOUND'    @{retList}
    FAIL    No HighActivityTimesIdentifier found in venue config file: ${mteConfigFile}
    [Return]    @{retList}

Get Domain Names
    [Arguments]    ${mteConfigFile}
    [Documentation]    get the Domain names from venue config file.
    ...    returns a list of Domain names.
    ${serviceName}    Get FMS Service Name
    ${domainList}    get MTE config list by path    ${mteConfigFile}    FMS    ${serviceName}    Domain    Z
    [Return]    @{domainList}

Get FID Values From Refresh Request
    [Arguments]    ${ricList}    ${domain}
    [Documentation]    Get the value for all non-blank FIDs for the RICs listed in the specfied file on the remote machine.
    ...
    ...    Returns a dictionary with key=RIC, value = {sub-dictionary with key=FID NAME and value=FID value}
    ${result}=    Send TRWF2 Refresh Request No Blank FIDs    ${ricList}    ${domain}    -RL 1
    ${ricDict}=    Convert DataView Response to MultiRIC Dictionary    ${result}
    [Return]    ${ricDict}

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

Get Label IDs
    [Documentation]    Get the list of labelIDs from MTE config file on current machine.
    ...    The LabelID may be different across machines, so use config files from current machine.
    Set Suite Variable    ${LOCAL_MTE_CONFIG_FILE}    ${None}
    ${localVenueConfig}=    get MTE config file
    @{labelIDs}=    get MTE config list by section    ${localVenueConfig}    Publishing    LabelID
    [Return]    @{labelIDs}

Get Mangling Config File
    [Documentation]    Get the manglingConfiguration.xml from TD Box
    ...    1. The file would be saved at Control PC and only removed at Suite Teardown
    ...    2. Suite Variable ${LOCAL_MANGLING_CONFIG_FILE} has created to store the fullpath of the config file at Control PC
    ${localFile}=    Get Variable Value    ${LOCAL_MANGLING_CONFIG_FILE}
    Run Keyword If    '${localFile}' != 'None'    Return From Keyword    ${localFile}
    ${res}=    search remote files    ${VENUE_DIR}    manglingConfiguration.xml    recurse=${True}
    Length Should Be    ${res}    1    manglingConfiguration.xml not found (or multiple files found).
    ${localFile}=    Set Variable    ${LOCAL_TMP_DIR}/mangling_config_file.xml
    get remote file    ${res[0]}    ${localFile}
    Set Suite Variable    ${LOCAL_MANGLING_CONFIG_FILE}    ${localFile}
    [Return]    ${localFile}

Get MTE Config File
    [Documentation]    Get the MTE config file (MTE.xml) from the remote machine and save it as a local file.
    ...    If we already have the local file, just return the file name without copying the remote file again.
    ${localFile}=    Get Variable Value    ${LOCAL_MTE_CONFIG_FILE}
    Run Keyword If    '${localFile}' != 'None'    Return From Keyword    ${localFile}
    ${lowercase_filename}    convert to lowercase    ${MTE}.xml
    ${res}=    search remote files    ${VENUE_DIR}    ${lowercase_filename}    recurse=${True}
    Length Should Be    ${res}    1    ${lowercase_filename} file not found (or multiple files found).
    ${localFile}=    Set Variable    ${LOCAL_TMP_DIR}/mte_config_file.xml
    get remote file    ${res[0]}    ${localFile}
    Set Suite Variable    ${LOCAL_MTE_CONFIG_FILE}    ${localFile}
    [Return]    ${localFile}

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
    [Documentation]    Get a single RIC name from MTE cache for the specified Domain and contextID.
    ...    If no Domain is specified it will call Get Preferred Domain to get the domain name to use.
    ...    If no contextID is specified, it will use any contextID
    ${preferredDomain}=    Run Keyword If    '${requestedDomain}'=='${EMPTY}'    Get Preferred Domain
    ${domain}=    Set Variable If    '${requestedDomain}'=='${EMPTY}'    ${preferredDomain}    ${requestedDomain}
    ${result}=    get RIC fields from cache    1    ${domain}    ${contextID}
    ${ric}=    set variable    ${result[0]['RIC']}
    ${publish_key}=    set variable    ${result[0]['PUBLISH_KEY']}
    [Teardown]
    [Return]    ${ric}    ${publish_key}

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
    [Documentation]    For all feeds, set start of feed time to current time and end of feed time in 2 minutes. Wait for end of feed time to occur.
    ...    The returned EXL file lists should be used to call Restore EXL Changes at the end of the test.
    ...
    ...    Return:
    ...    ${exlFiles} : list of the exlFiles that were modified by this KW
    ...    ${modifiedExlFiles} : list of the modified exlFiles
    ${secondsBeforeFeedEnd}=    set variable    120
    ${connectTimeRicDomain}=    set variable    MARKET_PRICE
    ${mteConfigFile}=    Get MTE Config File
    @{connectTimesIdentifierList}=    Get ConnectTimesIdentifier    ${mteConfigFile}    ${EMPTY}
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
    \    ${startWeekDay}=    get day of week from date    @{localDateTime}[0]    @{localDateTime}[1]    @{localDateTime}[2]
    \    ${startTime}=    set variable    @{localDateTime}[3]:@{localDateTime}[4]:@{localDateTime}[5]
    \    ${endDateTime}    add time to date    @{localDateTime}[0]-@{localDateTime}[1]-@{localDateTime}[2] ${startTime}    ${secondsBeforeFeedEnd} second
    \    ${endDateTime}    get Time    year month day hour min sec    ${endDateTime}
    \    ${endWeekDay}=    get day of week from date    @{endDateTime}[0]    @{endDateTime}[1]    @{endDateTime}[2]
    \    ${endTime}=    set variable    @{endDateTime}[3]:@{endDateTime}[4]:@{endDateTime}[5]
    \    @{edits}    Create List    <it:SUN_FD_OPEN>BLANK</it:SUN_FD_OPEN>    <it:SUN_FD_CLOSE>BLANK</it:SUN_FD_CLOSE>    <it:MON_FD_OPEN>BLANK</it:MON_FD_OPEN>    <it:MON_FD_CLOSE>BLANK</it:MON_FD_CLOSE>
    \    ...    <it:TUE_FD_OPEN>BLANK</it:TUE_FD_OPEN>    <it:TUE_FD_CLOSE>BLANK</it:TUE_FD_CLOSE>    <it:WED_FD_OPEN>BLANK</it:WED_FD_OPEN>    <it:WED_FD_CLOSE>BLANK</it:WED_FD_CLOSE>    <it:THU_FD_OPEN>BLANK</it:THU_FD_OPEN>
    \    ...    <it:THU_FD_CLOSE>BLANK</it:THU_FD_CLOSE>    <it:FRI_FD_OPEN>BLANK</it:FRI_FD_OPEN>    <it:FRI_FD_CLOSE>BLANK</it:FRI_FD_CLOSE>    <it:SAT_FD_OPEN>BLANK</it:SAT_FD_OPEN>    <it:SAT_FD_CLOSE>BLANK</it:SAT_FD_CLOSE>
    \    Modify EXL    ${useFile}    ${modifiedExlFile}    ${connectTimesIdentifier}    ${connectTimeRicDomain}    @{edits}
    \    Set Feed Time In EXL    ${modifiedExlFile}    ${modifiedExlFile}    ${connectTimesIdentifier}    ${connectTimeRicDomain}    ${startTime}
    \    ...    ${endTime}    ${startWeekDay}
    \    Run Keyword Unless    '${startWeekDay}' == '${endWeekDay}'    Set Feed Time In EXL    ${exlFile}    ${exlFile}    ${connectTimesIdentifier}
    \    ...    ${connectTimeRicDomain}    ${startTime}    ${endTime}    ${endWeekDay}
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

Inject PCAP File on UDP at MTE Box
    [Arguments]    ${intfName}    @{pcapFileList}
    [Documentation]    Start injection of the specified PCAP files on UDP transport with PCapPlybk tool at MTE box
    : FOR    ${pcapFile}    IN    @{pcapFileList}
    \    remote file should exist    ${pcapFile}
    \    ${stdout}    ${rc}    execute_command    PCapPlybk -ifile ${pcapFile} -intf ${intfName} -pps ${PLAYBACK_PPS}    return_rc=True
    \    Should Be Equal As Integers    ${rc}    0

Insert ICF
    [Arguments]    ${insertFile}    ${serviceName}
    ${returnCode}    ${returnedStdOut}    ${command}    Run FmsCmd    ${CHE_IP}    insert    --InputFile ${insertFile}
    ...    --HandlerName ${MTE}    --Services ${serviceName}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Load All EXL Files
    [Arguments]    ${service}    ${headendIP}    @{optargs}
    [Documentation]    Loads all EXL files for a given service using FMSCMD. The FMS files for the given service must be on the local machine. The input parameters to this keyword are the FMS service name and headend's IP.
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
    ${mteConfigFile}=    Get MTE Config File
    @{connectTimesIdentifierList}=    Get ConnectTimesIdentifier    ${mteConfigFile}    ${EMPTY}
    @{highActivityIdentifierList}=    Get HighActivityTimesIdentifier    ${mteConfigFile}
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
    wait SMF log does not contain    Drop message sent for    10    600

Load Single EXL File
    [Arguments]    ${exlFile}    ${service}    ${headendIP}    @{optargs}
    [Documentation]    Loads a single EXL file using FMSCMD. The EXL file must be on the local machine. Inputs for this keyword are the EXL Filename including the path, the FMS service and the headend's IP.
    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd    ${headendIP}    Process    --Services ${service}
    ...    --InputFile "${exlFile}"    @{optargs}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS file \ ${returnedStdOut}

Manual ClosingRun for ClosingRun Rics
    [Arguments]    ${servicename}
    @{closingrunRicList}    Get RIC List From StatBlock    Closing Run
    : FOR    ${closingrunRicName}    IN    @{closingrunRicList}
    \    ${currentDateTime}    get date and time
    \    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd    ${CHE_IP}    ClsRun
    \    ...    --RIC ${closingrunRicName}    --Services ${serviceName}    --Domain MARKET_PRICE    --ClosingRunOperation Invoke    --HandlerName ${MTE}
    \    wait SMF log message after time    ClosingRun.*?CloseItemGroup.*?Found [0-9]* closeable items out of [0-9]* items    ${currentDateTime}    2    60

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
    Set Suite Variable    ${CHE_IP}    ${ip}
    start smf
    setUtilPath
    Set 24x7 Feed And Trade Time And No Holidays
    Start MTE
    ${memUsage}    get memory usage
    Run Keyword If    ${memUsage} > 90    Fail    Memory usage > 90%. This would make the system become instable during testing. Please review the FMS file set used and reduce number of Rics if possible
    [Return]    ${ret}

Persist File Should Exist
    ${res}=    search remote files    ${VENUE_DIR}    PERSIST_${MTE}.DAT    recurse=${True}
    Length Should Be    ${res}    1    PERSIST_${MTE}.DAT file not found (or multiple files found).
    Comment    Currently, GATS does not provide the Venue name, so the pattern matching Keywords must be used. If GATS provides the Venue name, then "remote file should not exist" Keywords could be used here.

Reset Sequence Numbers
    [Arguments]    @{mach_ip_list}
    [Documentation]    Reset the FH, GRS, and MTE sequence numbers on each specified machine (default is current machine).
    ...    Currently this is done by stopping and starting the components and deleting the GRS PCAP and MTE PERSIST files.
    ...    If/when a hook is provided to reset the sequence numbers without restarting the component, it should be used.
    ...    For peer testing, stop processes and delete files on all machines before restarting processes to avoid GRS peer recovery of sequence numbers.
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
    \    Stop Process    GRS
    \    Stop Process    FHController
    \    Delete GRS PCAP Files
    \    Delete Persist Files
    Comment    Then, restart everything
    : FOR    ${mach}    IN    @{new_list}
    \    Run Keyword If    '${mach}' != '${host}'    Switch To TD Box    ${mach}
    \    ${currDateTime}    get date and time
    \    Start Process    GRS
    \    Start Process    FHController
    \    Start MTE
    \    Wait SMF Log Message After Time    Finished Startup, Begin Regular Execution    ${currDateTime}
    \    Comment    We don't capture the output file, but this waits for any publishing to complete
    \    Wait For MTE Capture To Complete    5    600
    [Teardown]    Switch Connection    ${host}

Restore EXL Changes
    [Arguments]    ${serviceName}    ${exlFiles}
    [Documentation]    Reload the original version of the EXL files using Fmscmd.
    : FOR    ${file}    IN    @{exlFiles}
    \    Load Single EXL File    ${file}    ${serviceName}    ${CHE_IP}
    [Teardown]

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
    ${ddnreqLabelfilepath}=    search remote files    ${BASE_DIR}    ddnReqLabels.xml    recurse=${True}
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
    ${ddnreqLabelfilepath}=    search remote files    ${BASE_DIR}    ddnReqLabels.xml    recurse=${True}
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
    ${mteConfigFile}=    Get MTE Config File
    @{connectTimesIdentifierList}=    Get ConnectTimesIdentifier    ${mteConfigFile}    ${EMPTY}
    @{highActivityIdentifierList}=    Get HighActivityTimesIdentifier    ${mteConfigFile}
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
    modify EXL    ${srcFile}    ${dstFile}    ${ric}    ${domain}    <it:${feedDay}_FD_OPEN>${startTime}</it:${feedDay}_FD_OPEN>
    modify EXL    ${dstFile}    ${dstFile}    ${ric}    ${domain}    <it:${feedDay}_FD_CLOSE>${endTime}</it:${feedDay}_FD_CLOSE>

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
    @{files}=    backup remote cfg file    ${VENUE_DIR}    ${configFile}
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

Start MTE
    [Documentation]    Start the MTE and wait for initialization to complete.
    ...    Then load the state EXL files (that were modified by suite setup to set 24x7 feed and trade time).
    ...
    ...    If Recon is changed to set ResendFM=0 in the MTE config file, instead of loading just the state EXL files, this will need to load all of the EXL files (if they have not already been loaded). \ With ResendFM=1, we need to wait for FMS reorg to finish, and then load the state EXL files to override the ones loaded from the FMS server.
    ${result}=    find processes by pattern    MTE -c ${MTE}
    ${len}=    Get Length    ${result}
    Run keyword if    ${len} != 0    wait for HealthCheck    ${MTE}    IsLinehandlerStartupComplete    waittime=5    timeout=600
    Run keyword if    ${len} != 0    Load All State EXL Files
    Return from keyword if    ${len} != 0
    run commander    process    start ${MTE}
    wait for process to exist    MTE -c ${MTE}
    wait for HealthCheck    ${MTE}    IsLinehandlerStartupComplete    waittime=5    timeout=600
    Wait For FMS Reorg
    Load All State EXL Files

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
    wait for process to not exist    MTE -c ${MTE}

Stop Process
    [Arguments]    ${process}
    [Documentation]    Stop process, argument is the process name
    run commander    process    stop ${process}
    wait for process to not exist    ${process}

Suite Setup
    [Documentation]    Do test suite level setup, e.g. things that take time and do not need to be repeated for each test case.
    ...    Make sure the CHE_IP machine has the LIVE MTE instance.
    Should Not be Empty    ${CHE_IP}
    ${ret}    MTE Machine Setup    ${CHE_IP}
    Set Suite Variable    ${CHE_A_Session}    ${ret}
    ${ip_list}    Create List
    Run Keyword If    '${CHE_A_IP}' != '' and '${CHE_A_IP}' != 'null'    Append To List    ${ip_list}    ${CHE_A_IP}
    Run Keyword If    '${CHE_B_IP}' != '' and '${CHE_B_IP}' != 'null'    Append To List    ${ip_list}    ${CHE_B_IP}
    ${master_ip}    get master box ip    ${ip_list}
    Run Keyword If    '${CHE_IP}'=='${CHE_A_IP}'    switch MTE LIVE STANDBY status    A    LIVE    ${master_ip}
    ...    ELSE IF    '${CHE_IP}'=='${CHE_B_IP}'    switch MTE LIVE STANDBY status    B    LIVE    ${master_ip}
    ...    ELSE    Fail    CHE_IP does not equal CHE_A_IP or CHE_B_IP in VenueVariables
    Verify MTE State In Specific Box    ${CHE_IP}    LIVE
    [Return]    ${ret}

Suite Setup Two TD Boxes
    [Documentation]    Setup 2 Sessions for 2 Peer Thunderdome Boxes
    Should Not be Empty    ${CHE_A_IP}
    Should Not be Empty    ${CHE_B_IP}
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
    close all connections
    ${localCfgFile}=    Get Variable Value    ${LOCAL_MTE_CONFIG_FILE}
    Run Keyword If    '${localCfgFile}' != 'None'    Remove File    ${localCfgFile}
    ${localCfgFile}=    Get Variable Value    ${LOCAL_MANGLING_CONFIG_FILE}
    Run Keyword If    '${localCfgFile}' != 'None'    Remove File    ${localCfgFile}

Switch To TD Box
    [Arguments]    ${ip}
    [Documentation]    To switch the current ssh session to specific CHE_X_IP
    ${switchBox}    Run Keyword If    '${ip}' == '${CHE_A_IP}'    set variable    ${CHE_A_Session}
    ...    ELSE IF    '${ip}' == '${CHE_B_IP}'    set variable    ${CHE_B_Session}
    ...    ELSE IF    '${ip}' == '${PLAYBACK_MACHINE_IP}'    set variable    ${Playback_Session}
    ...    ELSE    Fail    Invaild IP
    Set Suite Variable    ${CHE_IP}    ${ip}
    switch connection    ${switchBox}

Validate MTE Capture Against FIDFilter
    [Arguments]    ${pcapfile}    ${contextId}    ${constit}
    [Documentation]    validate MTE pcap capture against content in FIDFilter.txt
    get remote file    ${pcapfile}    ${LOCAL_TMP_DIR}/capture_local.pcap
    verify fid in fidfilter by contextId and constit against pcap    ${LOCAL_TMP_DIR}/capture_local.pcap    ${contextId}    ${constit}
    delete remote files    ${pcapfile}
    Remove Files    ${LOCAL_TMP_DIR}/capture_local.pcap
    [Teardown]

Validate MTE Capture Within FID Range For Constituent
    [Arguments]    ${pcapfile}    ${constit}    @{fid_range}
    get remote file    ${pcapfile}    ${LOCAL_TMP_DIR}/capture_local.pcap
    verify fid in range by constit against pcap    ${LOCAL_TMP_DIR}/capture_local.pcap    ${constit}    @{fid_range}
    delete remote files    ${pcapfile}
    Remove Files    ${LOCAL_TMP_DIR}/capture_local.pcap

Verify MTE State In Specific Box
    [Arguments]    ${che_ip}    ${state}    ${waittime}=5    ${timeout}=150
    ${host}=    get current connection index
    Switch To TD Box    ${che_ip}
    verify MTE state    ${state}    ${waittime}    ${timeout}
    Switch Connection    ${host}

Verify RIC In MTE Cache
    [Arguments]    ${ric}
    ${ricFields}=    Get All Fields For RIC From Cache    ${ric}
    Should Not Be Empty    ${ricFields}    RIC ${ric} not found in MTE cache
    ${ric}=    set variable    ${ricFields['RIC']}
    ${publish_key}=    set variable    ${ricFields['PUBLISH_KEY']}
    [Teardown]
    [Return]    ${ric}    ${publish_key}

Verify RIC Not In MTE Cache
    [Arguments]    ${ric}
    ${ricFields}=    Get All Fields For RIC From Cache    ${ric}
    Should Be Empty    ${ricFields}    RIC ${ric} found in MTE cache

Verify RIC Is Dropped In MTE Cache
    [Arguments]    ${ric}
    [Documentation]    If a RIC be dropped, it will be non-publishable and be in InDeletionDelay state
    ${allricFields}=    get all fields for ric from cache    ${ric}
    Should Be Equal    ${allricFields['PUBLISHABLE']}    FALSE
    Should Be True    ${allricFields['NON_PUBLISHABLE_REASONS'].find('InDeletionDelay')} != -1

Verfiy Item Persisted
    [Arguments]    ${ric}=${EMPTY}    ${sic}=${EMPTY}    ${domain}=${EMPTY}
    [Documentation]    Dump persist file to XML and check if ric, sic and/or domain items exist in MTE persist file.
    ${cacheDomainName}=    Remove String    ${domain}    _
    ${pmatDomain}=    Run Keyword If    '${cacheDomainName}'!='${EMPTY}'    Map to PMAT Numeric Domain    ${cacheDomainName}
    @{pmatOptargs}=    Gen Pmat Cmd Args    ${ric}    ${sic}    ${pmatDomain}
    ${pmatDumpfile}=    Dump Persist File To XML    @{pmatOptargs}
    Verify Item in Persist Dump File    ${pmatDumpfile}    ${ric}    ${sic}    ${cacheDomainName}
    Remove Files    ${pmatDumpfile}

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
