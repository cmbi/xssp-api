import logging

from flask_debugtoolbar import DebugToolbarExtension


_VERSION = '4.1.0'


# Create the top-level logger. This is required because Flask's built-in method
# results in loggers with the incorrect level.
_log = logging.getLogger(__name__)

toolbar = DebugToolbarExtension()


def get_version():
    return _VERSION
