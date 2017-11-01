from nose.tools import with_setup

import xssp_api.default_settings as settings
from xssp_api.storage import storage


def setup():
    storage.uri = settings.MONGODB_URI
    storage.db_name = settings.MONGODB_DB_NAME
    storage.connect()

def shutdown():
    pass


@with_setup(setup, shutdown)
def test_remove_olds_tasks():
    from xssp_api.tasks import remove_old_tasks

    remove_old_tasks()
