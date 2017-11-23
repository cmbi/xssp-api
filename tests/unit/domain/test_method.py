from nose.tools import ok_

from xssp_api.controllers.blast import BlastAlignment
from xssp_api.domain.method import is_almost_same


def test_is_almost_same():

    seq       = 'MLAGAGRPGLPQGRHLCWLLCAFTLKLCQAEAPIEEEKLSASTSNLPCWLVEEFVVAEECSPCSNFRAKTTPECGPTGYVEKITCSCSKRNEFKSCRSALMEQRLFWKFEGAVVCVALIFACLVIIRQRQLDRKALEKVRKQIESI'
    other_seq = 'MLAGAGRPGLPQGRHLCWLLCAFTLKLCQAEAPVQEEKLSASTSNLPCWLVEEFVVAEECSPCSNFRAKTTPECGPTGYVEKITCSSSKRNEFKSCRSALMEQRLFWKFEGAVVCVALIFACLVIIRQRQLDRKALEKVRKQIESI'

    alignment = BlastAlignment(1, len(seq), seq,
                               1, len(other_seq), other_seq)

    ok_(is_almost_same(seq, alignment))
