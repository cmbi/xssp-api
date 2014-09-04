import logging


_log = logging.getLogger(__name__)


class XsspStrategyFactory(object):
    @classmethod
    def create(cls, input_type, output_type):
        if input_type == 'pdb_id':
            return PdbIdStrategy(output_type)
        elif input_type == 'pdb_redo_id':
            return PdbRedoIdStrategy(output_type)
        elif input_type == 'pdb_file':
            return PdbContentStrategy(output_type)
        elif input_type == 'sequence':
            return SequenceStrategy(output_type)
        else:
            raise ValueError("Unexpected input type '{}'".format(input_type))


class PdbIdStrategy(object):
    def __init__(self, output_format):
        self.output_format = output_format

    def __call__(self, pdb_id):
        from xssp_rest.tasks import get_task
        task = get_task('pdb_id', self.output_format)
        _log.debug("Calling task '{}'".format(task.__name__))

        if 'hssp' in self.output_format:
            result = task.delay(pdb_id, self.output_format)
        else:
            result = task.delay(pdb_id)
        return result.id


class PdbRedoIdStrategy(object):
    def __init__(self, output_format):
        self.output_format = output_format

    def __call__(self, pdb_redo_id):
        from xssp_rest.tasks import get_task
        task = get_task('pdb_redo_id', self.output_format)
        _log.debug("Calling task '{}'".format(task.__name__))

        if self.output_format == 'dssp':
            result = task.delay(pdb_redo_id)
        return result.id


class SequenceStrategy(object):
    def __init__(self, output_format):
        self.output_format = output_format

    def __call__(self, sequence):
        from xssp_rest.tasks import get_task
        task = get_task('sequence', self.output_format)
        _log.debug("Calling task '{}'".format(task.__name__))

        if 'hssp' in self.output_format:
            result = task.delay(sequence, self.output_format)
        return result.id


class PdbContentStrategy(object):
    def __init__(self, output_format):
        self.output_format = output_format

    def __call__(self, pdb_content):
        from xssp_rest.tasks import get_task
        task = get_task('pdb_file', self.output_format)
        _log.debug("Calling task '{}'".format(task.__name__))

        if 'hssp' in self.output_format:
            result = task.delay(pdb_content, self.output_format)
        else:
            result = task.delay(pdb_content)
        return result.id
