import bz2
import logging
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import uuid
import datetime
from typing import List

from filelock import FileLock
from celery import current_app as celery_app
from celery.signals import setup_logging, task_prerun, task_failure
from flask import current_app as flask_app

from xssp_api.frontend.validators import RE_FASTA_DESCRIPTION
from xssp_api.storage import storage

from xssp_api.controllers.identify import get_identifier
from xssp_api.controllers.blast import blast_databank
from xssp_api.domain.method import is_almost_same

_log = logging.getLogger(__name__)


@setup_logging.connect
def setup_logging_handler(*args, **kwargs):
    # By default, celery creates a StreamHandler on the root logger, which
    # results in duplicate log messages.
    #
    # Handling this signals allows us to control the loggers created and
    # prevent duplicate logging.
    #
    # For now, no loggers are created in celery.
    pass


@task_failure.connect
def task_failure_handler(task_id, exception, *args, **kwargs):
    _log.exception(f"on task id: {task_id}")


tmp_dir_path = tempfile.gettempdir()

def _strip_remarks_(pdb_path: str):

    if os.path.isfile(pdb_path):

        tmp_path = os.path.join(tmp_dir_path, uuid.uuid4().hex + ".pdb")
        with open(tmp_path, 'wt') as tmp_file:
            with open(pdb_path, 'rt') as pdb_file:
                for line in pdb_file:
                    if not line.startswith("REMARK "):
                        tmp_file.write(line)

        shutil.move(tmp_path, pdb_path)


def _execute_subprocess(args: List[str]):

    _log.info("Running command '{}'".format(args))
    p = subprocess.run(args, capture_output=True, text=True)

    if p.returncode != 0:
        raise RuntimeError(f"{args} error:\n{p.stderr}")

    return p.stdout, p.stderr


def should_log(exception):
    if len(exception.output.strip()) == 0:
        return False

    return "Expected record CRYST1 but found ATOM" not in exception.output and \
           "Error parsing PDB" not in exception.output


@celery_app.task(bind=True)
def mkdssp_from_pdb(self, pdb_file_path, output_format):
    """Creates a DSSP file from the given pdb file path."""

    try:
        _strip_remarks_(pdb_file_path)

        args = ['mkdssp', '--output-format', output_format, pdb_file_path]
        output, error = _execute_subprocess(args)
        if len(output.strip()) == 0:
            raise RuntimeError(error)
    finally:
        _log.debug("Deleting PDB file '{}'".format(pdb_file_path))
        os.remove(pdb_file_path)

    return output


@celery_app.task(bind=True, queue='hssp')
def mkhssp_from_pdb(self, pdb_file_path, output_format):
    """Creates a HSSP file from the given pdb file path."""

    try:
        _strip_remarks_(pdb_file_path)

        args = ['mkhssp', '-i', pdb_file_path, '-a', '1', '-m', '1000']
        for d in flask_app.config['XSSP_DATABANKS']:
            args.extend(['-d', d])

        output, error = _execute_subprocess(args)
        if len(output.strip()) == 0:
            raise RuntimeError(error)

        if output_format == 'hssp_hssp':

            return _stockholm_to_hssp(output)
        else:
            return output
    finally:
        _log.debug("Deleting PDB file '{}'".format(pdb_file_path))
        os.remove(pdb_file_path)


@celery_app.task(queue='hssp')
def mkhssp_from_sequence(sequence, output_format):
    """
    Creates a HSSP file from the given sequence.

    mkhssp accepts a FASTA file as input. The given sequence is saved to a
    temporary file which is passed as the input argument.

    If present, the input FASTA description line is used.
    """

    # The temporary file name must end in .fasta, otherwise mkhssp assumes it's
    # a PDB file.

    sequence_id = get_identifier(sequence)
    stockholm_cache_dir = flask_app.config["HSSP_STO_CACHE"]
    stockholm_file_path = os.path.join(stockholm_cache_dir, sequence_id + ".sto.bz2")

    try:
        lock_path = stockholm_file_path + ".lock"
        with FileLock(lock_path):

            if os.path.isfile(stockholm_file_path):
                with bz2.open(stockholm_file_path, 'rt') as f:
                    output = f.read()
            else:
                tmp_file, tmp_path = tempfile.mkstemp(prefix='hssp_api_tmp', suffix='.fasta')
                os.close(tmp_file)

                with open(tmp_path, 'wt') as f:

                    _log.debug("Writing data to '{}'".format(tmp_path))
                    m = re.search(RE_FASTA_DESCRIPTION, sequence)
                    if not m:
                        f.write('>Input\n' + sequence)
                    else:
                        f.write(m.group())
                        sequence = re.sub(RE_FASTA_DESCRIPTION, '', sequence)
                    # The fasta format recommends that all lines be less than 80 chars.
                    f.write(textwrap.fill(sequence, 79))

                args = ['mkhssp', '-a', '1', '-m', '1000', '-i', tmp_path]
                for databank_path in flask_app.config['XSSP_DATABANKS']:
                    args.extend(['-d', databank_path])

                try:
                    output, error = _execute_subprocess(args)

                    # store in cache
                    if len(output) > 0:
                        with bz2.open(stockholm_file_path, 'wt') as f:
                            f.write(output)
                    else:
                        raise RuntimeError(error)
                finally:
                    os.remove(tmp_path)
    finally:
        os.remove(lock_path)

    if output_format == 'hssp_hssp':
        return _stockholm_to_hssp(output)
    else:
        return output

