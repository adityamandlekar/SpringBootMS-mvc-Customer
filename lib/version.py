import sys

VERSION = '1.0'

def get_version(sep=' '):
    return VERSION

def get_full_version(who=''):
    sys_version = sys.version.split()[0]
    version = '%s %s (%s %s on %s)' \
        % (who, get_version(), _get_interpreter(), sys_version, sys.platform)
    return version.strip()

def _get_interpreter():
    if sys.platform.startswith('java'):
        return 'Jython'
    return 'Python'
