import logging
_log = logging.getLogger(__name__)

sh = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s')
sh.setFormatter(formatter)
_log.addHandler(sh)
_log.setLevel(logging.DEBUG)

import json
import random
import requests
import time

from nose.tools import eq_


XSSP_URL = 'http://www.cmbi.umcn.nl/xssp/api/'
FMT_CREATE = '{}create/{}/{}/'
FMT_STATUS = '{}status/{}/{}/{}/'
FMT_WHY_NOT_PRESENT = 'http://www.cmbi.ru.nl/WHY_NOT2/resources/list/{}'


class TestApi(object):
    """Integration tests fot the XSSP-REST API."""

    def setup(self):
        self.all_dssp = self._get_present_ids_from_why_not('DSSP_PRESENT')
        self.all_rssp = self._get_present_ids_from_why_not('DSSP_REDO_PRESENT')
        self.all_hssp = self._get_present_ids_from_why_not('HSSP_PRESENT')

    def _get_present_ids_from_why_not(self, db):
        _log.info('Retrieving {} list from WHY_NOT...'.format(db))
        r = requests.get(FMT_WHY_NOT_PRESENT.format(db))
        r.raise_for_status()

        return filter(None, r.text.split('\n'))

    def _test_input_ids(self, input_type, output_types, test_ids):
        """Driver for testing retrieval of existing files using XSSP-REST."""
        for pdb_id in test_ids:
            _log.info('Testing {} {}...'.format(input_type, pdb_id))
            for output_type in output_types:
                _log.info('Getting {} for {} {}...'.format(output_type,
                                                           input_type,
                                                           pdb_id))
                url_create = FMT_CREATE.format(XSSP_URL,
                                               input_type,
                                               output_type)

                r = requests.post(url_create, data={'data': pdb_id})
                r.raise_for_status()
                job_id = json.loads(r.text)['id']

                while True:
                    url_status = FMT_STATUS.format(XSSP_URL, input_type,
                                                   output_type, job_id)
                    r = requests.get(url_status)
                    r.raise_for_status()

                    status = json.loads(r.text)['status']
                    msg = None
                    try:
                        msg = json.loads(r.text)['message']
                    except KeyError:
                        pass

                    if status in ['SUCCESS', 'FAILURE', 'REVOKED']:
                        eq_(status,
                            'SUCCESS', "{}/{} - {} failed: '{}'".format(
                                input_type, output_type, pdb_id, msg))
                        break
                    else:
                        _log.debug('Waiting 5 more seconds...')
                        time.sleep(5)
                _log.info('Done!')

    def test_input_id_existing_hssp(self):
        """Tests that existing HSSP files can be retrieved.

        The test tries to get 5 randomly chosen existing HSSP files
        using the XSSP REST API.
        """
        test_ids = [random.choice(self.all_hssp) for i in xrange(0, 5)]
        _log.info('Testing 5 random existing hssp inputs: {}'.format(
            ' '.join(test_ids)))
        self._test_input_ids('pdb_id', ['hssp_hssp', 'hssp_stockholm'],
                             test_ids)

    def test_input_id_existing_dssp(self):
        """Tests that existing PDB DSSP files can be retrieved.

        The test tries to get 5 randomly chosen existing DSSP files
        using the XSSP REST API.
        """
        test_ids = [random.choice(self.all_dssp) for i in xrange(0, 5)]
        _log.info('Testing 5 random existing dssp inputs: {}'.format(
            ' '.join(test_ids)))
        self._test_input_ids('pdb_id', ['dssp'], test_ids)

    def test_input_id_existing_rssp(self):
        """Tests that existing PDB_REDO DSSP files can be retrieved.

        The test tries to get 5 randomly chosen existing RSSP files
        using the XSSP REST API.
        """
        test_ids = [random.choice(self.all_rssp) for i in xrange(0, 5)]
        _log.info('Testing 5 random existing rssp inputs: {}'.format(
            ' '.join(test_ids)))
        self._test_input_ids('pdb_id', ['dssp'], test_ids)
