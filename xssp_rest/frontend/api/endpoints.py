import logging

from flask import Blueprint, request
from flask.json import jsonify

from xssp_rest.services.xssp import create_dssp, create_hssp


_log = logging.getLogger(__name__)

bp = Blueprint('xssp', __name__, url_prefix='/api')


@bp.route('/create/dssp/from_pdb/', methods=['POST'])
def create_dssp_from_pdb():
    celery_id = create_dssp('pdb', request.form['pdb_content'])
    return jsonify({'id': celery_id}), 202


@bp.route('/create/hssp/from_pdb/', methods=['POST'])
def create_hssp_from_pdb():
    celery_id = create_hssp('pdb', request.form['pdb_content'])
    return jsonify({'id': celery_id}), 202


@bp.route('/create/hssp/from_sequence/', methods=['POST'])
def create_hssp_from_sequence():
    celery_id = create_hssp('seq', request.form['sequence'])
    return jsonify({'id': celery_id}), 202


@bp.route('/job/<job_type>/<celery_id>/status/', methods=['GET'])
def get_dssp_from_pdb_status(job_type, celery_id):
    if job_type == 'dssp_from_pdb':
        from xssp_rest.tasks import mkdssp_from_pdb
        response = {'status': mkdssp_from_pdb.AsyncResult(celery_id).status}
    elif job_type == 'hssp_from_pdb':
        from xssp_rest.tasks import mkhssp_from_pdb
        response = {'status': mkhssp_from_pdb.AsyncResult(celery_id).status}
    elif job_type == 'hssp_from_sequence':
        from xssp_rest.tasks import mkhssp_from_sequence
        response = {'status':
                    mkhssp_from_sequence.AsyncResult(celery_id).status}
    else:
        return '', 400
    return jsonify(response)


@bp.route('/job/<job_type>/<celery_id>/result/', methods=['GET'])
def get_dssp_from_pdb_result(job_type, celery_id):
    if job_type == 'dssp_from_pdb':
        from xssp_rest.tasks import mkdssp_from_pdb
        response = {'result': mkdssp_from_pdb.AsyncResult(celery_id).get()}
    elif job_type == 'hssp_from_pdb':
        from xssp_rest.tasks import mkhssp_from_pdb
        response = {'result': mkhssp_from_pdb.AsyncResult(celery_id).get()}
    elif job_type == 'hssp_from_sequence':
        from xssp_rest.tasks import mkhssp_from_sequence
        response = {'result':
                    mkhssp_from_sequence.AsyncResult(celery_id).get()}
    else:
        return '', 400
    return jsonify(response)