@celery_app.task
def get_hssp(pdb_id, output_type):
    pdb_id = pdb_id.lower()
    _log.info("Getting hssp data for '{}' in format '{}'".format(pdb_id,
                                                                 output_type))

    # Determine path to hssp file and check that it exists.
    if output_type == 'hssp_hssp':
        hssp_path = os.path.join(flask_app.config['HSSP_ROOT'],
                                 pdb_id + '.hssp.bz2')
    elif output_type == 'hssp_stockholm':
        hssp_path = os.path.join(flask_app.config['HSSP_STO_ROOT'],
                                 pdb_id + '.hssp.bz2')
    else:
        raise ValueError("Unexepected output type '{}'".format(output_type))

    if not os.path.exists(hssp_path):
        raise RuntimeError("File not found: '{}'".format(hssp_path))

    # Unzip the file and return the contents
    _log.info("Unzipping '{}'".format(hssp_path))
    with bz2.open(hssp_path, 'rt') as f:
        hssp_content = f.read()
    return hssp_content


@celery_app.task
def get_hg_hssp(sequence):
    _log.info("Getting hg-hssp data for '{}'".format(sequence))

    hits = blast_databank(sequence, flask_app.config['HG_HSSP_DATABANK'])
    for hitID in hits:
        path, chain = hitID.split(':')

        for alignment in hits[hitID]:
            _log.debug("query:  {}".format(alignment.query_alignment))
            _log.debug("subject:{}".format(alignment.subj_alignment))

            if is_almost_same(sequence, alignment):
                # Check that it still exists.
                if not os.path.exists(path):
                    continue

                # Unzip the file and return the contents
                _log.info("Unzipping '{}'".format(path))
                with bz2.open(path, 'rt') as f:
                    content = f.read()
                return content

    raise RuntimeError("No hits")


@celery_app.task
def get_dssp(pdb_id):
    pdb_id = pdb_id.lower()
    _log.info("Getting dssp data for '{}'".format(pdb_id))

    # Determine path to hssp file and check that it exists.
    dssp_path = os.path.join(flask_app.config['DSSP_ROOT'], pdb_id + '.dssp')
    if not os.path.exists(dssp_path):
        raise RuntimeError("File not found: '{}'".format(dssp_path))

    # Unzip the file and return the contents
    _log.info("Reading '{}'".format(dssp_path))
    with open(dssp_path, 'rt') as f:
        dssp_content = f.read()
    return dssp_content


@celery_app.task
def get_dssp_redo(pdb_redo_id):
    pdb_redo_id = pdb_redo_id.lower()
    _log.info("Getting dssp data for redo '{}'".format(pdb_redo_id))

    # Determine path to hssp file and check that it exists.
    dssp_path = os.path.join(flask_app.config['DSSP_REDO_ROOT'],
                             pdb_redo_id + '.dssp')
    if not os.path.exists(dssp_path):
        raise RuntimeError("File not found: '{}'".format(dssp_path))

    # Unzip the file and return the contents
    _log.info("Reading '{}'".format(dssp_path))
    with open(dssp_path, 'rt') as f:
        dssp_content = f.read()
    return dssp_content


def get_task(input_type, output_type):
    """
    Get the task for the given input_type and output_type combination.

    If the combination is not allowed, a ValueError is raised.
    """
    _log.info("Getting task for input '{}' and output '{}'".format(
        input_type, output_type))

    if input_type == 'pdb_id':
        if output_type == 'dssp':
            task = get_dssp
        else:
            task = get_hssp
    elif input_type == 'pdb_redo_id':
        if output_type == 'dssp':
            task = get_dssp_redo
        else:
            raise ValueError("Invalid input and output combination")
    elif input_type == 'pdb_file':
        if output_type == 'dssp' or output_type == 'mmcif':
            task = mkdssp_from_pdb
        else:
            task = mkhssp_from_pdb
    elif input_type == 'sequence':
        if output_type == 'hssp_hssp' or \
           output_type == 'hssp_stockholm':
            task = mkhssp_from_sequence
        elif output_type == 'hg_hssp':
            task = get_hg_hssp
        else:
            raise ValueError("Invalid input and output combination")
    else:
        raise ValueError("Unexpected input_type '{}'".format(input_type))

    _log.debug("Got task '{}'".format(task.__name__))
    return task


def _stockholm_to_hssp(stockholm_content):
    _log.info("Converting stockholm to hssp")

    tmp_file, tmp_path = tempfile.mkstemp(prefix='hssp_api_tmp', suffix='.hssp')
    os.close(tmp_file)

    try:
        with open(tmp_path, 'wt') as f:
            f.write(stockholm_content)

        args = ['hsspconv', '-i', tmp_path]

        output, error = _execute_subprocess(args)

        if len(output) == 0:
            raise RuntimeError(error)
    finally:
        os.remove(tmp_path)

    return output


@celery_app.task
def remove_old_tasks():
    storage.remove('tasks', {'created_on': {'$exists': False}})
    storage.remove('tasks', {'created_on': {
        '$lt': datetime.datetime.utcnow() - datetime.timedelta(days=30)
    }})
