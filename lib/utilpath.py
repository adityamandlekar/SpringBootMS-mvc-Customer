from utils.ssh import _search_file
from utils.version import get_version

from VenueVariables import *

class utilpath():
    """A test library providing keywords for running, starting, starting CHE processes.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()
    
    COMMANDER = ''
    HOSTMANAGER = ''
    STATBLOCKFIELDREADER = ''
    DATAVIEW = ''
    
    def setUtilPath(self):
        """Setting the Utilities paths by searching under BASE_DIR from VenueVariables
        This is called by suite setup in core.robot to make these variables available to the keywords
         """
        utilpath.COMMANDER = _search_file(BASE_DIR,'Commander',True)[0]
        utilpath.STATBLOCKFIELDREADER = _search_file(BASE_DIR,'StatBlockFieldReader',True)[0]
        utilpath.HOSTMANAGER = _search_file(BASE_DIR,'HostManager',True)[0]
        utilpath.DATAVIEW = _search_file(TOOLS_DIR,'DataView',True)[0]
