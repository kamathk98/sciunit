from __future__ import absolute_import

from sciunit2.command import AbstractCommand
from sciunit2.command.mixin import CommitMixin
from sciunit2.exceptions import CommandLineError, MalformedExecutionId
import sciunit2.core
import sys
from getopt import getopt
import os
import sciunit2.filelock

class ParallelExecCommand(CommitMixin, AbstractCommand):
    name = 'parallel_exec'

    @property
    def usage(self):
        return [('parallel_exec ::: command_1 command_2 ... command_n',
                 "Repeat the execution of <execution id1> to <execution idn>. Use parallel before sciunit exec")]


    def run(self, args):
        optlist, args = getopt(args, 'i')
        # parallel_seq = os.getenv('PARALLEL_SEQ')
        # hostname = os.getenv('HOSTNAME')
        # if parallel_seq is None:
        #     raise CommandLineError
        # print(hostname)
        # parallel_seq contains which id it was run in 
        if bool(optlist) == bool(args):
            raise CommandLineError
        emgr, repo = sciunit2.workspace.current()
        lock = sciunit2.filelock.FileLock(os.path.join(repo.location ,'lockfile'))
        try:
            with emgr.exclusive():
                if optlist:
                    standin_fn = resource_filename(__name__, 'sciunit')
                    sciunit2.core.shell(env=path_injection_for(standin_fn))
                else:
                    sciunit2.core.capture(args)
                lock.acquire()
                rev = emgr.add(args)
                return self.do_commit('cde-package', rev, emgr, repo)
        finally:
            lock.release()
