


def is_almost_same(sequence, blast_alignment):
    nalign = 0
    nid = 0
    for i in range(len(blast_alignment.query_alignment)):
        if blast_alignment.query_alignment.isalpha() and \
                blast_alignment.subj_alignment.isalpha():
            nalign += 1
            if last_alignment.query_alignment.upper() == \
                    blast_alignment.subj_alignment.upper():
                nid += 1
    if nalign < (len(sequence) - 20):
        return False

    pid = (100.0 * nid) / nalign
    return (pid > 98.0)
