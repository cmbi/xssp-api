import logging
import traceback

from flask import (Blueprint, current_app as app, g, redirect, render_template,
                   request, url_for)

from xssp_api import get_version
from xssp_api.frontend.dashboard.forms import XsspForm
from xssp_api.services.xssp import process_request

_log = logging.getLogger(__name__)

bp = Blueprint('dashboard', __name__)


@bp.route("/", methods=['GET', 'POST'])
def index():
    _log.debug("request for index")
    form = XsspForm(allowed_extensions=app.config['ALLOWED_EXTENSIONS'])
    if form.validate_on_submit():
        celery_id = process_request(form.input_type.data, form.output_type.data,
                                    form.pdb_id.data, request.files,
                                    form.sequence.data)

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


@bp.route("/queue/", methods=['GET'])
def queue():
    return render_template("dashboard/queue.html")


@bp.errorhandler(Exception)
def exception_error_handler(error):  # pragma: no cover
    _log.error("Unhandled exception:\n".format(traceback.format_exc()))
    return render_template('dashboard/error.html', msg=error), 500


@bp.before_request
def before_request():
    g.xssp_version = get_version()
