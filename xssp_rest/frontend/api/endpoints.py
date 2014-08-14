import inspect
import logging
import re

from flask import Blueprint, render_template, request
from flask.json import jsonify

from xssp_rest.services.xssp import create_dssp, create_hssp


_log = logging.getLogger(__name__)

bp = Blueprint('xssp', __name__, url_prefix='/api')


@bp.route('/create/dssp/from_pdb/', methods=['POST'])
def create_dssp_from_pdb():
    """
    Create DSSP data from a PDB input string.

    :param pdb_content: The PDB data as a string.
    :return: A unique id for the job running on the server. This is used to
             retrieve the status and result.
    """
    id = create_dssp('pdb', request.form['pdb_content'])
    return jsonify({'id': id}), 202


@bp.route('/create/hssp/from_pdb/', methods=['POST'])
def create_hssp_from_pdb():
    """
    Create HSSP data from a PDB input string.

    :param pdb_content: The PDB data as a string.
    :return: A unique id for the job running on the server. This is used to
             retrieve the status and result.
    """
    id = create_hssp('pdb', request.form['pdb_content'])
    return jsonify({'id': id}), 202


@bp.route('/create/hssp/from_sequence/', methods=['POST'])
def create_hssp_from_sequence():
    """
    Create HSSP data from a sequence input string.

    :param sequence: The sequence data as a string.
    :return: A unique id for the job running on the server. This is used to
             retrieve the status and result.
    """
    id = create_hssp('seq', request.form['sequence'])
    return jsonify({'id': id}), 202


@bp.route('/job/<job_type>/<id>/status/', methods=['GET'])
def get_xssp_status(job_type, id):
    """
    Get the status of a previous job submission.

    :param job_type: Either dssp_from_pdb, hssp_from_pdb, or hssp_from_sequence.
    :param id: The id returned by a call to one of the create methods.
    :return: Either PENDING, STARTED, SUCCESS, FAILURE, RETRY, or REVOKED.
    """

    if job_type == 'dssp_from_pdb':
        from xssp_rest.tasks import mkdssp_from_pdb
        response = {'status': mkdssp_from_pdb.AsyncResult(id).status}
    elif job_type == 'hssp_from_pdb':
        from xssp_rest.tasks import mkhssp_from_pdb
        response = {'status': mkhssp_from_pdb.AsyncResult(id).status}
    elif job_type == 'hssp_from_sequence':
        from xssp_rest.tasks import mkhssp_from_sequence
        response = {'status':
                    mkhssp_from_sequence.AsyncResult(id).status}
    else:
        return '', 400
    return jsonify(response)


@bp.route('/job/<job_type>/<id>/result/', methods=['GET'])
def get_xssp_result(job_type, id):
    """
    Get the result of a previous job submission.

    :param job_type: Either dssp_from_pdb, hssp_from_pdb, or hssp_from_sequence.
    :param id: The id returned by a call to one of the create methods.
    :return: The output of the job. If the job status is not SUCCESS, this
             method returns an error.
    """
    if job_type == 'dssp_from_pdb':
        from xssp_rest.tasks import mkdssp_from_pdb
        response = {'result': mkdssp_from_pdb.AsyncResult(id).get()}
    elif job_type == 'hssp_from_pdb':
        from xssp_rest.tasks import mkhssp_from_pdb
        response = {'result': mkhssp_from_pdb.AsyncResult(id).get()}
    elif job_type == 'hssp_from_sequence':
        from xssp_rest.tasks import mkhssp_from_sequence
        response = {'result':
                    mkhssp_from_sequence.AsyncResult(id).get()}
    else:
        return '', 400
    return jsonify(response)


@bp.route('/', methods=['GET'])
def api_doc():
    fs = [create_dssp_from_pdb,
          create_hssp_from_pdb,
          create_hssp_from_sequence,
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
