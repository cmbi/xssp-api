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

from celery import current_app as celery_app
from celery.signals import setup_logging, task_prerun
from flask import current_app as flask_app

from xssp_api.frontend.validators import RE_FASTA_DESCRIPTION
from xssp_api.storage import storage

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


def should_log(exception):
    if len(exception.output.strip()) == 0:
        return False

    return "Expected record CRYST1 but found ATOM" not in exception.output and \
           "Error parsing PDB" not in exception.output


@celery_app.task(bind=True)
def mkdssp_from_pdb(self, pdb_file_path):
    """Creates a DSSP file from the given pdb file path."""

    output_path = "{}.dssp".format(pdb_file_path)

    try:
        args = ['mkdssp', pdb_file_path, output_path]
        _log.info("Running command '{}'".format(args))
        subprocess.check_output(args, stderr=subprocess.STDOUT, text=True)

        with open(output_path, 'r') as f:
            output = f.read()

    except subprocess.CalledProcessError as e:
        if should_log(e):
            _log.error("{}: {}".format(args, e.output))
        # Copy the file so developers can access the pdb content to
        # reproduce the error. The renamed file is never deleted by xssp-api.
        head, tail = os.path.split(pdb_file_path)
        error_pdb_path = os.path.join(head,
                                      '{}_{}'.format(self.request.id, tail))
        shutil.copyfile(pdb_file_path, error_pdb_path)
        _log.info("Copied '{}' to '{}'".format(pdb_file_path, error_pdb_path))
        raise RuntimeError(e.output)
    finally:
        _log.debug("Deleting PDB file '{}'".format(pdb_file_path))
        os.remove(pdb_file_path)

    return output


@celery_app.task(bind=True)
def mkhssp_from_pdb(self, pdb_file_path, output_format):
    """Creates a HSSP file from the given pdb file path."""
    try:
        args = ['mkhssp', '-i', pdb_file_path, '-a', '1', '-m', '1000']
        for d in flask_app.config['XSSP_DATABANKS']:
            args.extend(['-d', d])
        _log.info("Running command '{}'".format(args))
        output = subprocess.check_output(args, stderr=subprocess.STDOUT, text=True)

        if output_format == 'hssp_hssp':
            return _stockholm_to_hssp(output)
        else:
            return output
    except subprocess.CalledProcessError as e:
        _log.error("{}: {}".format(args, e.output))
        # Copy the file so developers can access the pdb content to
        # reproduce the error. The renamed file is never deleted by xssp-api.
        head, tail = os.path.split(pdb_file_path)
        error_pdb_path = os.path.join(head,
                                      '{}_{}'.format(self.request.id, tail))
        shutil.copyfile(pdb_file_path, error_pdb_path)
        _log.info("Copied '{}' to '{}'".format(pdb_file_path, error_pdb_path))
        raise RuntimeError(e.output)
    finally:
        _log.debug("Deleting PDB file '{}'".format(pdb_file_path))
        os.remove(pdb_file_path)


@celery_app.task
def mkhssp_from_sequence(sequence, output_format):
    """
    Creates a HSSP file from the given sequence.

    mkhssp accepts a FASTA file as input. The given sequence is saved to a
    temporary file which is passed as the input argument.

    If present, the input FASTA description line is used.
    """
    # The temporary file name must end in .fasta, otherwise mkhssp assumes it's
    # a PDB file.
    tmp_file = tempfile.NamedTemporaryFile(prefix='hssp_api_tmp',
                                           suffix='.fasta',
                                           delete=False,
                                           mode='w+t')
    _log.debug("Created tmp file '{}'".format(tmp_file.name))
    _log.info(sequence)
    try:
        with tmp_file as f:
            _log.debug("Writing data to '{}'".format(tmp_file.name))
            m = re.search(RE_FASTA_DESCRIPTION, sequence)
            if not m:
                f.write('>Input\n')
            else:
                f.write(m.group())
                sequence = re.sub(RE_FASTA_DESCRIPTION, '', sequence)
            # The fasta format recommends that all lines be less than 80 chars.
            f.write(textwrap.fill(sequence, 79))

        args = ['mkhssp', '-i', tmp_file.name, '-a', '1', '-m', '1000']
        for d in flask_app.config['XSSP_DATABANKS']:
            args.extend(['-d', d])

        try:
            _log.info("Running command '{}'".format(args))
            output = subprocess.check_output(args, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            _log.error("{}: {}".format(args, e.output))
            raise RuntimeError(e.output)

        if output_format == 'hssp_hssp':
            return _stockholm_to_hssp(output)
        else:
            return output
    except subprocess.CalledProcessError as e:
        # Celery cannot pickle a CalledProcessError. Convert to RuntimeError.
        raise RuntimeError(e.output)
    finally:
        _log.debug("Deleting tmp file '{}'".format(tmp_file.name))
        os.remove(tmp_file.name)


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
        if output_type == 'dssp':
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


def _stockholm_to_hssp(stockholm_text):
    _log.info("Converting stockholm to hssp")

    tmp_file = tempfile.NamedTemporaryFile(prefix='hssp_api_tmp',
                                           delete=False, mode='w+t')
    _log.debug("Created tmp file '{}'".format(tmp_file.name))

    try:
        with tmp_file as f:
            _log.debug("Writing text to '{}'".format(tmp_file.name))
            f.write(stockholm_text)

        _log.info("Calling hsspconv")
        args = ['hsspconv', '-i', tmp_file.name]
        _log.debug("Running command '{}'".format(args))
        output = subprocess.check_output(args, stderr=subprocess.STDOUT, text=True)

        return output
    except subprocess.CalledProcessError as e:
        _log.error("{}: {}".format(args, e.output))
        raise
    finally:
        _log.debug("Deleting tmp file '{}'".format(tmp_file.name))
        os.remove(tmp_file.name)


@celery_app.task
def remove_old_tasks():
    storage.remove('tasks', {'created_on': {'$exists': False}})
    storage.remove('tasks', {'created_on': {
        '$lt': datetime.datetime.utcnow() - datetime.timedelta(days=30)
    }})
