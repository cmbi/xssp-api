import inspect
import json
import re
from io import StringIO

from mock import patch
from nose.tools import eq_, ok_, raises

from xssp_api.factory import create_app


class TestEndpoints(object):

    @classmethod
    def setup_class(cls):
        # The API doesn't need a CSRF token, so enable CSRF so that tests will
        # fail if the API is incorrectly configured.
        cls.flask_app = create_app({'TESTING': True,
                                    'SECRET_KEY': 'testing',
                                    'WTF_CSRF_ENABLED': True})
        cls.app = cls.flask_app.test_client()

    @patch('xssp_api.services.xssp.PdbContentStrategy.__call__')
    def test_create_xssp_pdb_file_dssp(self, mock_call):
        mock_call.return_value = 12345
        rv = self.app.post('/api/create/pdb_file/dssp/',
                           data={'file_': (StringIO('not-real-data'),
                                           'fake.pdb')})
        eq_(rv.status_code, 202)
        response = json.loads(rv.data)
        ok_('id' in response)
        eq_(response['id'], 12345)
        mock_call.assert_called_once_with()

    def test_create_xssp_pdb_file_dssp_no_data(self):
        rv = self.app.post('/api/create/pdb_file/dssp/')
        eq_(rv.status_code, 400)

    @patch('xssp_api.services.xssp.PdbContentStrategy.__call__')
    def test_create_xssp_pdb_file_hssp(self, mock_call):
        mock_call.return_value = 12345
        rv = self.app.post('/api/create/pdb_file/hssp_hssp/',
                           data={'file_': (StringIO('not-real-data'),
                                           'fake.pdb')})
        print(rv.data)
        eq_(rv.status_code, 202)
        response = json.loads(rv.data)
        ok_('id' in response)
        eq_(response['id'], 12345)
        mock_call.assert_called_once_with()

    def test_create_xssp_pdb_file_hssp_no_data(self):
        rv = self.app.post('/api/create/pdb_file/hssp/')
        eq_(rv.status_code, 400)

    @patch('xssp_api.services.xssp.SequenceStrategy.__call__')
    def test_create_xssp_sequence_hssp(self, mock_call):
        mock_call.return_value = 12345
        rv = self.app.post('/api/create/sequence/hssp_hssp/',
                           data={'data': 'not-a-real-sequence'})
        eq_(rv.status_code, 202)
        response = json.loads(rv.data)
        ok_('id' in response)
        eq_(response['id'], 12345)
        mock_call.assert_called_once_with()

    def test_create_xssp_sequence_hssp_no_data(self):
        rv = self.app.post('/api/create/sequence/hssp_hssp/')
        eq_(rv.status_code, 400)

    @patch('xssp_api.tasks.mkdssp_from_pdb.AsyncResult')
    def test_get_xssp_status_pdb_file_dssp(self, mock_result):
        mock_result.return_value.failed.return_value = False
        mock_result.return_value.status = 'SUCCESS'
        rv = self.app.get('/api/status/pdb_file/dssp/12345/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('status' in response)
        eq_(response['status'], 'SUCCESS')

    @patch('xssp_api.tasks.mkhssp_from_pdb.AsyncResult')
    def test_get_xssp_status_pdb_file_hssp(self, mock_result):
        mock_result.return_value.failed.return_value = False
        mock_result.return_value.status = 'SUCCESS'
        rv = self.app.get('/api/status/pdb_file/hssp_hssp/12345/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('status' in response)
        eq_(response['status'], 'SUCCESS')

    @patch('xssp_api.tasks.mkhssp_from_sequence.AsyncResult')
    def test_get_xssp_status_sequence_hssp(self, mock_result):
        mock_result.return_value.failed.return_value = False
        mock_result.return_value.status = 'SUCCESS'
        rv = self.app.get('/api/status/sequence/hssp_hssp/12345/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('status' in response)
        eq_(response['status'], 'SUCCESS')

    @patch('xssp_api.tasks.mkhssp_from_sequence.AsyncResult')
    def test_get_xssp_status_sequence_hssp_failed_message(self, mock_result):
        mock_result.return_value.failed.return_value = True
        mock_result.return_value.status = 'FAILED'
        mock_result.return_value.traceback = 'Error message'
        rv = self.app.get('/api/status/sequence/hssp_hssp/12345/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('status' in response)
        eq_(response['status'], 'FAILED')
        ok_('message' in response)
        eq_(response['message'], 'Error message')

    @raises(ValueError)
    def test_get_xssp_status_unknown_input_type(self):
        rv = self.app.get('/api/status/unknown/hssp_hssp/12345/')
        eq_(rv.status_code, 400)

    @raises(ValueError)
    def test_get_xssp_status_unknown_output_type(self):
        rv = self.app.get('/api/status/sequence/unknown/12345/')
        eq_(rv.status_code, 400)

    @patch('xssp_api.tasks.mkdssp_from_pdb.AsyncResult')
    def test_get_xssp_result_pdb_file_dssp(self, mock_result):
        mock_result.return_value.get.return_value = 'content-of-result'
        rv = self.app.get('/api/result/pdb_file/dssp/12345/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('result' in response)
        eq_(response['result'], 'content-of-result')

    @patch('xssp_api.tasks.mkhssp_from_pdb.AsyncResult')
    def test_get_xssp_result_pdb_file_hssp(self, mock_result):
        mock_result.return_value.get.return_value = 'content-of-result'
        rv = self.app.get('/api/result/pdb_file/hssp_hssp/12345/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('result' in response)
        eq_(response['result'], 'content-of-result')

    @patch('xssp_api.tasks.mkhssp_from_sequence.AsyncResult')
    def test_get_xssp_result_sequence_hssp(self, mock_result):
        mock_result.return_value.get.return_value = 'content-of-result'
        rv = self.app.get('/api/result/sequence/hssp_hssp/12345/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('result' in response)
        eq_(response['result'], 'content-of-result')

    @raises(ValueError)
    def test_get_xssp_result_unknown_input_type(self):
        rv = self.app.get('/api/result/unknown/hssp_hssp/12345/')
        eq_(rv.status_code, 400)

    @raises(ValueError)
    def test_get_xssp_result_unknown_output_type(self):
        rv = self.app.get('/api/result/sequence/unknown/12345/')
        eq_(rv.status_code, 400)

    def test_api_doc(self):
        from xssp_api.frontend.api import endpoints

        rv = self.app.get('/api/')
        eq_(rv.status_code, 200)

        excluded_fs = ['api_doc', 'api_examples']
        for f_name, f in inspect.getmembers(endpoints, inspect.isfunction):
            mod_name = inspect.getmodule(f).__name__
            if "xssp_api.frontend.api.endpoints" in mod_name and \
               f_name not in excluded_fs:
                src = inspect.getsourcelines(f)
                rx = r"@bp\.route\('([\w\/<>]*)', methods=\['([A-Z]*)']\)"
                m = re.search(rx, src[0][0])
                url = m.group(1)
                url = url.replace('>', '&gt;')
                url = url.replace('<', '&lt;')
                assert "<samp>/api{}</samp>".format(url) in rv.data
