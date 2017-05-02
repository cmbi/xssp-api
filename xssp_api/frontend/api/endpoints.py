import inspect
import logging
import re

from flask import Blueprint, current_app as app, render_template, request
from flask.json import jsonify

from xssp_api.frontend.dashboard.forms import XsspForm
from xssp_api.services.xssp import process_request


_log = logging.getLogger(__name__)

bp = Blueprint('xssp', __name__, url_prefix='/api')


@bp.route('/create/<input_type>/<output_type>/', methods=['POST'])
def create_xssp(input_type, output_type):
    """
    Create HSSP or DSSP data.

    Adds a job to a queue to produce the data in the given output_type format
    from the data passed. The pdb_id and sequence must be set in a form
    parameter called 'data', and the pdb_file content in a parameter called
    'file_' format.

    :param input_type: Either 'pdb_id', 'pdb_redo_id', 'pdb_file' or 'sequence'.
    :param output_type: Either 'hssp_hssp', 'hssp_stockholm', or 'dssp'.
    :return: The id of the job.
    """
    form = XsspForm(allowed_extensions=app.config['ALLOWED_EXTENSIONS'],
                    csrf_enabled=False)
    form.input_type.data = input_type
    form.output_type.data = output_type
    form.sequence.data = request.form.get('data', None)
    form.pdb_id.data = request.form.get('data', None)
    form.file_.data = request.files.get('file_', None)
    if form.validate_on_submit():
        celery_id = process_request(form.input_type.data, form.output_type.data,
                                    form.pdb_id.data, request.files,
                                    form.sequence.data)

        return jsonify({'id': celery_id}), 202
    return jsonify(form.errors), 400


@bp.route('/status/<input_type>/<output_type>/<id>/', methods=['GET'])
def get_xssp_status(input_type, output_type, id):
    """
    Get the status of a previous job submission.

    :param input_type:
        Either 'pdb_id', 'pdb_redo_id', 'pdb_file' or 'sequence'.
    :param output_type: Either 'hssp_hssp', 'hssp_stockholm', or 'dssp'.
    :param id: The id returned by a call to the create method.
    :return: Either PENDING, STARTED, SUCCESS, FAILURE, RETRY, or REVOKED.
    """
    from xssp_api.tasks import get_task
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

    :param input_type:
        Either 'pdb_id', 'pdb_redo_id', 'pdb_file' or 'sequence'.
    :param output_type: Either 'hssp_hssp', 'hssp_stockholm', or 'dssp'.
    :param id: The id returned by a call to the create method.
    :return: The output of the job. If the job status is not SUCCESS, this
             method returns an error.
    """
    from xssp_api.tasks import get_task
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


@bp.route('/examples', methods=['GET'])
def api_examples():
    return render_template('api/examples.html')  # pragma: no cover
