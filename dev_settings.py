# Flask
DEBUG = True
SECRET_KEY = 'development_key'

# Debug toolbar
DEBUG_TB_ENABLED = DEBUG
DEBUG_TB_INTERCEPT_REDIRECTS = False

# Email logging settings
MAIL_SERVER = "131.174.165.22"
MAIL_SMTP_PORT = 25
MAIL_FROM = "xssp-rest@cmbi.umcn.nl"
MAIL_TO = ["Jon.Black@radboudumc.nl"]

# HSSP and DSSP databank locations
DSSP_ROOT = '/mnt/cmbi4/dssp/'
DSSP_REDO_ROOT = '/mnt/cmbi4/dssp_redo/'
HSSP_ROOT = '/mnt/cmbi4/hssp/'
HSSP_STO_ROOT = '/mnt/cmbi4/hssp3/'
