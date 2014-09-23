from mock import Mock
from nose.tools import eq_, raises
from wtforms.validators import StopValidation

from xssp_rest.frontend.validators import NotRequiredIfOneOf


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
        eq_(sve.message, '')

    mock_field3.data = ''

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field1,
                         'field2': mock_field2,
                         'field3': mock_field3}
    try:
        NotRequiredIfOneOf(['field2', 'field3'])(mock_form, mock_field1)
    except StopValidation as sve:
        eq_(sve.message, '')


@raises(StopValidation)
def test_not_required_if_one_of_failed():
    mock_field1 = Mock()
    mock_field1.data = ''
    mock_field1.errors = []

    mock_field2 = Mock()
    mock_field2.data = ''
    mock_field2.errors = []

    mock_field3 = Mock()
    mock_field3.data = ''
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
