from celery.schedules import crontab
from kombu import Exchange, Queue

# Celery
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER='pickle'
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_BROKER_URL = 'amqp://guest@rabbitmq'
CELERY_DEFAULT_QUEUE = 'xssp'
default_exchange = Exchange('xssp', type='direct')
CELERY_QUEUES = (
    Queue('xssp', default_exchange, routing_key='xssp'),
    Queue('mkhssp', default_exchange, routing_key='mkhssp'),
)
CELERY_RESULT_BACKEND = 'redis://redis/0'
CELERY_TRACK_STARTED = True
CELERYBEAT_SCHEDULE = {
    # Every day at midnight
    'remove_old_tasks': {
        'task': 'xssp_api.tasks.remove_old_tasks',
        'schedule': crontab(hour=0, minute=0),
    },
}

# xssp
XSSP_DATABANKS = ['/mnt/chelonium/uniprot/uniprot_sprot.fasta',
                  '/mnt/chelonium/uniprot/uniprot_trembl.fasta']

# uploads
UPLOAD_FOLDER = '/tmp/xssp-api/uploads'
ALLOWED_EXTENSIONS = ['bdb', 'bz2', 'cif', 'ent', 'gz', 'mcif', 'pdb']

# HSSP and DSSP databank locations
DSSP_ROOT = '/mnt/chelonium/dssp/'
DSSP_REDO_ROOT = '/mnt/chelonium/dssp_redo/'
HSSP_ROOT = '/mnt/chelonium/hssp/'
HG_HSSP_ROOT = '/mnt/chelonium/hg-hssp'
HSSP_STO_ROOT = '/mnt/chelonium/hssp3/'
PDB_ROOT = '/mnt/chelonium/pdb/all/'
PDB_REDO_ROOT = '/mnt/chelonium/pdb_redo/'
HSSP_STO_CACHE = "/srv/hssp3"

# Database
MONGODB_URI = 'mongodb://mongo'
MONGODB_DB_NAME = 'xssp-api'

# Blast executables
MAKEBLASTDB = '/usr/bin/makeblastdb'
BLASTP = '/usr/bin/blastp'

# Blast databanks
HG_HSSP_DATABANK = '/srv/blast/hg-hssp'
HSSP_STO_DATABANK = '/srv/blast/hssp3'

# support
ADMINISTRATOR_EMAIL = "coos.baakman@radboudumc.nl"
MAIL_SERVER = "smtp.umcn.nl"
