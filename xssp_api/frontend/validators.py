import logging
import re
import os

from wtforms.validators import InputRequired, StopValidation, ValidationError


RE_FASTA_DESCRIPTION = re.compile(r"^>\S.*\n")
RE_SEQ = re.compile(r"^[XARNDCEQGHILKMFPSTWYVxarndceqghilkmfpstwyv]+$")


_log = logging.getLogger(__name__)


class FileExtension(object):
    """
    Validate the PDB or mmCIF file extension.

    raise ValidationError if the extension of the given filename is not
        supported.

    The extension check is case insensitive.
    """
    def __init__(self, allowed):
        self.allowed = {e.lower() for e in allowed}
        self.message = ('Only the following file extensions are ' +
                        'supported: .{}').format(' .'.join(allowed))

    def __call__(self, form, field):
        field.errors = []
        if field.data is None:
            raise ValidationError("filename not set")

        name = field.data.filename
        if '.' not in name or \
                name.rsplit('.', 1)[1].lower() not in self.allowed:
            raise ValidationError(self.message)


class OnlyRequiredIf(object):
    """
    Validate a field if and only if another field has a given value

    raise StopValidation without a message when the other field does not has the given value.
    """

    def __init__(self, other_field_name, other_field_values):
        self._other_field_name = other_field_name
        self._other_field_values = other_field_values

        self.message = "This field is required if {} is {}".format(other_field_name, ' or '.join(other_field_values))

    def __call__(self, form, field):

        other_field = form._fields.get(self._other_field_name)
        if other_field is None:
            raise Exception("No field named '{}' in form".format(self._other_field_name))

        if other_field.data not in self._other_field_values:
            raise StopValidation()


class NAminoAcids(object):
    """
    Validate a protein sequence field.

    raise ValidationError if less than min amino acids have been given.

    Amino Acids can be from the set ACDEFGHIKLMNPQRSTVWXY.
    Single sequence FASTA and lowercase 1-letter codes are also accepted.
    Whitespace, sequence numbers, and asteriks are ignored.
    """

    def __init__(self, min=-1, len_message=None, set_message=None,
                 fasta_message=None):
        self.min = min
        if not len_message:
            len_message = u'Must be at least {0:d} amino acids long.'.format(
                min)
        if not set_message:
            set_message = u'This field only accepts 1-letter codes from ' + \
                          'the set "ACDEFGHIKLMNPQRSTVWXY".'
        if not fasta_message:
            fasta_message = u'Multiple sequence FASTA input ' + \
                            'is currently not supported. ' + \
                            'The first line of FASTA input should start ' + \
                            'with ">" followed by a description.'
        self.len_message = len_message
        self.set_message = set_message
        self.fasta_message = fasta_message

    def __call__(self, form, field):
        if not field.data:
            raise ValidationError(self.len_message)

        # Remove the FASTA description line if present
        seq = re.sub(RE_FASTA_DESCRIPTION, '', field.data)
        if re.search('>', seq):
            raise ValidationError(self.fasta_message)

        # Remove whitespace, sequence numbers, and asteriks from the input
        seq = re.sub('\s+|\d+|\*', '', seq)
        if not re.search(RE_SEQ, seq):
            raise ValidationError(self.set_message)

        if len(seq) < self.min:
            raise ValidationError(self.len_message)


class PdbidExists(object):
    """
    Validate that the submitted pdb id exists as a file.

    raise ValidationError if the chosen id does not exist.
    """

    def __init__(self, pdb_root, pdbredo_root):
        self.pdb_root = pdb_root
        self.pdbredo_root = pdbredo_root

    def __call__(self, form, field):

        _log.debug("validating pdbid exists")

        input_type = form._fields.get('input_type')
        id_ = field.data

        if type(id_) != str or id_.strip() == "":
            raise ValidationError("No pdb entry for an empty id")

        whynot_url = "https://www3.cmbi.umcn.nl/WHY_NOT2/search/pdbid/%s/" % id_

        if input_type.data == 'pdb_redo_id':
            path = os.path.join(self.pdbredo_root, '%s/%s/%s_final.pdb' % (id_[1:3].lower(), id_.lower(), id_.lower()))
            if not os.path.isfile(path):
                raise ValidationError("No pdb redo entry for %s. For more info, check %s" % (id_, whynot_url))

        elif input_type.data == 'pdb_id':
            path = os.path.join(self.pdb_root, "pdb%s.ent.gz" % id_.lower())
            if not os.path.isfile(path):
                raise ValidationError("No pdb entry for %s. For more info, check %s" % (id_, whynot_url))
