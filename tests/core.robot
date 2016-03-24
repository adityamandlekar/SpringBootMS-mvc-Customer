*** Settings ***
Documentation     The common set of Robot imports and keywords for Thunderdome.
...               This file should be imported as a Resource in each Thunderdome test suite.
Library           Collections
Library           OperatingSystem
Library           String
Library           DateTime
Library           LinuxCoreUtilities
Library           LinuxToolUtilities
Library           LinuxFSUtilities
Library           configfiles
Library           das
Library           dataview
Library           fidfilter
Library           fms_exl
Library           mtecache
Library           persistfile
Library           pmat
Library           scwcli
Library           trwf2messages
Library           WinFSUtilities

*** Keywords ***
Switch To TD Box
    [Arguments]    ${che_ip}
    [Documentation]    To switch the current ssh session to specific CHE_X_IP
    ${switchBox}    Run Keyword If    '${che_ip}' == '${CHE_A_IP}'    set variable    ${CHE_A_Session}
    ...    ELSE IF    '${che_ip}' == '${CHE_B_IP}'    set variable    ${CHE_B_Session}
    ...    ELSE IF    '${che_ip}' == '${PLAYBACK_MACHINE_IP}'    set variable    ${Playback_Session}
    ...    ELSE    Fail    Invaild IP
    switch connection    ${switchBox}

Suite Setup Two TD Boxes
    [Documentation]    Setup 2 Sessions for 2 Peer Thunderdome Boxes
    Should Not be Empty    ${CHE_A_IP}
    Should Not be Empty    ${CHE_B_IP}
    ${ret}    suite setup    ${CHE_A_IP}
    Set Suite Variable    ${CHE_A_Session}    ${ret}
    ${ret}    suite setup    ${CHE_B_IP}
    Set Suite Variable    ${CHE_B_Session}    ${ret}

Suite Setup
    [Arguments]    ${ip}=${CHE_IP}
    [Documentation]    Do test suite level setup, e.g. things that take time and do not need to be repeated for each test case.
    ${ret}    open connection    host=${ip}    port=${CHE_PORT}    timeout=6
    login    ${USERNAME}    ${PASSWORD}
    start smf
    setUtilPath
    Start MTE
    [Return]    ${ret}

Suite Setup with Playback
    [Documentation]    Setup Playback box and suit scope variable Playback_Session.
    Should Not be Empty    ${PLAYBACK_MACHINE_IP}
    Should Not be Empty    ${CHE_A_IP}
    ${plyblk}    open connection    host=${PLAYBACK_MACHINE_IP}    port=${PLAYBACK_PORT}    timeout=5
    login    ${PLAYBACK_USERNAME}    ${PLAYBACK_PASSWORD}
    Set Suite Variable    ${Playback_Session}    ${plyblk}
    ${ret}    suite setup    ${CHE_A_IP}
    Set Suite Variable    ${CHE_A_Session}    ${ret}

Suite Teardown
    [Documentation]    Do test suite level teardown, e.g. closing ssh connections.
    close all connections
    ${localCfgFile}=    Get Variable Value    ${LOCAL_MTE_CONFIG_FILE}
    Run Keyword If    '${localCfgFile}' != 'None'    Remove File    ${localCfgFile}
    ${localCfgFile}=    Get Variable Value    ${LOCAL_MANGLING_CONFIG_FILE}
    Run Keyword If    '${localCfgFile}' != 'None'    Remove File    ${localCfgFile}

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

Dumpcache And Copyback Result
    [Arguments]    ${destfile}    # where will the csv be copied back
    [Documentation]    Dump the MTE cache to a file and copy the file to the local temp directory.
    ${remotedumpfile}=    dump cache
    get remote file    ${remotedumpfile}    ${destfile}
    delete remote files    ${remotedumpfile}

