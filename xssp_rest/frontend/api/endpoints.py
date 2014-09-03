import inspect
import logging
import re

from flask import Blueprint, render_template, request
from flask.json import jsonify

from xssp_rest.services.xssp import XsspStrategyFactory


_log = logging.getLogger(__name__)

bp = Blueprint('xssp', __name__, url_prefix='/api')


# TODO: Improve docs

@bp.route('/create/<input_type>/<output_type>/')
def create_xssp(input_type, output_type):
    strategy = XsspStrategyFactory.create(input_type, output_type)
    _log.debug("Using '{}'".format(strategy.__class__.__name__))
    celery_id = strategy(request.form['data'])

    _log.info("Task created with id '{}'".format(celery_id))
    return jsonify({'id': celery_id}), 202


@bp.route('/job/<input_type>/<output_type>/<id>/status/', methods=['GET'])
def get_xssp_status(input_type, output_type, id):
    """
    Get the status of a previous job submission.

    :param id: The id returned by a call to one of the create methods.
    :return: Either PENDING, STARTED, SUCCESS, FAILURE, RETRY, or REVOKED.
    """
    # Must import here after the
    from xssp_rest.tasks import get_task
    task = get_task(input_type, output_type)
    async_result = task.AsyncResult(id)

    response = {'status': async_result.status}
    if async_result.failed():
        response.update({'message': async_result.traceback})
    return jsonify(response)


@bp.route('/job/<input_type>/<output_type>/<id>/result/', methods=['GET'])
def get_xssp_result(input_type, output_type, id):
    """
    Get the result of a previous job submission.

    :param job_type: Either dssp_from_pdb, hssp_from_pdb, or hssp_from_sequence.
    :param id: The id returned by a call to one of the create methods.
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
