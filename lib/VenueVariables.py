#---------------------------------------------
# common variables for the venue
#----------------------------------------------

# Remote Machine Settings
CHE_A_IP       = '10.35.63.188'
CHE_B_IP       = '10.35.63.102'
CHE_IP         = CHE_A_IP
CHE_PORT       = '22'
FMSCMD_PORT    = '25000'
SCWCLI_PORT    = '27000'
USERNAME       = 'root'
PASSWORD       = 'Reuters1'
MTE            = 'WIF01M'
FH             = 'WIF01F'
VENUE_DIR      = '/ThomsonReuters/Venues/'
BASE_DIR       = '/ThomsonReuters/'
REMOTE_TMP_DIR = '/tmp'
TOOLS_DIR      = '/usr'

# Playback Machine Settings
PLAYBACK_MACHINE_IP = '10.35.63.188'
PLAYBACK_PORT     = '22'
PLAYBACK_BIND_IP_A = '192.168.19.189'
PLAYBACK_BIND_IP_B = '192.168.19.188'
PLAYBACK_PPS      = '10'
PLAYBACK_USERNAME = 'root'
PLAYBACK_PASSWORD = 'Reuters1'
PLAYBACK_PCAP_DIR ='/data/wif0219.pcap'
PLAYBACK_TCP_PORT = 4527

# Local Machine Settings
LOCAL_DAS_DIR    = 'C:\\Program Files\\Reuters Test Tools\\DAS'
LOCAL_PMAT_DIR   = 'C:\\PMAT\\x64'
LOCAL_FMS_DIR    = 'D:\\tools\\FMSCMD\\config\\DataFiles\\Groups'
LOCAL_FMS_BIN    = 'D:\\tools\\FMSCMD\\bin'
LOCAL_SCWCLI_BIN = 'C:\\Program Files\\SCWWatchdog_v1.7.0\\bin'
LOCAL_TMP_DIR    = 'D:\\temp'

# My vagrant VM settings
CHE_IP     =  '10.35.63.102'
USERNAME   =  'root'
PASSWORD   =  'Reuters1'
LOCAL_TMP_DIR  = 'C:\\temp'
LOCAL_FMS_DIR = 'C:\\tools\\FMSCMD\\config\\DataFiles\\Groups'
LOCAL_FMS_BIN = 'C:\\tools\\FMSCMD\\bin'
LOCAL_SCWCLI_BIN = 'C:\\Program Files\\SCWatchdog_v1.7.0\\bin\\x64'