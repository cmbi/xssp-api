import logging


_log = logging.getLogger(__name__)


def create_hssp(source, data):
    _log.info("Submitting task to create HSSP from {}".format(source))

    if source == 'pdb':
        from xssp_rest.tasks import mkhssp_from_pdb
        result = mkhssp_from_pdb.delay(data)
    elif source == 'seq':
        from xssp_rest.tasks import mkhssp_from_sequence
        result = mkhssp_from_sequence.delay(data)
    else:
        raise ValueError("Unexpected source type: '{}'".format(source))

    _log.info("Task created with id '{}'".format(result.id))
    return result.id


def create_dssp(source, data):
    _log.info("Submitting task to create DSSP from {}".format(source))

    if source == 'pdb':
        from xssp_rest.tasks import mkdssp_from_pdb
        result = mkdssp_from_pdb.delay(data)
    else:
        raise ValueError("Unexpected source type: '{}'".format(source))

    _log.info("Task created with id '{}'".format(result.id))
    return result.id