Dump Persist File To XML
    [Arguments]    @{optargs}
    [Documentation]    Run PMAT on control PC and return the \ persist xml dump file.
    ...    optarg could be ---ric <ric> | --sic <sic> | --domain <domain> |--fids <comma-delimited-fid-list> | --meta <meta> | --encode <0|1. \ Default to 0 > | --ffile <path to XQuery-syntax-FilterFile>
    ...
    ...    Note: <domain> = 0 for MarketByOrder, 1 for MarketByPrice, 2 for MarketMaker, 3 for MarketPrice, 4 for symbolList.
    ...    \ \ \ \ <ric> = a single ric or a wide-card
    ...
    ...    PMAT Guide: https://thehub.thomsonreuters.com/docs/DOC-110727
    ${localPersistFile}=    set variable    ${LOCAL_TMP_DIR}/local_persist.dat
    ${remotePersist}=    search remote files    ${VENUE_DIR}    PERSIST_${MTE}.DAT    ${True}
    Should Be True    len(${remotePersist}) ==1
    get remote file    ${remotePersist[0]}    ${localPersistFile}
    ${pmatXmlDumpfile}=    set variable    ${LOCAL_TMP_DIR}/pmatDumpfile.xml
    Run PMAT    dump    --dll Schema_v6.dll    --db ${localPersistFile}    --outf ${pmatXmlDumpfile}    @{optargs}
    Remove Files    ${localPersistFile}
    [Return]    ${pmatXmlDumpfile}

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
    ...    1. either single ConnectTimesIdentifier if fhName is specified Or
    ...    2. list with ConnectTimesIdentifier(s) if fhName = ${Empty}
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
    return from keyword if    '${connectTimesIdentifier}' != 'NOT FOUND' and '${connectTimesIdentifier}' != 'None'    ${connectTimesIdentifier}
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
    ${highActivityTimesIdentifier}=    get MTE config value    ${mteConfigFile}    Inputs    ${FH}    FHRealtimeLine    HighActivityTimesIdentifier
    return from keyword if    '${highActivityTimesIdentifier}' != 'NOT FOUND'    ${highActivityTimesIdentifier}
    ${highActivityTimesIdentifier}=    get MTE config value    ${mteConfigFile}    HighActivityTimesRIC
    return from keyword if    '${highActivityTimesIdentifier}' != 'NOT FOUND'    ${highActivityTimesIdentifier}
    FAIL    No HighActivityTimesIdentifier found in venue config file: ${mteConfigFile}
    [Return]    ${highActivityTimesIdentifier}

Get Domain Names
    [Arguments]    ${mteConfigFile}
    [Documentation]    get the Domain names from venue config file.
    ...    returns a list of Domain names.
    ${serviceName}    Get FMS Service Name
    ${domainList}    get MTE config list by path    ${mteConfigFile}    FMS    ${serviceName}    Domain    Z
    [Return]    @{domainList}

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
    ...    MARKET_BY_ORDER, MARKET_BY_PRICE, MARKET_PRICE
    ...
    ...    Examples:
    ...    ${domain}= | get preferred Domain
    ...    ${domain}= | get preferred Domain | MARKET_BY_PRICE | MARKET_PRICE | MARKET_BY_ORDER
    Run Keyword If    len(${preferenceOrder})==0    append to list    ${preferenceOrder}    MARKET_BY_ORDER    MARKET_BY_PRICE    MARKET_PRICE
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

Inject PCAP File on UDP
    [Arguments]    @{pcapFileList}
    [Documentation]    http://www.iajira.amers.ime.reuters.com/browse/RECON-72
    ...
    ...    Switch to playback box and inject the specified PCAP files. Then switch back to original box
    ${host}=    get current connection index
    Switch Connection    ${Playback_Session}
    : FOR    ${pcapFile}    IN    @{pcapFileList}
    \    remote file should exist    ${pcapFile}
    \    ${intfName}    Get Playback NIC For PCAP File    ${pcapFile}
    \    ${stdout}    ${rc}    execute_command    tcpreplay-edit --enet-vlan=del --pps ${PLAYBACK_PPS} --intf1=${intfName} '${pcapFile}'    return_rc=True
    \    Should Be Equal As Integers    ${rc}    0
    [Teardown]    Switch Connection    ${host}

Load All EXL Files
    [Arguments]    ${service}    ${headendIP}    @{optargs}
    [Documentation]    Loads all EXL files for a given service using FMSCMD. The FMS files for the given service must be on the local machine. The input parameters to this keyword are the FMS service name and headend's IP.
    ${returnCode}    ${returnedStdOut}    ${command} =    Run FmsCmd    ${headendIP}    Recon    --Services ${service}
    ...    @{optargs}
    Should Be Equal As Integers    0    ${returnCode}    Failed to load FMS files \ ${returnedStdOut}

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

Persist File Should Exist
    ${res}=    search remote files    ${VENUE_DIR}    PERSIST_${MTE}.DAT    recurse=${True}
    Length Should Be    ${res}    1    PERSIST_${MTE}.DAT file not found (or multiple files found).
    Comment    Currently, GATS does not provide the Venue name, so the pattern matching Keywords must be used. If GATS provides the Venue name, then "remote file should not exist" Keywords could be used here.

Reset Sequence Numbers
    [Documentation]    Reset the FH, GRS, and MTE sequence numbers.
    ...    Currently this is done by stopping and starting the components and deleting the PERSIST files.
    ...    If/when a hook is provided to reset the sequence numbers without restarting the component, it should be used.
    ...
    ...    This KW also waits for any publishing due to the MTE restart/reorg to complete.
    ${currDateTime}    get date and time
    Stop MTE
    Stop Process    GRS
    Stop Process    FHController
    Delete Persist Files
    Start Process    GRS
    Start Process    FHController
    Start MTE
    Wait SMF Log Message After Time    Finished Startup, Begin Regular Execution    ${currDateTime}
    Comment    We don't capture the output file, but this waits for publishing to complete
    Wait For Capture To Complete    ${MTE}

