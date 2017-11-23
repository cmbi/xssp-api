import logging


_log = logging.getLogger(__name__)

def is_almost_same(sequence, blast_alignment):
    nalign = 0
    nid = 0
    for i in range(len(blast_alignment.query_alignment)):
        if blast_alignment.query_alignment[i].isalpha() and \
                blast_alignment.subj_alignment[i].isalpha():
            nalign += 1
            if blast_alignment.query_alignment[i].upper() == \
                    blast_alignment.subj_alignment[i].upper():
                nid += 1

    _log.debug("sequence-len: {}, nalign: {}, nid: {}".format(len(sequence), nalign, nid))
    if nalign < (len(sequence) - 20):
        return False

    pid = (100.0 * nid) / nalign
    return (pid > 95.0)
