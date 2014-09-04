import inspect
import logging
import re

from flask import Blueprint, render_template, request
from flask.json import jsonify

from xssp_rest.services.xssp import XsspStrategyFactory


_log = logging.getLogger(__name__)

bp = Blueprint('xssp', __name__, url_prefix='/api')


# TODO: Improve docs

@bp.route('/create/<input_type>/<output_type>/', methods=['POST'])
def create_xssp(input_type, output_type):
    """
    Create HSSP or DSSP data.

    Adds a job to a queue to produce the data in the given output_type format
    from the data pass in as the form parameter 'data' in the given input_type
    format.

    :param input_type: Either 'pdb_id', 'pdb_redo_id', 'pdb_file' or 'sequence'.
    :param output_type: Either 'hssp_hssp', 'hssp_stockholm', or 'dssp'.
    :return: The id of the job.
    """
    strategy = XsspStrategyFactory.create(input_type, output_type)
    _log.debug("Using '{}'".format(strategy.__class__.__name__))
    celery_id = strategy(request.form['data'])

    _log.info("Task created with id '{}'".format(celery_id))
    return jsonify({'id': celery_id}), 202


@bp.route('/status/<input_type>/<output_type>/<id>/', methods=['GET'])
def get_xssp_status(input_type, output_type, id):
    """
    Get the status of a previous job submission.

    :param input_type: Either 'pdb_id', 'pdb_redo_id', 'pdb_file' or 'sequence'.
    :param output_type: Either 'hssp_hssp', 'hssp_stockholm', or 'dssp'.
    :param id: The id returned by a call to the create method.
    :return: Either PENDING, STARTED, SUCCESS, FAILURE, RETRY, or REVOKED.
    """
    from xssp_rest.tasks import get_task
    task = get_task(input_type, output_type)
    async_result = task.AsyncResult(id)

    response = {'status': async_result.status}
    if async_result.failed():
        response.update({'message': async_result.traceback})
    return jsonify(response)


@bp.route('/result/<input_type>/<output_type>/<id>/', methods=['GET'])
def get_xssp_result(input_type, output_type, id):
    """
    Get the result of a previous job submission.

    :param input_type: Either 'pdb_id', 'pdb_redo_id', 'pdb_file' or 'sequence'.
    :param output_type: Either 'hssp_hssp', 'hssp_stockholm', or 'dssp'.
    :param id: The id returned by a call to the create method.
    :return: The output of the job. If the job status is not SUCCESS, this
             method returns an error.
    """
    from xssp_rest.tasks import get_task
    task = get_task(input_type, output_type)
    _log.debug("task is {}".format(task.__name__))
    response = {'result': task.AsyncResult(id).get()}

    return jsonify(response)


@bp.route('/', methods=['GET'])
def api_doc():
    fs = [create_xssp,
          get_xssp_status,
          get_xssp_result]
    docs = {}
    for f in fs:
        src = inspect.getsourcelines(f)
        m = re.search(r"@bp\.route\('([\w\/<>]*)', methods=\['([A-Z]*)']\)",
                      src[0][0])
        if not m:  # pragma: no cover
            _log.debug("Unable to document function '{}'".format(f))
            continue

        url = m.group(1)
        method = m.group(2)
        docstring = inspect.getdoc(f)
        docs[url] = (method, docstring)

    return render_template('api/docs.html', docs=docs)


@bp.route('/example', methods=['GET'])
def api_example():
    return render_template('api/example.html')
