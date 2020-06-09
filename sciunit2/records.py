from __future__ import absolute_import

from sciunit2.exceptions import CommandError, MalformedExecutionId
from sciunit2 import timestamp

import os
import fcntl
import json
import re
from contextlib import closing
from tempfile import NamedTemporaryFile
import bsddb3
DBNotFoundError = bsddb3.db.DBNotFoundError


# contains metadata for a sciunit execution including
# the executed command, time of execution and its size in bytes
class Metadata(object):
    __slots__ = '__d'

    def __init__(self, args):
        if isinstance(args, list):
            self.__d = {'cmd': args, 'started': str(timestamp.now())}
        else:
            self.__d = json.loads(args.decode('utf-8'))

    def __str__(self):
        return json.dumps(self.__d, separators=(',', ':'))

    # cls is the class through which this method is invoked
    # s is the berkeleydb object for the project
    @classmethod
    def fromstring(cls, s):
        # cls is the construction function which constructs the
        # class object which calls it and then calls its __init__ function.
        # cls is a class factory. cls(s) is the same as calling Metadata(s)
        # or the constructor of the class which called this function.

        # returns the class object of type with which fromstring() is called.
        # It could be Metadata or any of its subclasses.
        return cls(s)

    @property
    def cmd(self):
        return self.__d['cmd']

    @property
    def started(self):
        return timestamp.fromstring(self.__d['started'])

    @property
    def size(self):
        return self.__d['size']

    @size.setter
    def size(self, val):
        self.__d['size'] = val


# encloses the sciunit database and handles all db operations
class ExecutionManager(object):
    __slots__ = ['__f', '__pending', '__fn']

    def __init__(self, location):
        self.__fn = os.path.join(location, 'sciunit.db')
        self.__f = bsddb3.rnopen(self.__fn)

    # closes the database object
    def close(self):
        self.__f.close()

    # places a non-blocking exclusive lock on the database file descriptor
    def exclusive(self):
        fcntl.flock(self.__f.db.fd(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return closing(self)

    # places a non-blocking shared lock on the database file descriptor
    def shared(self):
        fcntl.flock(self.__f.db.fd(), fcntl.LOCK_SH | fcntl.LOCK_NB)
        return closing(self)

    # adds a new execution id to the database
    def add(self, args):
        try:
            newid = self.__f.last()[0] + 1
        except DBNotFoundError:
            newid = 1
        self.__pending = (newid, Metadata(args))
        return self.__to_rev(newid)

    def commit(self, size):
        # __pending is the id, args pair for
        # the newly added execution via add()
        k, v = self.__pending   # eid, Metadata
        v.size = size
        self.__f[k] = str(v)
        return self.__to_rev(k), v

    def get(self, rev):
        # rev is the execution id in the format e<number>
        # looks up rev in the project database and
        # returns a new object of type Metadata.
        return Metadata.fromstring(self.__get(self.__to_id(rev)))

    def __get(self, i):
        try:
            return self.__f.db.get(i)
        except KeyError:
            raise CommandError('execution %r not found' % self.__to_rev(i))

    def last(self):
        id_, m = self.__f.last()
        return self.__to_rev(id_), Metadata.fromstring(m)

    # removes an execution from the database by id
    def delete(self, rev):
        try:
            del self.__f[self.__to_id(rev)]
        except KeyError:
            pass

    def deletemany(self, revrange):
        bg, ed = self.__to_id_range(revrange)
        with closing(self.__f.db.cursor()) as c:
            try:
                if ed is None:
                    p = c.last()
                    ed = p[0]
                else:
                    # XXX set_range not functioning
                    try:
                        p = c.set(ed)
                    except bsddb3.db.DBError:
                        p = c.last()

                while not p[0] < bg:
                    if not ed < p[0]:
                        c.delete()
                        yield self.__to_rev(p[0])
                    p = c.prev()

            except DBNotFoundError:
                pass

    def sort(self, revls):
        ls = list(map(self.__to_id, revls))
        d = set(ls)
        if len(d) < len(ls):
            raise CommandError('duplicated entries')
        mismatched = min(ls)
        rename_list = []

        def need_to_rename(from_, to):
            if to != from_:
                rename_list.append((self.__to_rev(from_), self.__to_rev(to)))
        # rnopen opens db in Record format file.
        # records are accessed in the order they were originally written
        with NamedTemporaryFile(dir=os.path.dirname(self.__fn)) as fp:
            guard = closing(bsddb3.rnopen(fp.name, 'w'))
            with guard as tmp:
                self.__for_upto(mismatched,
                                lambda pair: tmp.db.put(pair[0], pair[1]))
                for i in ls:
                    j = tmp.db.append(self.__get(i))
                    need_to_rename(i, j)
                self.__for_from(mismatched, lambda pair:
                                pair[0] not in d and
                                need_to_rename(pair[0],
                                               tmp.db.append(pair[1])))

                yield rename_list
                os.rename(fp.name, self.__fn)
                fp.delete = False
                fp._closer.delete = False
                x = self.__f
                self.__f = guard.thing
                guard.thing = x

    # gets the executions from database with
    # execution ids from [0-'last').
    # puts them in the temp dab opened in function 'f'
    def __for_upto(self, last, f):
        with closing(self.__f.db.cursor()) as c:
            try:
                pair = c.first()
                while pair[0] < last:
                    f(pair)
                    pair = c.next()
            except DBNotFoundError:
                pass

    # gets the executions from database with
    # execution ids starting from 'first'
    def __for_from(self, first, f):
        with closing(self.__f.db.cursor()) as c:
            pair = c.set(first)
            while True:
                f(pair)
                try:
                    pair = c.next()
                except DBNotFoundError:
                    break

    @staticmethod
    def __to_rev(id_):
        return 'e%d' % id_

    @staticmethod
    def __to_id(rev):
        if not re.match(r'^e[1-9]\d*$', rev):
            raise MalformedExecutionId
        return int(rev[1:])

    @staticmethod
    def __to_id_range(revrange):
        r = re.match(r'^e([1-9]\d*)-([1-9]\d*)?$', revrange)
        if not r:
            raise MalformedExecutionId
        return tuple(int(x) if x is not None else x for x in r.groups())

    def list(self):
        for k, v in self.__f.iteritems():
            yield self.__to_rev(k), Metadata.fromstring(v)
