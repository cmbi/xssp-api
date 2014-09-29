import logging

import bz2
import os
import re
import subprocess
import tempfile
import textwrap

from celery import current_app as celery_app
from flask import current_app as flask_app

from xssp_rest.frontend.validators import RE_FASTA_DESCRIPTION


_log = logging.getLogger(__name__)


@celery_app.task
def mkdssp_from_pdb(pdb_content):
    """
    Creates a DSSP file from the given pdb content.

    A temporary file is created to store the pdb_content because mkdssp doesn't
    accept input from stdin.
    """
    tmp_file = tempfile.NamedTemporaryFile(prefix='dssp_rest_tmp',
                                           delete=False)
    _log.debug("Created tmp file '{}'".format(tmp_file.name))

    try:
        with tmp_file as f:
            _log.debug("Writing data to '{}'".format(tmp_file.name))
            f.write(pdb_content)

        args = ['mkdssp', '-i', tmp_file.name]
        _log.info("Running command '{}'".format(args))
        output = subprocess.check_output(args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        _log.error("Error: {}".format(e.output))
        raise RuntimeError(e.output)
    finally:
        _log.debug("Deleting tmp file '{}'".format(tmp_file.name))
        os.remove(tmp_file.name)

    return output


@celery_app.task
def mkhssp_from_pdb(pdb_content, output_format):
    """
    Creates a HSSP file from the given pdb content.

    A temporary file is created to store the pdb_content because mkhssp doesn't
    accept input from stdin.
    """
    tmp_file = tempfile.NamedTemporaryFile(prefix='hssp_rest_tmp',
                                           delete=False)
    _log.debug("Created tmp file '{}'".format(tmp_file.name))

    try:
        with tmp_file as f:
            _log.debug("Writing data to '{}'".format(tmp_file.name))
            f.write(pdb_content)

        args = ['mkhssp', '-i', tmp_file.name]
        args.extend(reduce(lambda l, a: l + ['-d', a],
                           flask_app.config['XSSP_DATABANKS'],
                           []))
        _log.info("Running command '{}'".format(args))
        output = subprocess.check_output(args, stderr=subprocess.STDOUT)

        if output_format == 'hssp_hssp':
            return _stockholm_to_hssp(output)
        else:
            return output
    except subprocess.CalledProcessError as e:
        _log.error("Error: {}".format(e.output))
        raise RuntimeError(e.output)
    finally:
        _log.debug("Deleting tmp file '{}'".format(tmp_file.name))
        os.remove(tmp_file.name)


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
    tmp_file = tempfile.NamedTemporaryFile(prefix='hssp_rest_tmp',
                                           suffix='.fasta',
                                           delete=False)
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

        args = ['mkhssp', '-i', tmp_file.name]
        args.extend(reduce(lambda l, a: l + ['-d', a],
                           flask_app.config['XSSP_DATABANKS'],
                           []))
        try:
            _log.info("Running command '{}'".format(args))
            output = subprocess.check_output(args, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            _log.error("Error: {}".format(e.output))
            raise RuntimeError(e.output)

        if output_format == 'hssp_hssp':
            return _stockholm_to_hssp(output)
        else:
            return output
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
    with bz2.BZ2File(hssp_path) as f:
        hssp_content = f.read()
    return hssp_content


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
    with open(dssp_path) as f:
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
    with open(dssp_path) as f:
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
        else:
            raise ValueError("Invalid input and output combination")
    else:
        raise ValueError("Unexpected input_type '{}'".format(input_type))

    _log.debug("Got task '{}'".format(task.__name__))
    return task


def _stockholm_to_hssp(stockholm_data):
    _log.info("Converting stockholm to hssp")

    tmp_file = tempfile.NamedTemporaryFile(prefix='hssp_rest_tmp',
                                           delete=False)
    _log.debug("Created tmp file '{}'".format(tmp_file.name))

    try:
        with tmp_file as f:
            _log.debug("Writing data to '{}'".format(tmp_file.name))
            f.write(stockholm_data)

        _log.info("Calling hsspconv")
        args = ['hsspconv', '-i', tmp_file.name]
        _log.debug("Running command '{}'".format(args))
        output = subprocess.check_output(args, stderr=subprocess.STDOUT)

        return output
    except subprocess.CalledProcessError as e:
        _log.error("Error: {}".format(e.output))
        raise RuntimeError(e.output)
    finally:
        _log.debug("Deleting tmp file '{}'".format(tmp_file.name))
        os.remove(tmp_file.name)
