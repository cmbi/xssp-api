import logging
import os

from flask import (Blueprint, current_app as app, redirect, render_template,
                   request, url_for)
from werkzeug import secure_filename

from xssp_rest.frontend.dashboard.forms import XsspForm
from xssp_rest.services.xssp import XsspStrategyFactory

_log = logging.getLogger(__name__)

bp = Blueprint('dashboard', __name__)


@bp.route("/", methods=['GET', 'POST'])
def index():
    form = XsspForm(allowed_extensions=app.config['ALLOWED_EXTENSIONS'])
    if form.validate_on_submit():
        # Save the PDB file if necessary
        file_path = None
        if form.input_type.data == 'pdb_file':
            pdb_file = request.files['file_']
            filename = secure_filename(pdb_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdb_file.save(file_path)
            _log.debug("User uploaded '{}'. File saved to {}".format(
                pdb_file.filename, file_path))

        # Create and run the job via the strategy for the given input and
        # output types.
        _log.debug("Input type '{}' and output type '{}'".format(
            form.input_type.data, form.output_type.data))

        strategy = XsspStrategyFactory.create(form.input_type.data,
                                              form.output_type.data,
                                              form.pdb_id.data,
                                              file_path,
                                              form.sequence.data)
        _log.debug("Using '{}'".format(strategy.__class__.__name__))
        celery_id = strategy()
        _log.info("Job has id '{}'".format(celery_id))

        _log.info("Redirecting to output page")
        return redirect(url_for('dashboard.output',
                                input_type=form.input_type.data,
                                output_type=form.output_type.data,
                                celery_id=celery_id))
    _log.info("Rendering index page")
    return render_template("dashboard/index.html", form=form)


@bp.route("/output/<input_type>/<output_type>/<celery_id>", methods=['GET'])
def output(input_type, output_type, celery_id):
    return render_template("dashboard/output.html",
                           input_type=input_type,
                           output_type=output_type,
                           celery_id=celery_id)


@bp.errorhandler(Exception)
def exception_error_handler(error):  # pragma: no cover
    _log.error("Unhandled exception: {}".format(error))
    return render_template('dashboard/error.html', msg=error), 500
