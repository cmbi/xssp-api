import os
import subprocess
import tempfile

from mock import ANY, call, mock_open, patch
from nose.tools import eq_, raises

from xssp_rest.factory import create_app, create_celery_app


class TestTasks(object):

    @classmethod
    def setup_class(cls):
        flask_app = create_app({'TESTING': True,
                                'CELERY_ALWAYS_EAGER': True,
                                'DSSP_ROOT': '/dssp/',
                                'DSSP_REDO_ROOT': '/dssp_redo/',
                                'HSSP_ROOT': '/hssp/',
                                'HSSP_STO_ROOT': '/hssp3/'})
        cls.celery = create_celery_app(flask_app)

    @patch('subprocess.check_output')
    def test_mkdssp_from_pdb(self, mock_subprocess):
        mock_subprocess.return_value = "output"
        tmp_file = tempfile.NamedTemporaryFile(prefix='fake', suffix='.pdb',
                                               delete=False)

        from xssp_rest.tasks import mkdssp_from_pdb
        result = mkdssp_from_pdb.delay(tmp_file.name)

        eq_(result.get(), "output")
        eq_(os.path.isfile(tmp_file.name), False)
        mock_subprocess.assert_called_once_with(['mkdssp', '-i', ANY],
                                                stderr=ANY)

    @patch('subprocess.check_output')
    @raises(RuntimeError)
    def test_mkdssp_from_pdb_subprocess_exception(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            "returncode", "cmd", "output")
        tmp_file = tempfile.NamedTemporaryFile(prefix='fake', suffix='.pdb',
                                               delete=False)

        from xssp_rest.tasks import mkdssp_from_pdb
        try:
            result = mkdssp_from_pdb.delay(tmp_file.name)
            result.get()
        except RuntimeError:
            head, tail = os.path.split(tmp_file.name)
            # request id is None
            error_pdb_path = os.path.join(head, 'None_{}'.format(tail))
            eq_(os.path.isfile(error_pdb_path), True)
            raise
        finally:
            os.remove(error_pdb_path)

    @patch('subprocess.check_output')
    def test_mkhssp_from_pdb(self, mock_subprocess):
        mock_subprocess.side_effect = ["output1", "output2"]
        tmp_file = tempfile.NamedTemporaryFile(prefix='fake', suffix='.pdb',
                                               delete=False)

        from xssp_rest.tasks import mkhssp_from_pdb
        result = mkhssp_from_pdb.delay(tmp_file.name, 'hssp_hssp')

        eq_(result.get(), "output2")
        eq_(os.path.isfile(tmp_file.name), False)
        mock_subprocess.assert_has_calls([
            call(['mkhssp', '-i', ANY, '-d', ANY, '-d', ANY], stderr=ANY),
            call(['hsspconv', '-i', ANY], stderr=ANY)])

    @patch('subprocess.check_output')
    def test_mkhssp_stockholm_from_pdb(self, mock_subprocess):
        mock_subprocess.side_effect = ["output1", "output2"]
        tmp_file = tempfile.NamedTemporaryFile(prefix='fake', suffix='.pdb',
                                               delete=False)

        from xssp_rest.tasks import mkhssp_from_pdb
        result = mkhssp_from_pdb.delay(tmp_file.name, 'hssp_stockholm')

        eq_(result.get(), "output1")
        eq_(os.path.isfile(tmp_file.name), False)
        mock_subprocess.assert_called_once_with(['mkhssp', '-i', ANY, '-d',
                                                 ANY, '-d', ANY], stderr=ANY)
        assert not call(['hsspconv', '-i', ANY], stderr=ANY) in \
            mock_subprocess.call_args_list

    @patch('subprocess.check_output')
    @raises(RuntimeError)
    def test_mkhssp_from_pdb_subprocess_exception(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            "returncode", "cmd", "output")
        tmp_file = tempfile.NamedTemporaryFile(prefix='fake', suffix='.pdb',
                                               delete=False)

        from xssp_rest.tasks import mkhssp_from_pdb
        try:
            result = mkhssp_from_pdb.delay(tmp_file.name, 'hssp_hssp')
            result.get()
        except RuntimeError:
            head, tail = os.path.split(tmp_file.name)
            # request id is None
            error_pdb_path = os.path.join(head, 'None_{}'.format(tail))
            eq_(os.path.isfile(error_pdb_path), True)
            raise
        finally:
            os.remove(error_pdb_path)

    @patch('subprocess.check_output')
    def test_copy_input_when_stockholm_error(self, mock_subprocess):
        """
        Tests that when a stockholm file is produced but an error occurs, that
        the input file is copied for debugging.

        See https://github.com/cmbi/xssp-rest/issues/69.
        """
        mock_subprocess.side_effect = [
            "output1",
            subprocess.CalledProcessError("returncode", "cmd", "output")]

        tmp_file = tempfile.NamedTemporaryFile(prefix='fake', suffix='.pdb',
                                               delete=False)

        from xssp_rest.tasks import mkhssp_from_pdb
        try:
            result = mkhssp_from_pdb.delay(tmp_file.name, 'hssp_hssp')
            result.get()
        except RuntimeError:
            head, tail = os.path.split(tmp_file.name)
            # request id is None
            error_pdb_path = os.path.join(head, 'None_{}'.format(tail))
            eq_(os.path.isfile(error_pdb_path), True)
        finally:
            os.remove(error_pdb_path)

    @patch('subprocess.check_output')
    def test_mkhssp_from_sequence(self, mock_subprocess):
        mock_subprocess.return_value = "output"

        from xssp_rest.tasks import mkhssp_from_sequence
        result = mkhssp_from_sequence.delay('sequence', 'hssp_stockholm')

        eq_(result.get(), "output")
        mock_subprocess.assert_called_once_with(['mkhssp',
                                                 '-i', ANY,
                                                 '-d', ANY,
                                                 '-d', ANY], stderr=ANY)

    @patch('subprocess.check_output')
    def test_mkhssp_from_fasta(self, mock_subprocess):
        mock_subprocess.return_value = "output"

        from xssp_rest.tasks import mkhssp_from_sequence
        result = mkhssp_from_sequence.delay('>test\nseq', 'hssp_stockholm')

        eq_(result.get(), "output")
        mock_subprocess.assert_called_once_with(['mkhssp',
                                                 '-i', ANY,
                                                 '-d', ANY,
                                                 '-d', ANY], stderr=ANY)

    @patch('subprocess.check_output')
    def test_mkhssp_from_sequence_hssp_hssp(self, mock_subprocess):
        mock_subprocess.side_effect = ["output1", "output2"]

        from xssp_rest.tasks import mkhssp_from_sequence
        result = mkhssp_from_sequence.delay('pdb-content', 'hssp_hssp')

        eq_(result.get(), "output2")
        mock_subprocess.assert_has_calls([
            call(['mkhssp', '-i', ANY, '-d', ANY, '-d', ANY], stderr=ANY),
            call(['hsspconv', '-i', ANY], stderr=ANY)])

    @patch('subprocess.check_output')
    @raises(RuntimeError)
    def test_mkhssp_from_sequence_hssp_hsspconv_error(self, mock_subprocess):
        mock_subprocess.side_effect = [
            "output1",
            subprocess.CalledProcessError("returncode", "cmd", "output")]

        from xssp_rest.tasks import mkhssp_from_sequence
        result = mkhssp_from_sequence.delay('pdb-content', 'hssp_hssp')
        result.get()

    @patch('subprocess.check_output')
    @raises(RuntimeError)
    def test_mkhssp_from_sequence_subprocess_exception(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            "returncode", "cmd", "output")

        from xssp_rest.tasks import mkhssp_from_sequence
        result = mkhssp_from_sequence.delay('sequence', 'hssp_hssp')
        result.get()

    @patch('os.path.exists', return_value=False)
    @raises(RuntimeError)
    def test_get_dssp_file_not_found(self, mock_exists):
        from xssp_rest.tasks import get_dssp
        get_dssp('1crn')
        mock_exists.assert_called_once_with('/dssp/1crn.dssp')

    @patch('xssp_rest.tasks.open', mock_open(read_data='data'), create=True)
    @patch('os.path.exists', return_value=True)
    def test_get_dssp(self, mock_exists):
        from xssp_rest.tasks import get_dssp
        content = get_dssp('1crn')
        eq_(content, 'data')
        mock_exists.assert_called_once_with('/dssp/1crn.dssp')

    @patch('xssp_rest.tasks.open', mock_open(read_data='data'), create=True)
    @patch('os.path.exists', return_value=True)
    def test_get_dssp_upper(self, mock_exists):
        from xssp_rest.tasks import get_dssp
        content = get_dssp('1CRN')
        eq_(content, 'data')
        mock_exists.assert_called_once_with('/dssp/1crn.dssp')

    @patch('os.path.exists', return_value=False)
    @raises(RuntimeError)
    def test_get_dssp_redo_file_not_found(self, mock_exists):
        from xssp_rest.tasks import get_dssp_redo
        get_dssp_redo('1crn')
        mock_exists.assert_called_once_with('/dssp_redo/1crn.dssp')

    @patch('xssp_rest.tasks.open', mock_open(read_data='data'), create=True)
    @patch('os.path.exists', return_value=True)
    def test_get_dssp_redo(self, mock_exists):
        from xssp_rest.tasks import get_dssp_redo
        content = get_dssp_redo('1crn')
        eq_(content, 'data')
        mock_exists.assert_called_once_with('/dssp_redo/1crn.dssp')

    @patch('xssp_rest.tasks.open', mock_open(read_data='data'), create=True)
    @patch('os.path.exists', return_value=True)
    def test_get_dssp_redo_upper(self, mock_exists):
        from xssp_rest.tasks import get_dssp_redo
        content = get_dssp_redo('1CRN')
        eq_(content, 'data')
        mock_exists.assert_called_once_with('/dssp_redo/1crn.dssp')

    @patch('bz2.BZ2File')
    @patch('os.path.exists', return_value=True)
    def test_get_hssp_hssp(self, mock_exists, mock_bz2file):
        instance = mock_bz2file.return_value
        instance.__enter__.return_value.read.return_value = 'data'

        from xssp_rest.tasks import get_hssp
        content = get_hssp('1crn', 'hssp_hssp')

        eq_(content, 'data')
        mock_exists.assert_called_once_with('/hssp/1crn.hssp.bz2')

    @patch('bz2.BZ2File')
    @patch('os.path.exists', return_value=True)
    def test_get_hssp_hssp_upper(self, mock_exists, mock_bz2file):
        instance = mock_bz2file.return_value
        instance.__enter__.return_value.read.return_value = 'data'

        from xssp_rest.tasks import get_hssp
        content = get_hssp('1CRN', 'hssp_hssp')

        eq_(content, 'data')
        mock_exists.assert_called_once_with('/hssp/1crn.hssp.bz2')

    @patch('bz2.BZ2File')
    @patch('os.path.exists', return_value=True)
    def test_get_hssp_stockholm(self, mock_exists, mock_bz2file):
        instance = mock_bz2file.return_value
        instance.__enter__.return_value.read.return_value = 'data'

        from xssp_rest.tasks import get_hssp
        content = get_hssp('1crn', 'hssp_stockholm')

        eq_(content, 'data')
        mock_exists.assert_called_once_with('/hssp3/1crn.hssp.bz2')

    @raises(ValueError)
    def test_get_hssp_unexpected_output_type(self):
        from xssp_rest.tasks import get_hssp
        get_hssp('1crn', 'unexpected')

    @patch('os.path.exists', return_value=False)
    @raises(RuntimeError)
    def test_get_hssp_file_not_found(self, mock_exists):
        from xssp_rest.tasks import get_hssp
        get_hssp('1crn', 'hssp_hssp')

    def test_get_task(self):
        from xssp_rest.tasks import get_task

        task = get_task('pdb_id', 'dssp')
        eq_(task.__name__, 'get_dssp')
        task = get_task('pdb_id', 'hssp_hssp')
        eq_(task.__name__, 'get_hssp')
        task = get_task('pdb_id', 'hssp_stockholm')
        eq_(task.__name__, 'get_hssp')

        task = get_task('pdb_redo_id', 'dssp')
        eq_(task.__name__, 'get_dssp_redo')

        task = get_task('pdb_file', 'dssp')
        eq_(task.__name__, 'mkdssp_from_pdb')
        task = get_task('pdb_file', 'hssp_hssp')
        eq_(task.__name__, 'mkhssp_from_pdb')
        task = get_task('pdb_file', 'hssp_stockholm')
        eq_(task.__name__, 'mkhssp_from_pdb')

        task = get_task('sequence', 'hssp_hssp')
        eq_(task.__name__, 'mkhssp_from_sequence')
        task = get_task('sequence', 'hssp_stockholm')
        eq_(task.__name__, 'mkhssp_from_sequence')

    @raises(ValueError)
    def test_get_task_invalid_combination_pdb_redo_id_hssp(self):
        from xssp_rest.tasks import get_task
        get_task('pdb_redo_id', 'hssp')

    @raises(ValueError)
    def test_get_task_invalid_combination_pdb_redo_id_hssp_stockholm(self):
        from xssp_rest.tasks import get_task
        get_task('sequence', 'dssp')

    @raises(ValueError)
    def test_get_task_invalid_combination_sequence_dssp(self):
        from xssp_rest.tasks import get_task
        get_task('pdb_redo_id', 'hssp_stockholm')

    @raises(ValueError)
    def test_get_task_unexpected_input_type(self):
        from xssp_rest.tasks import get_task
        get_task('unexpected', 'hssp_stockholm')
