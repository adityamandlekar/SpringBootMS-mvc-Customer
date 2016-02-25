*** Settings ***
Documentation     Verify QoS value when disable the NIC
Suite Setup       Suite Setup
Suite Teardown    Suite Teardown
Resource          core.robot
Variables         ../lib/VenueVariables.py

*** Test Cases ***
Watchdog QOS - MTE Egress NIC
    [Documentation]    Test the QOS value when disable MTE Egress NIC http://www.iajira.amers.ime.reuters.com/browse/CATF-1966
    ...
    ...    Test Steps
    ...    1. Verify EgressNIC:100, Total QOS:100
    ...    2. Disable DDNA, EgressNIC:50, Total QOS:0
    ...    3. Enable DDNA, EgressNIC:100, Total QOS:100
    ...    4. Disable DDNB, EgressNIC:50, Total QOS:0
    ...    5. Enable DDNB, EgressNIC:100, Total QOS:100
    ...    6. Disable both DDNA and DDNB, EgressNIC:0, Total QOS:0
    ...    7. Enable both DDNA and DDNB, EgressNIC:100, Total QOS:100
    [Setup]    QoS Case Setup
    Verify QOS for Egress NIC    100    100
    Disable NIC    DDNA
    Verify QOS for Egress NIC    50    0
    Enable NIC    DDNA
    Verify QOS for Egress NIC    100    100
    Disable NIC    DDNB
    Verify QOS for Egress NIC    50    0
    Enable NIC    DDNB
    Verify QOS for Egress NIC    100    100
    Disable NIC    DDNA
    Disable NIC    DDNB
    Verify QOS for Egress NIC    0    0
    Enable NIC    DDNA
    Enable NIC    DDNB
    Verify QOS for Egress NIC    100    100
    [Teardown]    QoS Case Teardown

Watchdog QOS - SFH Ingress NIC
    [Documentation]    Test the QOS value when disable SFH Ingress NIC http://www.iajira.amers.ime.reuters.com/browse/CATF-1968
    ...
    ...    Test Steps
    ...    1. Verify IngressNIC:100, Total QOS:100
    ...    2. Disable EXCHIPA, IngressNIC:50, Total QOS:0
    ...    3. Enable EXCHIPA, IngressNIC:100, Total QOS:100
    ...    4. Disable EXCHIPB, IngressNIC:50, Total QOS:0
    ...    5. Enable EXCHIPB, IngressNIC:100, Total QOS:100
    ...    6. Disable both EXCHIPA and EXCHIPB, IngressNIC:0, Total QOS:0
    ...    7. Enable both EXCHIPA and EXCHIPB, IngressNIC:100, Total QOS:100
    [Setup]    QoS Case Setup
    Verify QOS for Ingress NIC    100    100
    Disable NIC    EXCHIPA
    Verify QOS for Ingress NIC    50    0
    Enable NIC    EXCHIPA
    Verify QOS for Ingress NIC    100    100
    Disable NIC    EXCHIPB
    Verify QOS for Ingress NIC    50    0
    Enable NIC    EXCHIPB
    Verify QOS for Ingress NIC    100    100
    Disable NIC    EXCHIPA
    Disable NIC    EXCHIPB
    Verify QOS for Ingress NIC    0    0
    Enable NIC    EXCHIPA
    Enable NIC    EXCHIPB
    Verify QOS for Ingress NIC    100    100
    [Teardown]    QoS Case Teardown

Watchdog QOS - FMS NIC
    [Documentation]    Test the QOS value when disable FMS NIC http://www.iajira.amers.ime.reuters.com/browse/CATF-1967
    ...
    ...    Test Steps
    ...    1. Verify the FMS NIC sholud not equal to MGMT
    ...    2. Verify FMS NIC:100, Total QOS:100
    ...    3. Disable FMS NIC
    ...    4. Verify FMS NIC:0, Total QOS:0
    ...    5. Enable FMS NIC
    ...    6. Verify FMS NIC:100, Total QOS:100
    [Setup]    QoS Case Setup
    ${interfaceFM}    Get Interface Name By Alias    DB_P_FM
    ${interfaceMGMT}    Get Interface Name By Alias    MGMT
    Should Not Be Equal    ${interfaceFM}    ${interfaceMGMT}    The FMS NIC is equal to MGMT NIC
    Verify QOS for FMS NIC    100    100
    Disable NIC    DB_P_FM
    Verify QOS for FMS NIC    0    0
    Enable NIC    DB_P_FM
    Verify QOS for FMS NIC    100    100
    [Teardown]    QoS Case Teardown