Send TRWF2 Refresh Request
    [Arguments]    ${ric}    ${domain}    @{optargs}
    [Documentation]    Call DataView to send TRWF2 Refresh Request to MTE.
    ...    The refresh request will be sent to all possible multicast addresses for each labelID defined in venue configuration file.
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1708
    Comment    LabelID may be different across machines, so make sure we have config file for this machine.
    Set Suite Variable    ${LOCAL_MTE_CONFIG_FILE}    ${None}
    ${localVenueConfig}=    get MTE config file
    ${ddnreqLabelfilepath}=    search remote files    ${BASE_DIR}    ddnReqLabels.xml    recurse=${True}
    Length Should Be    ${ddnreqLabelfilepath}    1    ddnReqLabels.xml file not found (or multiple files found).
    ${labelfile}=    set variable    ${LOCAL_TMP_DIR}/reqLabel.xml
    get remote file    ${ddnreqLabelfilepath[0]}    ${labelfile}
    ${updatedlabelfile}=    set variable    ${LOCAL_TMP_DIR}/updated_reqLabel.xml
    remove_xinclude_from_labelfile    ${labelfile}    ${updatedlabelfile}
    @{labelIDs}=    get MTE config list by section    ${localVenueConfig}    Publishing    LabelID
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
    Remove Files    ${labelfile}    ${updatedlabelfile}
    [Return]    ${res}

Send TRWF2 Refresh Request No Blank FIDs
    [Arguments]    ${ric}    ${domain}    @{optargs}
    [Documentation]    Call DataView to send TRWF2 Refresh Request to MTE.
    ...    The refresh request will be sent to all possible multicast addresses for each labelID defined in venue configuration file.
    ...    FIDs with blank value will be excluded
    ...    http://www.iajira.amers.ime.reuters.com/browse/CATF-1708
    Comment    LabelID may be different across machines, so make sure we have config file for this machine.
    Set Suite Variable    ${LOCAL_MTE_CONFIG_FILE}    ${None}
    ${localVenueConfig}=    get MTE config file
    ${ddnreqLabelfilepath}=    search remote files    ${BASE_DIR}    ddnReqLabels.xml    recurse=${True}
    Length Should Be    ${ddnreqLabelfilepath}    1    ddnReqLabels.xml file not found (or multiple files found).
    ${labelfile}=    set variable    ${LOCAL_TMP_DIR}/reqLabel.xml
    get remote file    ${ddnreqLabelfilepath[0]}    ${labelfile}
    ${updatedlabelfile}=    set variable    ${LOCAL_TMP_DIR}/updated_reqLabel.xml
    remove_xinclude_from_labelfile    ${labelfile}    ${updatedlabelfile}
    @{labelIDs}=    get MTE config list by section    ${localVenueConfig}    Publishing    LabelID
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
    Remove Files    ${labelfile}    ${updatedlabelfile}
    [Return]    ${res}

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
    [Arguments]    ${filename}=/tmp/capture.pcap    ${ddn}=DDNA
    [Documentation]    Start capture MTE output
    ${interfaceName}=    get interface name by alias    ${ddn}
    @{IpAndPort}=    get outputAddress and port for mte
    start capture packets    ${filename}    ${interfaceName}    @{IpAndPort}

Start MTE
    [Documentation]    Start the MTE and wait for initialization to complete.
    ${result}=    find processes by pattern    MTE -c ${MTE}
    ${len}=    Get Length    ${result}
    Run keyword if    ${len} != 0    wait for HealthCheck    ${MTE}    IsLinehandlerStartupComplete    waittime=5    timeout=600
    Return from keyword if    ${len} != 0
    run commander    process    start ${MTE}
    wait for process to exist    MTE -c ${MTE}
    wait for HealthCheck    ${MTE}    IsLinehandlerStartupComplete    waittime=5    timeout=600
    Wait For FMS Reorg

Start Process
    [Arguments]    ${process}
    [Documentation]    Start process, argument is the process name
    run commander    process    start ${process}
    wait for process to exist    ${process}
    wait for StatBlock    CritProcMon    ${process}    m_IsAvailable    1

Stop Capture MTE Output
    [Arguments]    ${waittime}=5    ${timeout}=300
    [Documentation]    Stop catpure MTE output
    wait for capture to complete    ${MTE}    ${waittime}    ${timeout}
    stop capture packets

Stop MTE
    run commander    process    stop ${MTE}
    wait for process to not exist    MTE -c ${MTE}

Stop Process
    [Arguments]    ${process}
    [Documentation]    Stop process, argument is the process name
    run commander    process    stop ${process}
    wait for process to not exist    ${process}

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

Verfiy RIC Persisted
    [Arguments]    ${ric}    ${domain}
    [Documentation]    Dump persist file to XML and check if ric and domain exist in MTE persist file.
    ${cacheDomainName}=    Remove String    ${domain}    _
    ${pmatDomain}=    Map to PMAT Numeric Domain    ${cacheDomainName}
    ${pmatDumpfile}=    Dump Persist File To XML    --ric ${ric}    --domain ${pmatDomain}
    Verify RIC in Persist Dump File    ${pmatDumpfile}    ${ric}    ${cacheDomainName}
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
