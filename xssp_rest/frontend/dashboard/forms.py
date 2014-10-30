import re

from flask_wtf import Form
from wtforms.fields import FileField, SelectField, TextAreaField, TextField
from wtforms.validators import Regexp

from xssp_rest.frontend.validators import (FileExtension, NAminoAcids,
                                           NotRequiredIfOneOf)


RE_PDB_ID = re.compile(r"^[0-9a-zA-Z]{4}$")


class XsspForm(Form):
    input_type = SelectField(u'Input',
                             choices=[('pdb_id', 'PDB code'),
                                      ('pdb_redo_id', 'PDB_REDO code'),
                                      ('pdb_file', 'PDB file'),
                                      ('sequence', 'Sequence')])
    output_type = SelectField(u'Output',
                              choices=[('dssp', 'DSSP'),
                                       ('hssp_hssp', 'HSSP'),
                                       ('hssp_stockholm', 'HSSP (Stockholm)')])
    pdb_id = TextField(u'PDB code', [NotRequiredIfOneOf(['sequence', 'file_']),
                                     Regexp(regex=RE_PDB_ID)])
    sequence = TextAreaField(u'Sequence', [
        NotRequiredIfOneOf(['pdb_id', 'file_']),
        NAminoAcids(min=25)
    ])
    file_ = FileField(u'File', [NotRequiredIfOneOf(['pdb_id', 'sequence'])])

    def __init__(self, allowed_extensions=None, **kwargs):
        super(XsspForm, self).__init__(**kwargs)
        if allowed_extensions:
            file_field = self._fields.get('file_')
            file_field.validators.append(FileExtension(allowed_extensions))
