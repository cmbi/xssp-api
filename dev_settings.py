# Flask
DEBUG = True
SECRET_KEY = 'development_key'

# Debug toolbar
DEBUG_TB_ENABLED = DEBUG
DEBUG_TB_INTERCEPT_REDIRECTS = False

# Email logging settings
MAIL_SERVER = "smtp.umcn.nl"
MAIL_SMTP_PORT = 25
MAIL_FROM = "xssp-api@cmbi.umcn.nl"
MAIL_TO = ["Jon.Black@radboudumc.nl", "Coos.Baakman@radboudumc.nl"]
