import logging
import os

from flask import current_app as app
from werkzeug import secure_filename

_log = logging.getLogger(__name__)


def process_request(input_type, output_type, pdb_id=None, uploaded_files=None,
                    sequence=None):
    # Save the PDB file if necessary
    file_path = None
    if input_type == 'pdb_file':
        assert 'file_' in uploaded_files
        pdb_file = uploaded_files['file_']
        assert hasattr(pdb_file, 'filename')

        filename = secure_filename(pdb_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pdb_file.save(file_path)
        _log.debug("User uploaded '{}'. File saved to {}".format(
            pdb_file.filename, file_path))

    # Create and run the job via the strategy for the given input and
    # output types.
    _log.debug("Input type '{}' and output type '{}'".format(
        input_type, output_type))

    strategy = XsspStrategyFactory.create(input_type, output_type, pdb_id,
                                          file_path, sequence)
    _log.debug("Using '{}'".format(strategy.__class__.__name__))
    celery_id = strategy()
    _log.info("Job has id '{}'".format(celery_id))

    return celery_id


class XsspStrategyFactory(object):
    @classmethod
    def create(cls, input_type, output_type, pdb_id, pdb_file_path, seq):
        if input_type == 'pdb_id':
            return PdbIdStrategy(output_type, pdb_id)
        elif input_type == 'pdb_redo_id':
            return PdbRedoIdStrategy(output_type, pdb_id)
        elif input_type == 'pdb_file':
            return PdbContentStrategy(output_type, pdb_file_path)
        elif input_type == 'sequence':
            return SequenceStrategy(output_type, seq)
        else:
            raise ValueError("Unexpected input type '{}'".format(input_type))


class PdbIdStrategy(object):
    def __init__(self, output_format, pdb_id):
        self.output_format = output_format
        self.pdb_id = pdb_id

    def __call__(self):
        from xssp_rest.tasks import get_task
        task = get_task('pdb_id', self.output_format)
        _log.debug("Calling task '{}'".format(task.__name__))

        if 'hssp' in self.output_format:
            result = task.delay(self.pdb_id, self.output_format)
        else:
            result = task.delay(self.pdb_id)
        return result.id


class PdbRedoIdStrategy(object):
    def __init__(self, output_format, pdb_redo_id):
        self.output_format = output_format
        self.pdb_redo_id = pdb_redo_id

    def __call__(self):
        from xssp_rest.tasks import get_task
        task = get_task('pdb_redo_id', self.output_format)
        _log.debug("Calling task '{}'".format(task.__name__))

        if self.output_format == 'dssp':
            result = task.delay(self.pdb_redo_id)
        return result.id


class SequenceStrategy(object):
    def __init__(self, output_format, sequence):
        self.output_format = output_format
        self.sequence = sequence

    def __call__(self):
        from xssp_rest.tasks import get_task
        task = get_task('sequence', self.output_format)
        _log.debug("Calling task '{}'".format(task.__name__))

        if 'hssp' in self.output_format:
            result = task.delay(self.sequence, self.output_format)
        return result.id


class PdbContentStrategy(object):
    def __init__(self, output_format, pdb_file_path):
        self.output_format = output_format
        self.pdb_file_path = pdb_file_path

    def __call__(self):
        from xssp_rest.tasks import get_task
        task = get_task('pdb_file', self.output_format)
        _log.debug("Calling task '{}'".format(task.__name__))

        if 'hssp' in self.output_format:
            result = task.delay(self.pdb_file_path, self.output_format)
        else:
            result = task.delay(self.pdb_file_path)
        return result.id
