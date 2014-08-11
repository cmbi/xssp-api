import json

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
        mock_result.return_value.status = 'SUCCESS'
        rv = self.app.get('/api/job/dssp_from_pdb/12345/status/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('status' in response)
        eq_(response['status'], 'SUCCESS')

    @patch('xssp_rest.tasks.mkhssp_from_pdb.AsyncResult')
    def test_get_job_status_for_hssp_from_pdb(self, mock_result):
        mock_result.return_value.status = 'SUCCESS'
        rv = self.app.get('/api/job/hssp_from_pdb/12345/status/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('status' in response)
        eq_(response['status'], 'SUCCESS')

    @patch('xssp_rest.tasks.mkhssp_from_sequence.AsyncResult')
    def test_get_job_status_for_hssp_from_sequence(self, mock_result):
        mock_result.return_value.status = 'SUCCESS'
        rv = self.app.get('/api/job/hssp_from_sequence/12345/status/')
        eq_(rv.status_code, 200)
        response = json.loads(rv.data)
        ok_('status' in response)
        eq_(response['status'], 'SUCCESS')

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
