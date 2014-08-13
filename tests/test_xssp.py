from nose.tools import raises

from xssp_rest.services.xssp import create_dssp, create_hssp


@raises(ValueError)
def test_create_hssp_unknown_source():
    create_hssp('not-real', 'data')


@raises(ValueError)
def test_create_dssp_unknown_source():
    create_dssp('not-real', 'data')
