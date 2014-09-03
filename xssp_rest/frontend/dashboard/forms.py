from flask_wtf import Form
from wtforms.fields import FileField, SelectField, TextAreaField, TextField

from xssp_rest.frontend.validators import NotRequiredIf


class XsspForm(Form):
    input_type = SelectField(u'Input',
                             choices=[('pdb_id', 'PDB Id'),
                                      ('pdb_redo_id', 'PDB_REDO Id'),
                                      ('pdb_file', 'PDB File'),
                                      ('sequence', 'Sequence')])
    output_type = SelectField(u'Output',
                              choices=[('dssp', 'DSSP'),
                                       ('hssp_hssp', 'HSSP'),
                                       ('hssp_stockholm', 'HSSP (Stockholm)')])
    pdb_id = TextField(u'PDB Id')
    sequence = TextAreaField(u'Sequence')
    file_ = FileField(u'File')
