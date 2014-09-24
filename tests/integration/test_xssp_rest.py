import json
import random
import time
import xml.etree.ElementTree as ET

import requests
from nose.tools import eq_


XSSP_URL = 'http://www.cmbi.umcn.nl/xssp/api/'
FMT_CREATE = '{}create/{}/{}/'
FMT_STATUS = '{}status/{}/{}/{}/'
IO_COMBOS = {
    'pdb_id': ['hssp_hssp', 'hssp_stockholm'],
    'pdb_redo_id': ['dssp']}


class TestApi(object):
    def setup(self):
        self.all_pdb_ids = self._get_current_pdb_ids()

    def _get_current_pdb_ids(self):
        r = requests.get('http://pdb.org/pdb/rest/getCurrent')
        r.raise_for_status()

        root = ET.fromstring(r.text)
        return [child.get('structureId') for child in root]

    def test_pdb_id_hssp_hssp(self):
        test_pdb_ids = [random.choice(self.all_pdb_ids) for i in xrange(0, 5)]
        for pdb_id in test_pdb_ids:
            for input_type, output_types in IO_COMBOS.iteritems():
                for output_type in output_types:
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
                        if status in ['SUCCESS', 'FAILURE', 'REVOKED']:
                            eq_(status,
                                'SUCCESS', "{}/{} - {} failed: '{}'".format(
                                    input_type, output_type, pdb_id,
                                    json.loads(r.text)['message']))
                        else:
                            time.sleep(5)
