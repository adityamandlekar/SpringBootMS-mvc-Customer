import string

def convert_dataView_response_to_dictionary(dataview_response):
    """ capture the FID Name and FID value from DateView output which return from run_dataview

        Argument : dataview_response - stdout return from run_dataview
                   
        Return : dictionary with key=FID NAME and value=FID value
        
        Examples :
        |convert dataView response to dictionary |  response |
    """        
    
    fidsAndValuesDict = {}
    lines = dataview_response.split('\n')
    for line in lines:
        if (line.find('->') != -1):
            fidAndValue = line.split(',')                
            if (len(fidAndValue) >= 2):
                fidIdAndfidName = fidAndValue[0].split()
                if (len(fidIdAndfidName) == 3):
                    fidsAndValuesDict[fidIdAndfidName[2].strip()] = ' '.join(fidAndValue[1:]).strip()
                else:
                    raise AssertionError('*ERROR* Unexpected FID/value format found in dataview response (%s), expected format (FIDNUM -> FIDNAME, FIDVALUE)' %line) 
            else:
                raise AssertionError('*ERROR* Unexpected FID/value format found in dataview response (%s), expected format (FIDNUM -> FIDNAME, FIDVALUE)' %line)
    
    return fidsAndValuesDict

def convert_dataView_response_to_multiRIC_dictionary(dataview_response,ignoreBlank=True):
    """ capture the FID Name and FID value for each RIC from DateView output which return from run_dataview

        Argument : dataview_response - stdout return from run_dataview
                    ignoreBlank - should entries with blank values be ignored?
                   
        Return : dictionary with key=RIC value = {sub-dictionary with key=FID NAME and value=FID value}
        
        Examples :
        |convert dataView response to multiRIC dictionary |  response |
    """        
    
    ric = ''
    retDict = {}
    fidsAndValuesDict = {}
    lines = dataview_response.split('\n')
    for line in lines:
        if (line.startswith('Msg Key:')):
            if (ric):
                retDict[ric] = fidsAndValuesDict
            ric = line.split(':')[1].strip()
            fidsAndValuesDict = {}
        if (line.find('->') != -1):
            fidAndValue = line.split(',')                
            if (len(fidAndValue) >= 2):
                fidIdAndfidName = fidAndValue[0].split()
                if (len(fidIdAndfidName) == 3):
                    fidsAndValuesDict[fidIdAndfidName[2].strip()] = ' '.join(fidAndValue[1:]).strip()
                else:
                    raise AssertionError('*ERROR* Unexpected FID/value format found in dataview response (%s), expected format (FIDNUM -> FIDNAME, FIDVALUE)' %line) 
            else:
                raise AssertionError('*ERROR* Unexpected FID/value format found in dataview response (%s), expected format (FIDNUM -> FIDNAME, FIDVALUE)' %line)
    
    return retDict

def verify_mangling_from_dataview_response(dataview_response,expected_pe,expected_ricname):
    """ Based on the DataView response to check if the expected Ric could be retrieved from MTE and having expected PE value

        Argument : dataview_response - stdout return from run_dataview
                   expected_pe - a list of expected PE values
                   expected_ricname - expected RIC name
                   
        Return : N/A
        
        Examples :
        |verify mangling from dataview response |  response | [4128, 4245, 4247] | ![HSIU5
    """   
                    
    fidsAndValues = convert_dataView_response_to_dictionary(dataview_response)
    if (len(fidsAndValues) > 0):
        if (fidsAndValues.has_key('PROD_PERM')):
            isPass = False
            for pe in expected_pe: 
                if (fidsAndValues['PROD_PERM'] == pe):
                    isPass = True
                    break
            if not (isPass):
                raise AssertionError('*ERROR* Ric (%s) has PE (%s) not equal to expected value (%s) ' %(expected_ricname, fidsAndValues['PROD_PERM'], expected_pe))
        else:
            raise AssertionError('*ERROR* Missing FID (PROD_PERM) from dataview response ')
    else:
        raise AssertionError('*ERROR* Cannt retrieve Ric (%s) from MTE' %expected_ricname)
