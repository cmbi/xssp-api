from mock import Mock
from nose.tools import eq_, raises
from wtforms.validators import StopValidation

from xssp_rest.frontend.validators import NotRequiredIf


def test_not_required_if():
    mock_field1 = Mock()
    mock_field1.data = ''
    mock_field1.errors = []

    mock_field2 = Mock()
    mock_field2.data = 'something'
    mock_field2.errors = []

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field1,
                         'field2': mock_field2}
    eq_(NotRequiredIf('field2')(mock_form, mock_field1), None)


@raises(StopValidation)
def test_not_required_if_failed():
    mock_field1 = Mock()
    mock_field1.data = ''
    mock_field1.errors = []

    mock_field2 = Mock()
    mock_field2.data = ''
    mock_field2.errors = []

    mock_form = Mock()
    mock_form._fields = {'field1': mock_field1,
                         'field2': mock_field2}
    NotRequiredIf('field2')(mock_form, mock_field1)
