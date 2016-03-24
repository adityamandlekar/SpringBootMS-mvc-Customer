from __future__ import with_statement
import os
import os.path
from sets import Set

from utils.version import get_version

class mtecache():
    
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()
    
    def get_context_ids_from_cachedump(self, cachedump_file_name):  
        """Returns a set of context_ids appeared in the cachedump.csv file.
         Argument : cache dump file full path

        Examples:
        | get context ids from cachedump | cachedump file name |     
        """    
        if not os.path.exists(cachedump_file_name):
            raise AssertionError('*ERROR*  %s is not available' %cachedump_file_name)
            
        context_id_val_set = Set()
        n = 0
        try:
            with open(cachedump_file_name) as fileobj:
                for line in fileobj:
                    n = n+1
                    if n>1:
                        context_id_val = line.split(",")[6]
                        if context_id_val:
                            context_id_val_set.add(context_id_val)
                            
        except IOError:
            raise AssertionError('*ERROR* failed to open file %s' %cachedump_file_name)
            
                    
        return context_id_val_set   #Set(['3470', '3471', '2452', '1933', '1246', '1405'])
    
    def verify_cache_contains_only_configured_context_ids(self, cachedump_file_name_full_path, filter_string): 
        """Get set of context ID from cache dump file and venue xml_config file
        and verify the context id set from cache dump is subset of context id set defined in fms filter string
        Argument : cachedump file, venue configuration file
        Returns : true if dumpcache_context_ids_set <= filterstring_context_id_set
        
        Examples:
        | verify cache contains only configured context ids | cache dump file |venue configuration file   
        """       
        
        filterstring_context_id_set = self.get_context_ids_from_fms_filter_string(filter_string)
        if len(filterstring_context_id_set) == 0:
            raise AssertionError('*ERROR* cannot find context ids from fms filter string %' %filter_string)
        
        dumpcache_context_ids_set = self.get_context_ids_from_cachedump(cachedump_file_name_full_path)
        if len(dumpcache_context_ids_set) == 0:
            raise AssertionError('*ERROR* cannot found dumpcache context ids in %s' %cachedump_file_name_full_path)
        
        if dumpcache_context_ids_set <= filterstring_context_id_set:
            return True
        else:
            raise AssertionError('*ERROR* dumpcache context ids %s are not all in configured context ids %s' %(dumpcache_context_ids_set, filterstring_context_id_set))
    
    def verify_csv_files_match(self, file1, file2, ignorefids):
        """Verify two .csv files match.

        Argument ignorefids is a comma separated list of fields to ignore.
        If it is used, the first line of file must contain the field names.
        Those columns will be excluded during the comparision.
        
        Does not return a value; raises an error if any differences are found.

        Examples:
        | Verify csv Files Match  | file1  | file2  | ignorefids=CURR_SEQ_NUM,LAST_UPDATED  |
        | Verify csv Files Match  | file1  | file2  | CURR_SEQ_NUM,LAST_UPDATED             |
        """
        fileobj1= open(file1,'r')
        lines1 = fileobj1.readlines()
        fileobj1.close()
        fileobj2= open(file2,'r')
        lines2 = fileobj2.readlines()
        fileobj2.close()
        ignorelist = ignorefids.split(',')
        ignorepositions = []
        if lines1[0].find(ignorelist[0])!=-1:
            # rstrip to remove newline
            itemslist = lines1[0].rstrip().split(',')
            for item in itemslist:
                if item in ignorelist:
                    ignorepositions.append(itemslist.index(item))
        else:
            ignorepositions = ignorelist
        print '*INFO* ignoring columns %s' %ignorepositions
        
        count = 0
        NotMatchlines =[]
        if len(lines1) != len(lines2):
            raise AssertionError('*ERROR* line count differs %s:%s' %(len(lines1),len(lines2)))
        
        while count < len(lines1) and count < len(lines2):
            items1 = lines1[count].split(',')
            items2 = lines2[count].split(',')
            if len(items1) != len(items2):
                NotMatchlines.append([lines1[count],lines2[count]])
            else:
                for idx in range(len(items1)):
                    if idx not in ignorepositions and items1[idx] != items2[idx]:
                        NotMatchlines.append([lines1[count],lines2[count]])
                        break
            count = count+1
        
        if len(NotMatchlines)!=0:
            raise AssertionError('*ERROR* %s lines are different' %len(NotMatchlines))
        else:
            print '*INFO* the files are identical'         