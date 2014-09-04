import subprocess

from mock import ANY, call, patch
from nose.tools import eq_, raises

from xssp_rest.factory import create_app, create_celery_app


class TestTasks(object):

    @classmethod
    def setup_class(cls):
        flask_app = create_app({'TESTING': True,
                                'CELERY_ALWAYS_EAGER': True})
        cls.celery = create_celery_app(flask_app)

    @patch('subprocess.check_output')
    def test_mkdssp_from_pdb(self, mock_subprocess):
        mock_subprocess.return_value = "output"

        from xssp_rest.tasks import mkdssp_from_pdb
        result = mkdssp_from_pdb.delay('pdb-content')

        eq_(result.get(), "output")
        mock_subprocess.assert_called_once_with(['mkdssp', '-i', ANY])

    @patch('subprocess.check_output')
    @raises(RuntimeError)
    def test_mkdssp_from_pdb_subprocess_exception(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            "returncode", "cmd", "output")

        from xssp_rest.tasks import mkdssp_from_pdb
        result = mkdssp_from_pdb.delay('pdb-content')
        result.get()

    @patch('subprocess.check_output')
    def test_mkhssp_from_pdb(self, mock_subprocess):
        mock_subprocess.side_effect = ["output1", "output2"]

        from xssp_rest.tasks import mkhssp_from_pdb
        result = mkhssp_from_pdb.delay('pdb-content', 'hssp_hssp')

        eq_(result.get(), "output2")
        mock_subprocess.assert_has_calls([
            call(['mkhssp', '-i', ANY, '-d', ANY, '-d', ANY]),
            call(['hsspconv', '-i', ANY])])

    @patch('subprocess.check_output')
    @raises(RuntimeError)
    def test_mkhssp_from_pdb_subprocess_exception(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            "returncode", "cmd", "output")

        from xssp_rest.tasks import mkhssp_from_pdb
        result = mkhssp_from_pdb.delay('pdb-content', 'hssp_hssp')
        result.get()

    @patch('subprocess.check_output')
    def test_mkhssp_from_sequence(self, mock_subprocess):
        mock_subprocess.return_value = "output"

        from xssp_rest.tasks import mkhssp_from_sequence
        result = mkhssp_from_sequence.delay('sequence', 'hssp_stockholm')

        eq_(result.get(), "output")
        mock_subprocess.assert_called_once_with(['mkhssp',
                                                 '-i', ANY,
                                                 '-d', ANY,
                                                 '-d', ANY])

    @patch('subprocess.check_output')
    @raises(RuntimeError)
    def test_mkhssp_from_sequence_subprocess_exception(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            "returncode", "cmd", "output")

        from xssp_rest.tasks import mkhssp_from_sequence
        result = mkhssp_from_sequence.delay('sequence', 'hssp_hssp')
        result.get()
