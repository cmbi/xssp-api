import logging

import os
import subprocess
import tempfile
import textwrap

from celery import current_app as celery_app
from flask import current_app as flask_app


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

        _log.info("Calling mkdssp")
        args = ['mkdssp', '-i', tmp_file.name]
        _log.debug("Running command '{}'".format(args))
        output = subprocess.check_output(args)
    except subprocess.CalledProcessError as e:
        _log.error("Error: {}".format(e.output))
        raise RuntimeError(e.output)
    finally:
        _log.debug("Deleting tmp file '{}'".format(tmp_file.name))
        os.remove(tmp_file.name)

    return output


@celery_app.task
def mkhssp_from_pdb(pdb_content):
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

        _log.info("Calling mkhssp")
        args = ['mkhssp', '-i', tmp_file.name]
        args.extend(reduce(lambda l, a: l + ['-d', a],
                           flask_app.config['XSSP_DATABANKS'],
                           []))
        _log.debug("Running command '{}'".format(args))
        output = subprocess.check_output(args)
    except subprocess.CalledProcessError as e:
        _log.error("Error: {}".format(e.output))
        raise RuntimeError(e.output)
    finally:
        _log.debug("Deleting tmp file '{}'".format(tmp_file.name))
        os.remove(tmp_file.name)

    return output


@celery_app.task
def mkhssp_from_sequence(sequence):
    """
    Creates a HSSP file from the given sequence.

    mkhssp accepts a fasta file as input. The given sequence is saved to a
    temporary file which is passed as the input argument.
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
            f.write('>test\n')
            # The fasta format recommends that all lines be less than 80 chars.
            f.write(textwrap.fill(sequence, 79))

        _log.info("Calling mkhssp")
        args = ['mkhssp', '-i', tmp_file.name]
        args.extend(reduce(lambda l, a: l + ['-d', a],
                           flask_app.config['XSSP_DATABANKS'],
                           []))
        try:
            _log.debug("Running command '{}'".format(args))
            output = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            _log.error("Error: {}".format(e.output))
            raise RuntimeError(e.output)
    finally:
        _log.debug("Deleting tmp file '{}'".format(tmp_file.name))
        os.remove(tmp_file.name)

    return output
