import logging

from wtforms.validators import Required, StopValidation


_log = logging.getLogger(__name__)


class NotRequiredIfOneOf(Required):
    """
    Validate a field if and only if all other fields have not been given.

    raise StopValidation without a message when other data is found for another
        field and remove prior errors from the field.
    """

    def __init__(self, other_field_names, *args, **kwargs):
        self.other_field_names = other_field_names

        self.message = ("This field is required if '{}' "
                        "{} not been provided").format(
                            "' and '".join(other_field_names),
                            "have" if len(other_field_names) > 0 else "has")

        super(NotRequiredIfOneOf, self).__init__(message=self.message,
                                                 *args, **kwargs)

    def __call__(self, form, field):
        for field_name in self.other_field_names:
            other_field = form._fields.get(field_name)
            if other_field is None:
                raise Exception("No field named '{}' in form".format(
                    field_name))

            if bool(other_field.data):
                field.errors[:] = []
                raise StopValidation()

        super(NotRequiredIfOneOf, self).__call__(form, field)
