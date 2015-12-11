# Parse all the .robot files under the current directory and
# generate a HTML table containing three columns, Test Suite, Test Case, Description

import glob
import re
from html import HTML

robotFiles = glob.glob('*.robot')
doc = HTML().html()
head = doc.head()
head.title('Thunderdome Functional Test Cases in Recon')
body = doc.body()

intro = body.p
intro.h1('Thunderdome Automated Functional Test cases')
intro.text('Click on the Test Suite name for details on the test steps (Keywords) for each test in the suite.')

tbl = body.table(border='1')
row = tbl.tr(style="text-align: center; background-color: #6690bc; color: #ffffff; padding: 2px;", valign="middle")
row.th('Test Suite')
row.th('Test Name')
row.th('Description')
for filename in robotFiles:
    if filename == 'core.robot':
        continue
    # print '\nDEBUG: Test Suite: %s' %filename
    testSuite = filename.replace('.robot','')
    testCase = []
    testDesc = []
    with open(filename, 'r') as f:
        while True:
            line = f.readline()
            if not line or (line.strip() == '*** Test Cases ***'):
                break
        line = f.readline()
        while True:
            if not line or (line.startswith('***')):
                # End of Test section, Start of next section
                break
            if line[0].isspace():
                # in body of test, ignore this line
                line = f.readline()
            else:
                # Start of Test Definition
                # print 'DEBUG: Test: %s' %line.rstrip()
                testCase.append(line.rstrip())
                desc = []   # initial empty Description
                line = f.readline()
                if line.strip().startswith('[Documentation]'):
                    docLine = re.sub(r'.*\]\s*','',line.rstrip(),count=1)
                    # print 'DEBUG: Documentation: %s' %docLine
                    desc.append(docLine)
                    while True:
                        line = f.readline()
                        if line.strip().startswith('...'):
                            docLine = re.sub(r'\s*\.\.\.\s*','',line.rstrip())
                            # print 'DEBUG: (continued)   : %s' %docLine
                            desc.append(docLine)
                        else:
                            break
                testDesc.append(desc)
        numTests = len(testCase)
        if numTests:
            for i in range(0,numTests):
                row = tbl.tr
                if i == 0:
                    suiteDoc = testSuite + '.html'
                    row.td(rowspan=str(numTests)).a(href=str(suiteDoc)).text(testSuite)
                row.td(testCase[i])
                # Add description one line at a time and add link to each html reference
                dCell = row.td('')
                dText = testDesc[i]
                for i in range(0,len(dText)):
                    if i > 0:
                        dCell.br #preserve newlines in description
                    dLine = dText[i]
                    matches = re.finditer(r'http[s]*://\S*', dLine)
                    beg = 0
                    for m in matches:
                        dCell += dLine[beg:m.start()]
                        dCell.a(href=str(m.group(0))).text(m.group(0))
                        beg = m.end()
                    dCell += dLine[beg:]
print doc
                        