*** Keywords ***
Disable NIC
    [Arguments]    ${NICName}
    [Documentation]    Disable a NIC, ${NICName} should be DDNA, DDNB, EXCHIPA, EXCHIPB, DB_P_FM
    Dictionary Should Contain Key    ${AliasAndInterfaceName}    ${NICName}
    ${interfaceName}    Get From Dictionary    ${AliasAndInterfaceName}    ${NICName}
    Enable Disable Interface    ${interfaceName}    Disable
    Append To List    ${disabledInterfaceName}    ${interfaceName}

Enable NIC
    [Arguments]    ${NICName}
    [Documentation]    Enable NIC, ${NICName} should be DDNA, DDNB, EXCHIPA, EXCHIPB, DB_P_FM
    Dictionary Should Contain Key    ${AliasAndInterfaceName}    ${NICName}
    ${interfaceName}    Get From Dictionary    ${AliasAndInterfaceName}    ${NICName}
    Enable Disable Interface    ${interfaceName}    Enable
    Remove Values From List    ${disabledInterfaceName}    ${interfaceName}

QoS Case Setup
    [Documentation]    Create suite dictionary variable, it saves the NIC Alias and Interface Name, like {'EXCHIPA':'eth0'}, and make sure all interfaces are enabled before the test
    @{disabledInterfaceName}    create list
    Set Suite Variable    @{disabledInterfaceName}
    ${AliasAndInterfaceName}    Create Dictionary
    Set Suite Variable    ${AliasAndInterfaceName}
    ${interfaceName}    Get Interface Name By Alias    DDNA
    Set To Dictionary    ${AliasAndInterfaceName}    DDNA    ${interfaceName}
    ${interfaceName}    Get Interface Name By Alias    DDNB
    Set To Dictionary    ${AliasAndInterfaceName}    DDNB    ${interfaceName}
    ${interfaceName}    Get Interface Name By Alias    EXCHIPA
    Set To Dictionary    ${AliasAndInterfaceName}    EXCHIPA    ${interfaceName}
    ${interfaceName}    Get Interface Name By Alias    EXCHIPB
    Set To Dictionary    ${AliasAndInterfaceName}    EXCHIPB    ${interfaceName}
    ${interfaceName}    Get Interface Name By Alias    DB_P_FM
    Set To Dictionary    ${AliasAndInterfaceName}    DB_P_FM    ${interfaceName}

QoS Case Teardown
    [Documentation]    Make sure all interfaces are enabled after the test
    : FOR    ${interfaceName}    IN    @{disabledInterfaceName}
    \    Enable Disable Interface    ${interfaceName}    Enable

Verify QOS for Egress NIC
    [Arguments]    ${IngressQOS}    ${TotalQOS}
    [Documentation]    Put Egress QOS and Total QOS into arguments
    Wait For QOS    A    EgressNIC    ${IngressQOS}    ${CHE_IP}
    Verify QOS Equal To Specific Value    A    Total QOS    ${TotalQOS}    ${CHE_IP}

Verify QOS for Ingress NIC
    [Arguments]    ${IngressQOS}    ${TotalQOS}
    [Documentation]    Put Ingress QOS and Total QOS into arguments
    Wait For QOS    A    IngressNIC    ${IngressQOS}    ${CHE_IP}
    Verify QOS Equal To Specific Value    A    Total QOS    ${TotalQOS}    ${CHE_IP}

Verify QOS for FMS NIC
    [Arguments]    ${IngressQOS}    ${TotalQOS}
    [Documentation]    Put FMS NIC QOS and Total QOS into arguments
    Wait For QOS    A    FMSNIC    ${IngressQOS}    ${CHE_IP}
    Verify QOS Equal To Specific Value    A    Total QOS    ${TotalQOS}    ${CHE_IP}
