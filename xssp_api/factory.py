import logging
import os
import sys
from logging.handlers import SMTPHandler, RotatingFileHandler

from celery import Celery
from flask import Flask


_log = logging.getLogger(__name__)
sh = logging.StreamHandler()
file_handler = RotatingFileHandler(os.environ["LOG_FILENAME"], maxBytes=10485760)


def create_app(settings=None):
    _log.info("Creating app")

    app = Flask(__name__, static_folder='frontend/static',
                template_folder='frontend/templates')
    app.config.from_object('xssp_api.default_settings')
    if settings:
        app.config.update(settings)
    else:  # pragma: no cover
        app.config.from_envvar('XSSP_API_SETTINGS')  # pragma: no cover

    # Set the maximum content length to 200MB. This is to allow large PDB files
    # to be sent in post requests. The largest mmCIF file found to date is
    # 149MB in size.
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 200

    # Ignore Flask's built-in logging
    # app.logger is accessed here so Flask tries to create it
    app.logger_name = "nowhere"
    app.logger

    # Configure logging.
    #
    # It is somewhat dubious to get _log from the root package, but I can't see
    # a better way. Having the email handler configured at the root means all
    # child loggers inherit it.
    from xssp_api import _log as xssp_logger

    # Only log to email during production.
    if not app.debug and not app.testing:  # pragma: no cover
        mail_handler = SMTPHandler((app.config["MAIL_SERVER"],
                                   app.config["MAIL_SMTP_PORT"]),
                                   app.config["MAIL_FROM"],
                                   app.config["MAIL_TO"],
                                   "xssp-api failed")
        mail_handler.setLevel(logging.ERROR)
        xssp_logger.addHandler(mail_handler)
        mail_handler.setFormatter(
            logging.Formatter("Message type: %(levelname)s\n" +
                              "Location: %(pathname)s:%(lineno)d\n" +
                              "Module: %(module)s\n" +
                              "Function: %(funcName)s\n" +
                              "Time: %(asctime)s\n" +
                              "Message:\n" +
                              "%(message)s"))

    # Only log to the console during development and production, but not during
    # testing.
    if app.testing:
        xssp_logger.setLevel(logging.DEBUG)
    else:
        ch = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        xssp_logger.addHandler(ch)

        if app.debug:
            xssp_logger.setLevel(logging.DEBUG)
        else:
            xssp_logger.setLevel(logging.INFO)

            # Log to file in production as well.  Log filename is loaded from
            # the environment, not from the settings file. maxBytes = 10MB.
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            xssp_logger.addHandler(file_handler)

    # Check if the upload folder exists and create it if it doesn't
    if not os.path.exists(app.config['UPLOAD_FOLDER']):  # pragma: no cover
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'])
        except OSError as ex:
            _log.error("Error creating upload folder: {}".format(ex))

    # Check that the process has permission to write in the upload folder
    try:
        test_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'test_file')
        with open(test_filename, 'w') as f:
            f.write('test')
    except OSError as ex:  # pragma: no cover
        _log.error("Unable to write to the upload folder '{}': {}".format(
            app.config['UPLOAD_FOLDER'], ex))
        sys.exit(1)
    finally:
        if os.path.exists(test_filename):
            os.remove(test_filename)

    # Use ProxyFix to correct URL's when redirecting.
    from xssp_api.middleware import ReverseProxied
    app.wsgi_app = ReverseProxied(app.wsgi_app)

    # Register jinja2 filters
    from xssp_api.frontend.filters import beautify_docstring, add_links
    app.jinja_env.filters['beautify_docstring'] = beautify_docstring
    app.jinja_env.filters['add_links'] = add_links

    # Register blueprints
    from xssp_api.frontend.api.endpoints import bp as api_bp
    from xssp_api.frontend.dashboard.views import bp as dashboard_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(dashboard_bp)

    # Database
    from xssp_api.storage import storage
    storage.uri = app.config['MONGODB_URI']
    storage.db_name = app.config['MONGODB_DB_NAME']
    storage.connect()

    return app


def create_celery_app(app):  # pragma: no cover
    _log.info("Creating celery app")

    app = app or create_app()

    celery = Celery(__name__,
                    backend='amqp',
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    import xssp_api.tasks

    return celery
