'''
Created on May 12, 2014

@author: xiaoqin.li
'''

def _rc(rc, detail=''):
    rcDict ={
             0: 'No error',
             1: 'Command not run successfully. Please check stdout, stderr further to assure its success or not.',
             2: 'file or path does not exist',
             3: 'copy fail',
             4: 'DAS not generate output file',
             5: 'FMSCMD with some error. Not all issues successed.',
             6: 'set date time fail',
             7: 'registry key or value not exist',
             8: 'add registry fail',
             9: 'delete registry fail',
             10: 'export registry fail',
             11: 'import registry fail',
             12: 'some processes not found to kill',
             13: 'FMSCMD not run successfully, not found Issued: xx, Success:xx ...information',
             14: 'create dir failure',
             15: 'path already exist'
             }
    if detail:
        print '*INFO* ErrorCode:%d,%s. Detail: %s' %(rc,rcDict[rc],detail)
    else:
        print '*INFO* ErrorCode:%d,%s' %(rc,rcDict[rc])