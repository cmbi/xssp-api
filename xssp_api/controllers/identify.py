import hashlib


def get_identifier(sequence: str):

    sequence = sequence.replace('\r', '').replace('\n', '').strip()

    id_ = hashlib.md5(sequence.encode()).hexdigest()

    return id_
