import logging

from flask import Blueprint, redirect, render_template, request, url_for

from xssp_rest.frontend.dashboard.forms import XsspForm
from xssp_rest.services.xssp import XsspStrategyFactory

_log = logging.getLogger(__name__)

bp = Blueprint('dashboard', __name__)


@bp.route("/", methods=['GET', 'POST'])
def index():
    form = XsspForm()
    if form.validate_on_submit():
        # Determine which form field has the input data.
        if form.input_type.data == 'pdb_id' or \
           form.input_type.data == 'pdb_redo_id':
            data = form.pdb_id.data
        elif form.input_type.data == 'pdb_file':
            _log.debug("User uploaded '{}'".format(
                request.files['file_'].filename))
            data = request.files['file_'].read()
        elif form.input_type.data == 'sequence':
            data = form.sequence.data
        else:
            raise ValueError("Unexpected input type '{}'".format(
                form.input_type.data))

        # Create and run the job via the strategy for the given input and
        # output types.
        _log.debug("Input type '{}' and output type '{}'".format(
            form.input_type.data, form.output_type.data))

        strategy = XsspStrategyFactory.create(form.input_type.data,
                                              form.output_type.data)
        _log.debug("Using '{}'".format(strategy.__class__.__name__))
        celery_id = strategy(data)
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
