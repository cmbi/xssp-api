import logging

from pymongo import MongoClient, ASCENDING


_log = logging.getLogger(__name__)


class Storage(object):
    def __init__(self, uri=None, db_name=None):
        self._db = None
        self._db_name = db_name
        self._client = None
        self._uri = uri

        if self._uri is not None and self._db_name is not None:
            self.connect()
            assert self._db is not None

    @property
    def db(self):
        if self._db is None:
            self.connect()
            assert self._db is not None
        return self._db

    @property
    def db_name(self):
        return self._db_name

    @db_name.setter
    def db_name(self, db_name):
        self._db_name = db_name

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, uri):
        self._uri = uri

    def connect(self):
        if self.uri is None or self._db_name is None:
            raise Exception("Storage hasn't been configured")

        _log.info("Connecting to '{}'".format(self.uri))
        self._client = MongoClient(self._uri)
        assert self._client is not None
        self._db = self._client[self._db_name]
        assert self._db is not None

        self.db['tasks'].create_index([('task_id', ASCENDING)])

    def insert_one(self, collection, document):
        if self._db is None:
            raise Exception("Not connected to storage. Did you call connect()?")

        self._db[collection].insert_one(document)

    def remove(self, collection, spec_or_id=None):
        if self._db is None:
            raise Exception("Not connected to storage. Did you call connect()?")

        _log.info("Removing documents from '{}'".format(collection))
        return self._db[collection].remove(spec_or_id)

    def find(self, collection, selector):
        if self._db is None:
            raise Exception("Not connected to storage. Did you call connect()?")

        _log.info("Querying documents in '{}'".format(collection))
        cursor = self._db[collection].find(selector)
        return [d for d in cursor]

    def find_one(self, collection, selector):
        if self._db is None:
            raise Exception("Not connected to storage. Did you call connect()?")

        _log.info("Querying single document in '{}'".format(collection))
        return self._db[collection].find_one(selector)


storage = Storage()
