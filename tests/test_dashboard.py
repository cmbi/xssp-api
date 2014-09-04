from StringIO import StringIO

from mock import patch
from nose.tools import eq_

from xssp_rest.factory import create_app


class TestDashboard(object):

    @classmethod
    def setup_class(cls):
        cls.flask_app = create_app({'TESTING': True,
                                    'SECRET_KEY': 'testing',
                                    'WTF_CSRF_ENABLED': False})
        cls.app = cls.flask_app.test_client()

    def test_index(self):
        rv = self.app.get('/')
        eq_(rv.status_code, 200)

    @patch('xssp_rest.services.xssp.PdbContentStrategy.__call__')
    def test_index_post_hssp_from_pdb(self, mock_call):
        mock_call.return_value = 12345
        rv = self.app.post('/', data={'input_type': 'pdb_file',
                                      'output_type': 'hssp_hssp',
                                      'file_': (StringIO('not-real-data'),
                                                'fake.pdb')},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert "Please wait while your request is processed" in rv.data
        mock_call.assert_called_once_with('not-real-data')

    @patch('xssp_rest.services.xssp.SequenceStrategy.__call__')
    def test_index_post_hssp_from_sequence(self, mock_call):
        mock_call.return_value = 12345
        rv = self.app.post('/', data={'input_type': 'sequence',
                                      'output_type': 'hssp_hssp',
                                      'sequence': 'not-real-seq'},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert "Please wait while your request is processed" in rv.data
        mock_call.assert_called_once_with('not-real-seq')

    @patch('xssp_rest.services.xssp.PdbContentStrategy.__call__')
    def test_index_post_dssp_from_pdb(self, mock_call):
        mock_call.return_value = 12345
        rv = self.app.post('/', data={'input_type': 'pdb_file',
                                      'output_type': 'dssp',
                                      'file_': (StringIO('not-real-pdb'),
                                                'fake.pdb')},
                           follow_redirects=True)
        print rv.data
        eq_(rv.status_code, 200)
        assert "Please wait while your request is processed" in rv.data
        mock_call.assert_called_once_with('not-real-pdb')
