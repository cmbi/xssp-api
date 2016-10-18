# Flask
DEBUG = False
SECRET_KEY = '+ei1tia^=%z&t9id276tae%*5jta&rng**+a_h=l^)c*$o#5=$'

# Debug toolbar
DEBUG_TB_ENABLED = False
DEBUG_TB_INTERCEPT_REDIRECTS = False

# Email logging settings
MAIL_SERVER = "smtp.umcn.nl"
MAIL_SMTP_PORT = 25
MAIL_FROM = "xssp-rest@cmbi.umcn.nl"
MAIL_TO = ["Jon.Black@radboudumc.nl", "Coos.Baakman@radboudumc.nl"]

# HSSP and DSSP databank locations
DSSP_ROOT = '/mnt/cmbi4/dssp/'
DSSP_REDO_ROOT = '/mnt/cmbi4/dssp_redo/'
HSSP_ROOT = '/mnt/cmbi4/hssp/'
HG_HSSP_ROOT = '/data/hg-hssp'
HSSP_STO_ROOT = '/mnt/cmbi4/hssp3/'
