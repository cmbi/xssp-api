from mock import Mock
from nose.tools import eq_, raises
from wtforms.validators import StopValidation

from xssp_api.frontend.validators import (FileExtension, NAminoAcids,
                                           NotRequiredIfOneOf, ValidationError)


def test_file_extension():
    mock_field = Mock()
    mock_field.data.filename = 'test.pdb'
    mock_field.errors = []

    mock_form = Mock()
    mock_form._fields = {'file_field': mock_field}

    eq_(FileExtension(['pdb'])(mock_form, mock_field), None)


def test_file_extension_case_insensitive():
    mock_field = Mock()
    mock_field.data.filename = 'test.PDB'
    mock_field.errors = []

    mock_form = Mock()
    mock_form._fields = {'file_field': mock_field}

    eq_(FileExtension(['pdb'])(mock_form, mock_field), None)

    mock_field.data.filename = 'test.pdb'
    eq_(FileExtension(['PDB'])(mock_form, mock_field), None)


@raises(ValidationError)
def test_file_extension_not_allowed():
    mock_field = Mock()
    mock_field.data.filename = 'test.notallowed'
    mock_field.errors = []

    mock_form = Mock()
    mock_form._fields = {'file_field': mock_field}

    eq_(FileExtension(['pdb'])(mock_form, mock_field), None)


def test_not_required_if_one_of():
    mock_field1 = Mock()
    mock_field1.data = ''
    mock_field1.errors = []

    mock_field2 = Mock()
    mock_field2.data = 'something'
    mock_field2.errors = []

    mock_field3 = Mock()
    mock_field3.data = 'something else'
    mock_field3.errors = []

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field1,
                         'field2': mock_field2,
                         'field3': mock_field3}
    try:
        NotRequiredIfOneOf(['field2', 'field3'])(mock_form, mock_field1)
    except StopValidation as sve:
        eq_(str(sve), '')

    mock_field3.data = ''

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field1,
                         'field2': mock_field2,
                         'field3': mock_field3}
    try:
        NotRequiredIfOneOf(['field2', 'field3'])(mock_form, mock_field1)
    except StopValidation as sve:
        eq_(str(sve), '')


@raises(StopValidation)
def test_not_required_if_one_of_failed():
    mock_field1 = Mock()
    mock_field1.raw_data = ''
    mock_field1.errors = []

    mock_field2 = Mock()
    mock_field2.raw_data = ''
    mock_field2.errors = []

    mock_field3 = Mock()
    mock_field3.raw_data = ''
    mock_field3.errors = []

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field1,
                         'field2': mock_field2,
                         'field3': mock_field3}
    NotRequiredIfOneOf(['field2', 'field3'])(mock_form, mock_field1)


@raises(Exception)
def test_not_required_if_one_of_no_field():
    mock_field1 = Mock()
    mock_field1.data = ''
    mock_field1.errors = []

    mock_field2 = Mock()
    mock_field2.data = ''
    mock_field2.errors = []

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field1,
                         'field2': mock_field2}
    NotRequiredIfOneOf(['field3'])(mock_form, mock_field1)


def test_n_amino_acids():
    mock_field = Mock()
    mock_field.data = '1 ACDEFGHIKLMNPQRSTVWXY 22acdefghiklmnpqrstvwxy\n\tA  C'
    mock_field.errors = []

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field}

    eq_(NAminoAcids(25)(mock_form, mock_field), None)


def test_n_amino_acids_fasta():
    mock_field = Mock()
    mock_field.data = '>test\r\n1 ACDEFGHIKLMNPQRSTVWXY 22acdefghik\r\n'
    mock_field.errors = []

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field}

    eq_(NAminoAcids(25)(mock_form, mock_field), None)


def test_n_amino_acids_none():
    mock_field = Mock()
    mock_field.data = ''
    mock_field.errors = []

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field}

    try:
        NAminoAcids(25)(mock_form, mock_field)
    except ValidationError as ve:
        eq_(str(ve), 'Must be at least 25 amino acids long.')


def test_n_amino_acids_invalid_set():
    mock_field = Mock()
    mock_field.data = 'BJOUZ'
    mock_field.errors = []

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field}

    try:
        NAminoAcids(25)(mock_form, mock_field)
    except ValidationError as ve:
        eq_(str(ve), 'This field only accepts 1-letter codes from ' +
                        'the set "ACDEFGHIKLMNPQRSTVWXY".')


def test_n_amino_acids_invalid_length():
    mock_field = Mock()
    mock_field.data = 'ACDEFGHIKLMNPQRSTVWXY'
    mock_field.errors = []

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field}

    try:
        NAminoAcids(25)(mock_form, mock_field)
    except ValidationError as ve:
        eq_(str(ve), 'Must be at least 25 amino acids long.')


def test_n_amino_acids_invalid_multi_fasta():
    mock_field = Mock()
    mock_field.data = '>test0\nACDEFGHIKLMNPQRSTVWXY\n>test1\nACDEFGHIK'
    mock_field.errors = []

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field}

    expected_message = u'Multiple sequence FASTA input ' + \
                       'is currently not supported. ' + \
                       'The first line of FASTA input should start ' + \
                       'with ">" followed by a description.'
    try:
        NAminoAcids(25)(mock_form, mock_field)
    except ValidationError as ve:
        eq_(str(ve), expected_message)


def test_n_amino_acids_invalid_fasta_description():
    mock_field = Mock()
    mock_field.data = '>\nACDEFGHIK'
    mock_field.errors = []

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field}

    expected_message = u'Multiple sequence FASTA input ' + \
                       'is currently not supported. ' + \
                       'The first line of FASTA input should start ' + \
                       'with ">" followed by a description.'
    try:
        NAminoAcids(25)(mock_form, mock_field)
    except ValidationError as ve:
        eq_(str(ve), expected_message)

    mock_field.data = '> test\nACDEFGHIK'

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field}

    try:
        NAminoAcids(25)(mock_form, mock_field)
    except ValidationError as ve:
        eq_(str(ve), expected_message)
