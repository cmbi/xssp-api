from tempfile import NamedTemporaryFile

from mock import patch
from nose.tools import eq_

from xssp_rest.factory import create_app


class TestDashboard(object):

    @classmethod
    def setup_class(cls):
        cls.flask_app = create_app({'TESTING': True,
                                    'SECRET_KEY': 'testing',
                                    'WTF_CSRF_ENABLED': False,
                                    'UPLOAD_FOLDER': 'uploads',
                                    'ALLOWED_EXTENSIONS': ['pdb', 'gz']})
        cls.app = cls.flask_app.test_client()

    def test_index(self):
        rv = self.app.get('/')
        eq_(rv.status_code, 200)

    @patch('xssp_rest.services.xssp.PdbContentStrategy.__call__')
    def test_index_post_hssp_from_pdb(self, mock_call):
        mock_call.return_value = 12345
        tmp_file = NamedTemporaryFile(prefix='fake', suffix='.pdb')
        rv = self.app.post('/', data={'input_type': 'pdb_file',
                                      'output_type': 'hssp_hssp',
                                      'file_': (tmp_file, tmp_file.name)},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert "Please wait while your request is processed" in rv.data
        mock_call.assert_called_once_with()

    @patch('xssp_rest.services.xssp.SequenceStrategy.__call__')
    def test_index_post_hssp_from_sequence(self, mock_call):
        mock_call.return_value = 12345
        test_sequence = 'ACDEFGHIKLMNPQRSTVWXYACDEFGHIKLMNPQRSTVWXY'
        rv = self.app.post('/', data={'input_type': 'sequence',
                                      'output_type': 'hssp_hssp',
                                      'sequence': test_sequence},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert "Please wait while your request is processed" in rv.data
        mock_call.assert_called_once_with()

    @patch('xssp_rest.services.xssp.SequenceStrategy.__call__')
    def test_index_post_hssp_from_sequence_no_input(self, mock_call):
        mock_call.return_value = 12345
        rv = self.app.post('/', data={'input_type': 'sequence',
                                      'output_type': 'hssp_hssp',
                                      'sequence': None},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert "This field is required if &#39;pdb_id&#39; and " + \
               "&#39;file_&#39; have not been provided" in rv.data

    @patch('xssp_rest.services.xssp.SequenceStrategy.__call__')
    def test_index_post_hssp_from_sequence_invalid_aa(self, mock_call):
        mock_call.return_value = 12345
        test_sequence = 'BJOZ'
        rv = self.app.post('/', data={'input_type': 'sequence',
                                      'output_type': 'hssp_hssp',
                                      'sequence': test_sequence},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert 'This field only accepts 1-letter codes from the set ' + \
               '&#34;ACDEFGHIKLMNPQRSTVWXY&#34;' in rv.data

    @patch('xssp_rest.services.xssp.SequenceStrategy.__call__')
    def test_index_post_hssp_from_sequence_invalid_length(self, mock_call):
        mock_call.return_value = 12345
        test_sequence = 'ACDEFGHIKLMNPQRSTVWXY'
        rv = self.app.post('/', data={'input_type': 'sequence',
                                      'output_type': 'hssp_hssp',
                                      'sequence': test_sequence},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert "Must be at least 25 amino acids long" in rv.data

    @patch('xssp_rest.services.xssp.PdbContentStrategy.__call__')
    def test_index_post_dssp_from_pdb(self, mock_call):
        mock_call.return_value = 12345
        tmp_file = NamedTemporaryFile(prefix='fake', suffix='.pdb')
        rv = self.app.post('/', data={'input_type': 'pdb_file',
                                      'output_type': 'dssp',
                                      'file_': (tmp_file, tmp_file.name)},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert "Please wait while your request is processed" in rv.data
        mock_call.assert_called_once_with()

    @patch('xssp_rest.services.xssp.PdbContentStrategy.__call__')
    def test_index_post_dssp_from_pdb_no_input(self, mock_call):
        mock_call.return_value = 12345
        rv = self.app.post('/', data={'input_type': 'pdb_file',
                                      'output_type': 'dssp',
                                      'file_': (None, None)},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert "This field is required if &#39;pdb_id&#39; and " + \
               "&#39;sequence&#39; have not been provided" in rv.data

    @patch('xssp_rest.services.xssp.PdbContentStrategy.__call__')
    def test_index_post_dssp_from_pdb_wrong_extension(self, mock_call):
        mock_call.return_value = 12345
        tmp_file = NamedTemporaryFile(prefix='fake', suffix='.mol')
        rv = self.app.post('/', data={'input_type': 'pdb_file',
                                      'output_type': 'dssp',
                                      'file_': (tmp_file, tmp_file.name)},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        print rv.data
        assert "Only the following file extensions are currently " + \
               "supported: .pdb .gz" in rv.data
