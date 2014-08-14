import inspect
import json
import re

from mock import patch
from nose.tools import eq_, ok_

from xssp_rest.factory import create_app


class TestViews(object):

    @classmethod
    def setup_class(cls):
        cls.flask_app = create_app({'TESTING': True})
        cls.app = cls.flask_app.test_client()

    @patch('xssp_rest.tasks.mkdssp_from_pdb.delay')
    def test_create_dssp_from_pdb(self, mock_delay):
        mock_delay.return_value.id = 12345
        rv = self.app.post('/api/create/dssp/from_pdb/',
                           data={'pdb_content': ''})
        eq_(rv.status_code, 202)
        response = json.loads(rv.data)
        ok_('id' in response)
        eq_(response['id'], 12345)

    def test_create_dssp_from_pdb_no_pdb_content(self):
        rv = self.app.post('/api/create/dssp/from_pdb/')
        eq_(rv.status_code, 400)

    @patch('xssp_rest.tasks.mkhssp_from_pdb.delay')
    def test_create_hssp_from_pdb(self, mock_delay):
        mock_delay.return_value.id = 12345
        rv = self.app.post('/api/create/hssp/from_pdb/',
                           data={'pdb_content': ''})
        eq_(rv.status_code, 202)
        response = json.loads(rv.data)
        ok_('id' in response)
        eq_(response['id'], 12345)

    def test_create_hssp_from_pdb_no_pdb_content(self):
        rv = self.app.post('/api/create/hssp/from_pdb/')
        eq_(rv.status_code, 400)

    @patch('xssp_rest.tasks.mkhssp_from_sequence.delay')
    def test_create_hssp_from_sequence(self, mock_delay):
        mock_delay.return_value.id = 12345
        rv = self.app.post('/api/create/hssp/from_sequence/',
                           data={'sequence': ''})
        eq_(rv.status_code, 202)
        response = json.loads(rv.data)
        ok_('id' in response)
        eq_(response['id'], 12345)

    def test_create_hssp_from_sequence_no_sequence(self):
        rv = self.app.post('/api/create/hssp/from_sequence/')
        eq_(rv.status_code, 400)

    @patch('xssp_rest.tasks.mkdssp_from_pdb.AsyncResult')
    def test_get_job_status_for_dssp_from_pdb(self, mock_result):
        mock_result.return_value.failed.return_value = False
        mock_result.return_value.status = 'SUCCESS'
        rv = self.app.get('/api/job/dssp_from_pdb/12345/status/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('status' in response)
        eq_(response['status'], 'SUCCESS')

    @patch('xssp_rest.tasks.mkhssp_from_pdb.AsyncResult')
    def test_get_job_status_for_hssp_from_pdb(self, mock_result):
        mock_result.return_value.failed.return_value = False
        mock_result.return_value.status = 'SUCCESS'
        rv = self.app.get('/api/job/hssp_from_pdb/12345/status/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('status' in response)
        eq_(response['status'], 'SUCCESS')

    @patch('xssp_rest.tasks.mkhssp_from_sequence.AsyncResult')
    def test_get_job_status_for_hssp_from_sequence(self, mock_result):
        mock_result.return_value.failed.return_value = False
        mock_result.return_value.status = 'SUCCESS'
        rv = self.app.get('/api/job/hssp_from_sequence/12345/status/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('status' in response)
        eq_(response['status'], 'SUCCESS')

    @patch('xssp_rest.tasks.mkhssp_from_sequence.AsyncResult')
    def test_get_job_status_failed_message(self, mock_result):
        mock_result.return_value.failed.return_value = True
        mock_result.return_value.status = 'FAILED'
        mock_result.return_value.traceback = 'Error message'
        rv = self.app.get('/api/job/hssp_from_sequence/12345/status/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('status' in response)
        eq_(response['status'], 'FAILED')
        ok_('message' in response)
        eq_(response['message'], 'Error message')

    def test_get_job_status_for_unknown_job_type(self):
        rv = self.app.get('/api/job/unknown/12345/status/')
        eq_(rv.status_code, 400)

    @patch('xssp_rest.tasks.mkdssp_from_pdb.AsyncResult')
    def test_get_job_result_for_dssp_from_pdb(self, mock_result):
        mock_result.return_value.get.return_value = 'content-of-result'
        rv = self.app.get('/api/job/dssp_from_pdb/12345/result/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('result' in response)
        eq_(response['result'], 'content-of-result')

    @patch('xssp_rest.tasks.mkhssp_from_pdb.AsyncResult')
    def test_get_job_result_for_hssp_from_pdb(self, mock_result):
        mock_result.return_value.get.return_value = 'content-of-result'
        rv = self.app.get('/api/job/hssp_from_pdb/12345/result/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('result' in response)
        eq_(response['result'], 'content-of-result')

    @patch('xssp_rest.tasks.mkhssp_from_sequence.AsyncResult')
    def test_get_job_result_for_hssp_from_sequence(self, mock_result):
        mock_result.return_value.get.return_value = 'content-of-result'
        rv = self.app.get('/api/job/hssp_from_sequence/12345/result/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('result' in response)
        eq_(response['result'], 'content-of-result')

    def test_get_job_result_for_unknown_job_type(self):
        rv = self.app.get('/api/job/unknown/12345/result/')
        eq_(rv.status_code, 400)

    def test_api_doc(self):
        from xssp_rest.frontend.api import endpoints

        rv = self.app.get('/api/')
        eq_(rv.status_code, 200)

        excluded_fs = ['api_doc']
        for f_name, f in inspect.getmembers(endpoints, inspect.isfunction):
            mod_name = inspect.getmodule(f).__name__
            if "xssp_rest.frontend.api.endpoints" in mod_name and \
               f_name not in excluded_fs:
                src = inspect.getsourcelines(f)
                rx = r"@bp\.route\('([\w\/<>]*)', methods=\['([A-Z]*)']\)"
                m = re.search(rx, src[0][0])
                url = m.group(1)
                url = url.replace('>', '&gt;')
                url = url.replace('<', '&lt;')
                assert "<samp>/api{}</samp>".format(url) in rv.data
