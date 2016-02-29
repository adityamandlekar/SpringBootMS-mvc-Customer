'''
Created on May 12, 2014

@author: xiaoqin.li
'''
import re
import os
#import xml.etree.ElementTree as ET
import xml
from xml.dom import minidom
import codecs

from utils.version import get_version
from utils.rc import _rc 

class _FMUtil:
    def keep_specified_exlobject(self, exlfilefullpath, RIC, Domain, outputfile):
        """keep the specified ric,domain exl object and remove all other exl objects.

        exlfilefullpath is the exl absolute path on local machine.\n
        RIC is the ric name in exl. Domain is the domain name.\n
        
        Return the modified exl path.

        Examples:
        | ${result} = | keep specified exlobject | c:/temp/test.exl | CB.N | MARKET_PRICE | C:/TEMP/tmp.exl |
        """
        keep=True
        return self._remove_exlobject(exlfilefullpath, RIC, Domain, keep, outputfile)
    
    def remove_specified_exlobject(self, exlfilefullpath, RIC, Domain, outputfile):
        """remove the specified exl object and keep all other exl objects.

        exlfilefullpath is the exl absolute path on local machine.\n
        RIC is the ric name in exl. Domain is the domain name.\n
        
        Return the modified exl path.

        Examples:
        | ${result} = | remove specified exlobject | c:/temp/test.exl | CB.N | MARKET_PRICE | C:/TEMP/tmp.exl |
        """
        keep=False
        return self._remove_exlobject(exlfilefullpath, RIC, Domain, keep, outputfile)

    def _remove_exlobject(self, exlfilefullpath, RIC, Domain,keep, outputfile):
        if os.path.abspath(exlfilefullpath) == os.path.abspath(outputfile):
            outputfile= os.path.abspath(os.path.dirname(outputfile)) +'\\' + 'GATS_' +os.path.basename(outputfile)
        try:

            with codecs.open(exlfilefullpath, 'r', 'utf-8') as exlfile:
                with codecs.open(outputfile, 'w', 'utf-8') as exlnewfile:
                    exlline = exlfile.readline()
                    objfind = False
                    Ricfind = False
                    Domainfind = False
                    exlobjlist = []
                    while exlline:
                        if objfind:
                            exlobjlist.append(exlline)
                            if exlline.find('</exlObject>') != -1:
                                objfind = False
                                if Domainfind and Ricfind:
                                    if not keep:
                                        exlobjlist = []
                                        Domainfind = False
                                        Ricfind = False
                                        exlline = exlfile.readline()
                                        continue
                                    else:
                                        Domainfind = False
                                        Ricfind = False
                                        exlnewfile.writelines(exlobjlist)
                                        exlobjlist = []
                                else:
                                    if not keep:
                                        Domainfind = False
                                        Ricfind = False
                                        exlnewfile.writelines(exlobjlist)
                                        exlobjlist = []
                                    else:
                                        exlobjlist = []
                                        Domainfind = False
                                        Ricfind = False
                                        exlline = exlfile.readline()
                                        continue        

                            elif exlline.find('<it:RIC>%s</it:RIC>' % RIC) != -1:
                                Ricfind = True
                            elif exlline.find('<it:DOMAIN>%s</it:DOMAIN>' % Domain) != -1:
                                Domainfind = True
                        else:
                            if exlline.find('<exlObject>') != -1:
                                exlobjlist.append(exlline)
                                objfind = True
                            else:
                                exlnewfile.write(exlline)
                        exlline = exlfile.readline()

        except IOError,e:
            raise AssertionError('*ERROR* %s' %e)
        
        return outputfile
    
    def modify_icf(self, srcfile, dstfile, ric, domain, *ModifyItem):
        """modify icf file for assigned ric and domain item.
        
        srcfile is the original file.\n
        dstfile is the modified output file.\n
        ModifyItem can be one or more items, and it supports one or multiple layers.
        For example: <it:DSPLY_NAME>xiaoqin</it:DSPLY_NAME>, <it:SCHEDULE_MON>\n<it:TIME>00:00:00</it:TIME>\n</it:SCHEDULE_MON>.
        In above example, mean change DSPLY_NAME to xiaoqin, and change SCHEDULE_MON to 00:00:00.\n
        
        Return the modified output file path.

        Examples:
        | ${result} | modify icf | c:/temp/ACLJ.icf | c:/temp/output.icf | ACLJ.JO | MARKET_PRICE | <it:EXCHANGE>test</it:EXCHANGE> | <it:TRDPRC_1>\\n         <it:outputFormat>TRWF_REAL_NOT_A_NUM</it:outputFormat>\\n         <it:value>20</it:value>\\n      </it:TRDPRC_1> |
        =>\n
        * change EXCHANGE's value to test and TRDPRC_1's value to 20\n
        """
        return self._modify_fm_file(srcfile, dstfile, 'r', ric, domain, *ModifyItem)
    
    def modify_exl(self, srcfile, dstfile, ric, domain, *ModifyItem):
        """modify exl file for assigned ric and domain item.
        if the modified item can't be found, then add it.
        
        srcfile is the original file.\n
        dstfile is the modified output file.\n
        ModifyItem can be one or more items, and it supports one or multiple layers.
        For example: <it:DSPLY_NAME>xiaoqin</it:DSPLY_NAME>, <it:SCHEDULE_MON>\n<it:TIME>00:00:00</it:TIME>\n</it:SCHEDULE_MON>.
        In above example, mean change DSPLY_NAME to xiaoqin, and change SCHEDULE_MON to 00:00:00.\n
        
        Return the modified output file path.

        Examples:
        | ${result} | modify exl |c:/temp/ACLJ.exl | c:/temp/output.exl | ACLJ.JO | MARKET_PRICE | <it:DSPLY_NAME>xiaoqin</it:DSPLY_NAME> | 
        """
        return self._modify_fm_file(srcfile, dstfile, 'exlObject', ric, domain, *ModifyItem)
    
    def modify_exl_header(self, srcfile, dstfile, *ModifyItem):
        """modify exl file header.
        
        srcfile is the original file.\n
        dstfile is the modified output file.\n
        ModifyItem can be one or more items, and it supports one or multiple layers.
        For example: <it:DSPLY_NAME>xiaoqin</it:DSPLY_NAME>, <it:SCHEDULE_MON>\n<it:TIME>00:00:00</it:TIME>\n</it:SCHEDULE_MON>.
        In above example, mean change DSPLY_NAME to xiaoqin, and change SCHEDULE_MON to 00:00:00.\n
        
        Return the modified output file path.

        Examples:
        | ${result} | modify exl header |c:/temp/ACLJ.exl | c:/temp/output.exl | <it:EXCHANGE>MP</it:EXCHANGE> | <it:ENABLED>true</it:ENABLED> |
        """
        return self._modify_fm_file(srcfile, dstfile, 'exlHeader', '', '', *ModifyItem)
    
               
    def _modify_fm_file(self, srcfile, dstfile, modifyType, ric, domain, *ModifyItem):
        '''modifyType: exlObject, exlHeader, r'''

        dom = xml.dom.minidom.parse(srcfile)  
        root = dom.documentElement  
        iteratorlist = dom.getElementsByTagName(modifyType) 
        
        if modifyType != 'exlHeader':
            #find the ric and domain parent node
            if domain.lower() == 'shellric' or domain.lower() == 'll2':
                domain = 'MARKET_PRICE'
            findric = False
            finddomain = False
            for node in iteratorlist:
                for subnode in node.childNodes:
                    if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:RIC':
                        if subnode.firstChild.data == ric:
                            findric = True
                    if subnode.nodeType == node.ELEMENT_NODE and subnode.nodeName == 'it:DOMAIN':
                        if subnode.firstChild.data == domain:
                            finddomain = True
                if findric and finddomain:
                    iteratoroot = node
                    break
            if findric == False or finddomain == False:
                raise AssertionError("*ERROR* not found %s and %s in the exl" % (ric, domain))
            
        else:
            iteratoroot = iteratorlist[0]
        
        def setvalue(node, field, value, replnodeflag):
            index= 0
            for subnode in node.childNodes:
                index = index +1
                if subnode.nodeType == node.ELEMENT_NODE:
                    if subnode.nodeName == field:
                        if replnodeflag == False:
                            subnode.firstChild.data = value
                            return True
                        else:
                            value.removeAttribute('xmlns:it')
                            node.replaceChild(value,subnode)                     
                            return True  
       
                    else:
                        result = setvalue(subnode, field, value, replnodeflag)
                        if result == True:
                            return True
            return False     
        
        pat = re.compile('<(.*?)>(.*)</.*?>', re.DOTALL)
        for mitem in ModifyItem:
            modifyflag = False
            match = pat.search(mitem)
            if match:
                field = match.group(1)
                value = match.group(2)
                tempdom = xml.dom.minidom.parseString('<%s xmlns:it="DbFieldsSchema">'%field +value + '</%s>'%field)  
                tempnode = tempdom.documentElement
                if pat.search(value):
                    # multiple layers
                    modifyflag = setvalue(iteratoroot, field, tempnode, True)
                    #print iteratoroot.childNodes.item(11).childNodes.item(1).childNodes
                else:
                    modifyflag = setvalue(iteratoroot, field, value, False)
            if modifyflag == False:
                    #raise AssertionError("*ERROR* not found field %s for %s and %s in exl" % (field, ric, domain))
                    print '*INFO* requested field %s does not exist, adding new field'%field
                    note = iteratoroot.getElementsByTagName('exlObjectFields')   
                    tempnode.removeAttribute('xmlns:it')
                    note[0].appendChild(tempnode)
            else:
                raise AssertionError("*ERROR* the format of modified item is incorrect")
        
        with codecs.open(dstfile,'w','utf-8') as out:
            dom.writexml(out,addindent='',newl='',encoding='utf-8')
        
        return dstfile
        

class FMUtilities(_FMUtil):
    """A test library providing keywords for handling FMS operations and handling exl, icf, lxl files, or other FMS related things.

    `FMUtilities` is GATS's standard library.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()
    
    




    
