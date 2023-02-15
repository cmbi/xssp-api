import re

from xssp_api import default_settings as settings
from flask_wtf import FlaskForm
from wtforms.fields import FileField, SelectField, TextAreaField, StringField, SubmitField, EmailField
from wtforms import validators

from xssp_api.frontend.validators import (FileExtension, NAminoAcids,
                                          English, NoSpam,
                                          OnlyRequiredIf, PdbidExists, OnlyAllowedIf)


RE_PDB_ID = re.compile(r"^[0-9a-zA-Z]{4}$")


class XsspForm(FlaskForm):

    input_type = SelectField(u'Input', default="pdb_id",
                             choices=[('pdb_id', 'PDB code'),
                                      ('pdb_redo_id', 'PDB_REDO code'),
                                      ('pdb_file', 'PDB file'),
                                      ('sequence', 'Sequence')])
    output_type = SelectField(u'Output', default="dssp",
                              choices=[('dssp', 'classic DSSP'),
                                       ('mmcif', 'DSSP-annotated mmCIF'),
                                       ('hssp_hssp', 'HSSP'),
                                       ('hssp_stockholm', 'HSSP (Stockholm)'),
                                       ('hg_hssp', 'HSSP (Human Genome)')],
                              validators=[OnlyAllowedIf('mmcif', 'input_type', ['pdb_file'])])
    pdb_id = StringField(u'PDB code', validators=[OnlyRequiredIf('input_type', ['pdb_id', 'pdb_redo_id']),
                                                  validators.Regexp(regex=RE_PDB_ID),
                                                  PdbidExists(settings.PDB_ROOT, settings.PDB_REDO_ROOT)])
    sequence = TextAreaField(u'Sequence', validators=[
        OnlyRequiredIf('input_type', ['sequence']),
        NAminoAcids(min=25)
    ])
    file_ = FileField(u'File', validators=[OnlyRequiredIf('input_type', ['pdb_file'])])

    def __init__(self, allowed_extensions=None, **kwargs):
        super(XsspForm, self).__init__(**kwargs)
        if allowed_extensions:
            file_field = self._fields.get('file_')
            file_field.validators.append(FileExtension(allowed_extensions))


class SupportForm(FlaskForm):
    email = EmailField('Email',
                       [validators.DataRequired(), validators.Email()])
    body = TextAreaField('Body', [validators.DataRequired(),
                                  validators.Regexp('^.*[A-Za-z].*$', flags=re.MULTILINE, message="Please fill in a text message here."),
                                  English(), NoSpam()])

