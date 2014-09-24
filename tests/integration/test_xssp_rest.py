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
import time
import xml.etree.ElementTree as ET

import requests
from nose.tools import eq_


XSSP_URL = 'http://www.cmbi.umcn.nl/xssp/api/'
CURRENT_PDB = 'http://pdb.org/pdb/rest/getCurrent'
CURRENT_REDO = 'http://www.cmbi.ru.nl/WHY_NOT2/resources/list/PDB_REDO_PRESENT'
FMT_CREATE = '{}create/{}/{}/'
FMT_STATUS = '{}status/{}/{}/{}/'
IO_COMBOS = {
    'pdb_id': ['dssp', 'hssp_hssp', 'hssp_stockholm'],
    'pdb_redo_id': ['dssp']}


class TestApi(object):
    def setup(self):
        self.all_pdb_ids = self._get_current_pdb_ids()
        self.all_pdb_redo_ids = self._get_current_pdb_redo_ids()

    def _get_current_pdb_ids(self):
        _log.info('Retrieving list of existing PDB entries from PDB...')
        r = requests.get(CURRENT_PDB)
        r.raise_for_status()

        root = ET.fromstring(r.text)
        return [child.get('structureId') for child in root]

    def _get_current_pdb_redo_ids(self):
        _log.info('Retrieving list of existing PDB_REDO ' +
                  'entries from WHY_NOT...')
        r = requests.get(CURRENT_REDO)
        r.raise_for_status()

        return filter(None, r.text.split('\n'))

    def test_input_id_existing_pdb_and_redo(self):
        """Tests that existing HSSP and DSSP files can be retrieved.

        The test tries to get HSSP and DSSP files for 5 randomly chosen
        existing PDB entries and DSSP files for 5 randomly chosen
        existing PDB_REDO entries using the XSSP REST API.
        """
        for input_type, output_types in IO_COMBOS.iteritems():
            test_ids = []
            if input_type == 'pdb_id':
                test_ids = [
                    random.choice(self.all_pdb_ids) for i in xrange(0, 5)]
            elif input_type == 'pdb_redo_id':
                test_ids = [
                    random.choice(self.all_pdb_redo_ids) for i in xrange(0, 5)]
            _log.info('Testing 5 random existing {} inputs: {}'.format(
                input_type, ' '.join(test_ids)))

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

                    _log.info('Done! {} for {} {}'.format(output_type,
                                                          input_type,
                                                          pdb_id))
