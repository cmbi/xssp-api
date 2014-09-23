import logging
import re

from wtforms.validators import Required, StopValidation, ValidationError


RE_SEQ = re.compile(r"^[XARNDCEQGHILKMFPSTWYVxarndceqghilkmfpstwyv]+$")


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
                        "{} not been provided.").format(
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


class NAminoAcids(object):
    """
    Validate a protein sequence field.

    raise a ValidationError if less than n amino acids have been given.
    Amino Acids can be from the set ACDEFGHIKLMNPQRSTVWXY.
    """

    def __init__(self, min=-1, len_message=None, set_message=None):
        self.min = min
        if not len_message:
            len_message = u'Must be at least {0:d} amino acids long.'.format(
                min)
        if not set_message:
            set_message = u'This field only accepts 1-letter codes from ' + \
                          'the set "ACDEFGHIKLMNPQRSTVWXY".'
        self.len_message = len_message
        self.set_message = set_message

    def __call__(self, form, field):
        if not field.data:
            raise ValidationError(self.len_message)

        # Remove whitespace and sequence numbers from the input
        seq = re.sub('\s+|\d+', '', field.data)
        if not re.search(RE_SEQ, seq):
            raise ValidationError(self.set_message)

        if not len(seq) > self.min:
            raise ValidationError(self.len_message)
