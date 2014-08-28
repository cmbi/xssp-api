import logging

from flask import Blueprint, redirect, render_template, request, url_for

from xssp_rest.frontend.dashboard.forms import XsspForm
from xssp_rest.services.xssp import create_dssp, create_hssp

_log = logging.getLogger(__name__)

bp = Blueprint('dashboard', __name__)


@bp.route("/", methods=['GET', 'POST'])
def index():
    form = XsspForm()
    if form.validate_on_submit():
        # Get the data from either the file or the textarea
        if form.file_.data:
            _log.debug("User uploaded '{}'".format(
                request.files['file_'].filename))
            data = request.files['file_'].read()
        else:
            _log.debug("User uploaded raw data")
            data = form.data.data

        # Start the task to create the output depending on the method selected
        if form.type_.data == "hssp_from_pdb":
            celery_id = create_hssp('pdb', data)
        elif form.type_.data == "hssp_from_sequence":
            celery_id = create_hssp('seq', data)
        elif form.type_.data == "dssp_from_pdb":
            celery_id = create_dssp('pdb', data)

        return redirect(url_for('dashboard.output', method=form.type_.data,
                                celery_id=celery_id))
    return render_template("dashboard/index.html", form=form)


@bp.route("/output/<method>/<celery_id>", methods=['GET'])
def output(method, celery_id):
    return render_template("dashboard/output.html", method=method,
                           celery_id=celery_id)


@bp.errorhandler(Exception)
def exception_error_handler(error):
    return render_template('dashboard/error.html', msg=error), 500
