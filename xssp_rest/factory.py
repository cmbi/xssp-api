import logging

from celery import Celery
from flask import Flask


_log = logging.getLogger(__name__)


def create_app(settings=None):
    _log.info("Creating app")

    app = Flask(__name__, static_folder='frontend/static',
                template_folder='frontend/templates')
    app.config.from_object('xssp_rest.default_settings')
    if settings:
        app.config.update(settings)
    else:  # pragma: no cover
        app.config.from_envvar('XSSP_REST_SETTINGS')  # pragma: no cover

    # Set the maximum content length to 150MB. This is to allow large PDB files
    # to be sent in post requests. The largest PDB file found to date is 109MB
    # in size.
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 150

    # Ignore Flask's built-in logging
    # app.logger is accessed here so Flask tries to create it
    app.logger_name = "nowhere"
    app.logger

    # Use ProxyFix to correct URL's when redirecting.
    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Initialise extensions
    from xssp_rest import toolbar
    toolbar.init_app(app)

    # Register jinja2 filters
    from xssp_rest.frontend.filters import beautify_docstring
    app.jinja_env.filters['beautify_docstring'] = beautify_docstring

    # Register blueprints
    from xssp_rest.frontend.api.endpoints import bp as api_bp
    from xssp_rest.frontend.dashboard.views import bp as dashboard_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(dashboard_bp)

    return app


def create_celery_app(app):
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

    import xssp_rest.tasks

    return celery
