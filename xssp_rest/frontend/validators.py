import logging

from wtforms.validators import Required


_log = logging.getLogger(__name__)


class NotRequiredIf(Required):
    """
    Validate a field if and only if another field has not been given.
    """

    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name

        self.message = "This field is required if '{}' is not provided".format(
            other_field_name)

        super(NotRequiredIf, self).__init__(message=self.message,
                                            *args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception("No field named '{}' in form".format(
                self.other_field_name))

        if not bool(other_field.data):
            super(NotRequiredIf, self).__call__(form, field)
