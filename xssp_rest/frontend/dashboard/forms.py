from flask_wtf import Form
from wtforms.fields import FileField, SelectField, TextAreaField

from xssp_rest.frontend.validators import NotRequiredIf


class XsspForm(Form):
    type_ = SelectField(u'Method',
                        choices=[('hssp_from_pdb', 'HSSP from PDB'),
                                 ('hssp_from_sequence', 'HSSP from Sequence'),
                                 ('dssp_from_pdb', 'DSSP from PDB')])
    data = TextAreaField(u'Data', [NotRequiredIf('file_')])
    file_ = FileField(u'File', [NotRequiredIf('data')])
