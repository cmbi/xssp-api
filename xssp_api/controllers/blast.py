import os
import logging
import subprocess
import tempfile
from bz2 import BZ2File
import xml.etree.ElementTree as ET

import xssp_api.default_settings as settings


_log = logging.getLogger(__name__)

def get_stockholm_sequences(path):

    sequences = {}

    with BZ2File(path, 'r') as f:
        for line in f:
            if line.startswith('#=GF RI'):
                amino_acid_letter = line[22]
                if amino_acid_letter.islower():
                    amino_acid_letter = 'C'

                chain = line[20]
                if chain == '>':
                    chain = line[69:73].strip()

                if chain not in sequences:
                    sequences[chain] = ''
                sequences[chain] += amino_acid_letter

    return sequences


def create_databank(hssp_dir_path, databank_path):

    fasta_path = tempfile.mktemp()
    try:
        with open(fasta_path, 'w') as f:
            for filename in os.listdir(hssp_dir_path):
                if not filename.endswith('.hssp.bz2'):
                    continue
                path = os.path.join(hssp_dir_path, filename)
                try:
                    sequences = get_stockholm_sequences(path)
                except Exception as e:
                    _log.warn("skipping {}: {}".format(path, str(e)))
                    continue

                id_ = os.path.basename(path).split('.')[0]

                _log.info("adding {}".format(path))
                for chain in sequences:
                    f.write(">%s_%s\n%s\n" % (id_, chain, sequences[chain]))

        subprocess.call([settings.MAKEBLASTDB, '-in', fasta_path,
                         '-dbtype', 'prot', '-out', databank_path])
    finally:
        if os.path.isfile(fasta_path):
            os.remove(fasta_path)


def blast_databank(sequence, databank_path):

    fasta_path = tempfile.mktemp()
    result_path = tempfile.mktemp()

    try:
        subprocess.call([settings.BLASTP, '-query', fasta_path,
                         '-db', databank_path, '-outFmt', '5',
                         '-out', result_path])

        root = ET.parse(result_path).getroot()
        hits = {}

        iterations = root.find('BlastOutput_iterations')
        for it in iterations.findall('Iteration'):
            for mem in it.findall('Iteration_hits'):
                for hit in mem.findall('Hit'):

                    hitID = hit.find('Hit_def').text
                    hits[hitID] = []

                    hsps = hit.find('Hit_hsps')
                    for hsp in hsps.findall('Hsp'):
                        querystart = int(hsp.find('Hsp_query-from').text)
                        queryend = int(hsp.find('Hsp_query-to').text)
                        queryali = hsp.find('Hsp_qseq').text

                        subjstart = int(hsp.find('Hsp_hit-from').text)
                        subjend = int(hsp.find('Hsp_hit-to').text)
                        subjali = hsp.find('Hsp_hseq').text

                        hits[hitID].append(BlastAlignment(querystart, queryend,
                                                          queryali, subjstart,
                                                          subjend, subjali))
        return hits
    finally:
        if os.path.isfile(fasta_path):
            os.remove(fasta_path)
        if os.path.isfile(result_path):
            os.remove(result_path)
