import os
from tempfile import mkdtemp
from shutil import rmtree

from nose.tools import with_setup

from xssp_api.application import app, celery
from xssp_api.tasks import mkhssp_from_sequence


def setup():
    cache_directory_path = mkdtemp()

    app.config["HSSP_STO_CACHE"] = cache_directory_path
    celery.conf["HSSP_STO_CACHE"] = cache_directory_path


def teardown():
    cache_directory_path = app.config["HSSP_STO_CACHE"]
    if os.path.isdir(cache_directory_path):
        rmtree(cache_directory_path)


@with_setup(setup, teardown)
def test_remove_olds_tasks():
    from xssp_api.tasks import remove_old_tasks

    remove_old_tasks()

@with_setup(setup, teardown)
def test_mkhssp_from_sequence():
    sequence = "MLPGLALLLLAAWTARALEVPTDGNAGLLAEPQIAMFCGRLNMHMNVQNGKWDSDPSGTK"

    output = mkhssp_from_sequence(sequence, "hssp_stockholm")

    assert len(output) > 0
