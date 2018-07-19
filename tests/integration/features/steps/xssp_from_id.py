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

from behave import given, when, then
from nose.tools import eq_


XSSP_URL = 'http://www.cmbi.umcn.nl/xssp/api/'
FMT_CREATE = '{}create/{}/{}/'
FMT_STATUS = '{}status/{}/{}/{}/'
FMT_WHY_NOT_PRESENT = 'http://www.cmbi.umcn.nl/WHY_NOT2/resources/list/{}'

MAX_POLLS = 24


@given('the list of existing "{xssp}" entries')
def step_given_existing_entries(context, xssp):
    _log.info('Retrieving {} list from WHY_NOT...'.format(xssp))
    r = requests.get(FMT_WHY_NOT_PRESENT.format(xssp))
    r.raise_for_status()
    context.existing = filter(None, r.text.split('\n'))


@when('we request an existing "{output_format}" entry')
def step_when_xssp_format_request(context, output_format):
    test_id = random.choice(context.existing)
    _log.info('Testing 1 random existing {} entry: {}'.format(
        output_format, test_id))

    _log.info('Testing {} {}...'.format(output_format, test_id))
    url_create = FMT_CREATE.format(XSSP_URL, 'pdb_id', output_format)

    r = requests.post(url_create, data={'data': test_id})
    r.raise_for_status()

    context.job_id = json.loads(r.text)['id']
    context.test_id = test_id
    context.output_format = output_format


@then('the status should be "{status}"')
def step_then_status_success(context, status):
    n_polls = 0
    while True:
        context.url_status = FMT_STATUS.format(XSSP_URL, 'pdb_id',
                                               context.output_format,
                                               context.job_id)
        r = requests.get(context.url_status)
        r.raise_for_status()

        request_status = json.loads(r.text)['status']
        msg = None
        try:
            msg = json.loads(r.text)['message']
        except KeyError:
            pass

        if request_status in ['SUCCESS', 'FAILURE', 'REVOKED']:
            eq_(request_status,
                status, "{}/{} - {} failed: '{}'".format(
                    'pdb_id', context.output_format, context.test_id, msg))
            break
        else:
            n_polls = n_polls + 1

        if n_polls > MAX_POLLS:
            raise Exception('The server is taking too long to finish the job')

        _log.debug('Waiting 5 more seconds...')
        time.sleep(5)
    _log.info('Done!')
