import re
import time

from utils.version import get_version

class WinFSUtilities():
    
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()
    
    def Modify_lines(self, oldFile, newFile, modifydic):
        """
        Modify the old contents to new contents.\n

        oldFile is the original file fullpath.\n
        newFile is the output file fullpath.\n
        modifydic is a dictionary, example: {oldContent1:newContent1, oldContent2:newContent2, ...}. 
         
        Examples:
        | Modify lines | c:/temp/template.xml | c:/temp/output.xml | {'<PE enabled="false">0</PE>': '<PE enabled="false">1</PE>','<Prefix.></Prefix.>':'<prefix>!!</Prefix>'} |
        ==>\n
        * all items are totally matched then replaced. 
        """
        fd = open(oldFile, "r")
        lines = fd.readlines()
        fd.close()
        for key in modifydic.keys():
            for i in range(len(lines)):
                if lines[i].find(key) != -1:
                    lines[i]=lines[i].replace(key, modifydic[key])
        fd = open(newFile, "w")
        fd.writelines(lines)
        fd.close()
        
    def Modify_lines_matching_pattern(self, oldFile, newFile, modifydic, case_insensitive):
        """
        Modify the old contents to new contents.\n

        oldFile is the original file fullpath.\n
        newFile is the output file fullpath.\n
        case_insensitive is True or false.\n
        modifydic is a dictionary, example: {oldContent1:newContent1, oldContent2:newContent2, ...}. Old content can be pattern. If Old content is not provided with pattern, please notice if in it contain pattern char, please use \\ before the char.\n 
         
        Examples:
        | Modify lines matching pattern | c:/temp/template.xml | c:/temp/output.xml | {'<Prefix.*>':'<Prefix>!!</Prefix>', '<PE.*>': '<PE enabled="false">1</PE>'} | ${True} |
        | Modify lines matching pattern | c:/temp/template.xml | c:/temp/output.xml | {'<PE enabled="false">0</PE>': '<PE enabled="false">1</PE>','<Prefix\\.></Prefix\\.>':'<prefix>!!</Prefix>'} | ${True} |
        ==>\n
        * pattern matching to modify
        * PE is non-pattern matching to replace, Prefix is also non-pattern, but there is . in the string, so use \\ before .
        """
        fd = open(oldFile, "r")
        lines = fd.readlines()
        fd.close()
        
        for key in modifydic.keys():
            if case_insensitive == True:
                pattern = re.compile(key, re.I)
            else:
                pattern = re.compile(key)
            for i in range(len(lines)):
                if pattern.search(lines[i]):
                    lines[i] = re.sub(pattern, modifydic[key], lines[i])
        fd = open(newFile, "w")
        fd.writelines(lines)
        fd.close()
        
    def grep_local_file(self, filePath, searchKeyWord, isPattern=True, isCaseSensitive=True, Fromline=0, timeout=0, retry_interval=0):
        """
        this keyword is used to grep keywords in a file, then return matching lines.\n

        filePath is the full path of the file.\n
        searchKeyWord is the keyword filter.\n
        isPattern is the flag indicate if searchKeyword is a normal search string or regular expression pattern.\n
        isCaseSensitive is the flag indicate if searchKeyword is case sensitive.\n
        timeout default to 0, mean not timeout wait.\n
        retry_interval is default to 20, mean every 20s will check the log once.\n
        Fromline default to 0, which mean from which line to search the content.\n
        
        The return value is a list for all the matched lines content.\n

        Examples:
        | @list | grep local file | c:/result.txt | AB\\.C | ${true} | ${true} |
        | @list | grep local file | c:/result.txt | AB.*C | ${true} | ${true} |
        | @list | grep local file | c:/result.txt | AB.C | ${false} | ${false} | 60 | 
        """
        returnMatchLines = []
        current = time.time()
        timout_value = float(timeout)
        maxtime = current + timout_value
        while (current <= maxtime):
            fileObj = open(filePath, "r")
            allLines = fileObj.readlines()
            fileObj.close()
            
            allLines=allLines[int(Fromline):]
            
            if isPattern == False:
                for line in allLines:
                    if isCaseSensitive and line.find(searchKeyWord) != -1:
                        returnMatchLines.append(line)
                    if not isCaseSensitive and line.lower().find(searchKeyWord.lower()) != -1:
                        returnMatchLines.append(line)
            else:
                if isCaseSensitive == False:
                    pattern = re.compile(searchKeyWord, re.I)
                else:
                    pattern = re.compile(searchKeyWord)
                for line in allLines:
                    match = pattern.search(line)
                    if match:
                        returnMatchLines.append(line)                
            if len(returnMatchLines) < 1:
                if timout_value == 0:
                    break
                current = time.time()
                time.sleep(float(retry_interval))
            else:
                break
            
        return returnMatchLines
        