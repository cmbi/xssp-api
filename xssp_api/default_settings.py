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
XSSP_DATABANKS = ['/mnt/cmbi4/fasta/uniprot_sprot.fasta',
                  '/mnt/cmbi4/fasta/uniprot_trembl.fasta']

# uploads
UPLOAD_FOLDER = '/tmp/xssp-api/uploads'
ALLOWED_EXTENSIONS = ['bdb', 'bz2', 'cif', 'ent', 'gz', 'mcif', 'pdb']

# HSSP and DSSP databank locations
DSSP_ROOT = '/mnt/cmbi4/dssp/'
DSSP_REDO_ROOT = '/mnt/cmbi4/dssp_redo/'
HSSP_ROOT = '/mnt/cmbi4/hssp/'
HG_HSSP_ROOT = '/mnt/cmbi4/hg-hssp'
HSSP_STO_ROOT = '/mnt/cmbi4/hssp3/'

# Database
MONGODB_URI = 'mongodb://xsspapi_mongo_1'
MONGODB_DB_NAME = 'xsspapi'
