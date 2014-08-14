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
        assert "Select the output type" in rv.data

    def test_index_post_empty_form(self):
        rv = self.app.post('/', data={'type_': 'hssp_from_pdb'})
        eq_(rv.status_code, 200)
        assert "required if &#39;file_&#39; is not provided" in rv.data
        assert "required if &#39;data&#39; is not provided" in rv.data

    def test_index_post_invalid_method(self):
        rv = self.app.post('/', data={'type_': 'not-a-real-value',
                                      'data': 'not-real-data'})
        eq_(rv.status_code, 200)
        assert "Not a valid choice" in rv.data

    @patch('xssp_rest.frontend.dashboard.views.create_hssp')
    def test_index_post_manual_data(self, mock_create_hssp):
        mock_create_hssp.return_value.id = 12345
        rv = self.app.post('/', data={'type_': 'hssp_from_pdb',
                                      'data': 'not-real-data'},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert "Please wait while your request is processed" in rv.data
        mock_create_hssp.assert_called_once_with('pdb', 'not-real-data')

    @patch('xssp_rest.frontend.dashboard.views.create_hssp')
    def test_index_post_file_data(self, mock_create_hssp):
        mock_create_hssp.return_value.id = 12345
        rv = self.app.post('/', data={'type_': 'hssp_from_pdb',
                                      'file_': (StringIO('not-real-data'),
                                                'fake.pdb')},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert "Please wait while your request is processed" in rv.data
        mock_create_hssp.assert_called_once_with('pdb', 'not-real-data')

    @patch('xssp_rest.frontend.dashboard.views.create_hssp')
    def test_index_post_hssp_from_sequence(self, mock_create_hssp):
        mock_create_hssp.return_value.id = 12345
        rv = self.app.post('/', data={'type_': 'hssp_from_sequence',
                                      'data': 'not-real-seq'},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert "Please wait while your request is processed" in rv.data
        mock_create_hssp.assert_called_once_with('seq', 'not-real-seq')

    @patch('xssp_rest.frontend.dashboard.views.create_dssp')
    def test_index_post_dssp_from_pdb(self, mock_create_dssp):
        mock_create_dssp.return_value.id = 12345
        rv = self.app.post('/', data={'type_': 'dssp_from_pdb',
                                      'data': 'not-real-pdb'},
                           follow_redirects=True)
        eq_(rv.status_code, 200)
        assert "Please wait while your request is processed" in rv.data
        mock_create_dssp.assert_called_once_with('pdb', 'not-real-pdb')
