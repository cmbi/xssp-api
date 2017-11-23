from celery.schedules import crontab
from kombu import Exchange, Queue

# Celery
CELERY_BROKER_URL = 'amqp://guest@xsspapi_rabbitmq_1'
CELERY_DEFAULT_QUEUE = 'xssp'
CELERY_QUEUES = (
    Queue('xssp', Exchange('xssp'), routing_key='xssp'),
)
CELERY_RESULT_BACKEND = 'redis://xsspapi_redis_1/0'
CELERY_TRACK_STARTED = True
CELERYBEAT_SCHEDULE = {
    # Every day at midnight
    'remove_old_tasks': {
        'task': 'xssp_api.tasks.remove_old_tasks',
        'schedule': crontab(hour=0, minute=0),
    },
}

# xssp
XSSP_DATABANKS = ['/mnt/chelonium/fasta/uniprot_sprot.fasta',
                  '/mnt/chelonium/fasta/uniprot_trembl.fasta']

# uploads
UPLOAD_FOLDER = '/tmp/xssp-api/uploads'
ALLOWED_EXTENSIONS = ['bdb', 'bz2', 'cif', 'ent', 'gz', 'mcif', 'pdb']

# HSSP and DSSP databank locations
DSSP_ROOT = '/mnt/chelonium/dssp/'
DSSP_REDO_ROOT = '/mnt/chelonium/dssp_redo/'
HSSP_ROOT = '/mnt/chelonium/hssp/'
HG_HSSP_ROOT = '/mnt/chelonium/hg-hssp'
HSSP_STO_ROOT = '/mnt/chelonium/hssp3/'

# Database
MONGODB_URI = 'mongodb://xsspapi_mongo_1'
MONGODB_DB_NAME = 'xsspapi'

# Blast executables
MAKEBLASTDB = '/usr/bin/makeblastdb'
BLASTP = '/usr/bin/blastp'

# Blast databanks
HG_HSSP_DATABANK = '/srv/blast/hg-hssp'
HSSP_STO_DATABANK = '/srv/blast/hssp3'
