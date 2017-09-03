from __future__ import absolute_import

from sciunit2.exceptions import CommandLineError, CommandError
from sciunit2.command.create import CreateCommand
from sciunit2.command.open import OpenCommand
from sciunit2.command.exec_ import ExecCommand
from sciunit2.command.repeat import RepeatCommand
from sciunit2.command.list import ListCommand
from sciunit2.command.rm import RmCommand

import sys
from getopt import getopt, GetoptError
from cStringIO import StringIO
import pkg_resources

__cmds__ = [CreateCommand, OpenCommand, ExecCommand, RepeatCommand,
            ListCommand, RmCommand]


def short_usage(out):
    out.write("usage: sciunit [--version] [--help]\n"
              "       sciunit <command> [<args...>]\n")


def subcommand_usage(out, cmds):
    buf = StringIO()
    for cmd in cmds:
        for ln in cmd.usage:
            if len(ln[0]) > 18:
                buf.write("  sciunit %s\n"
                          "                              %s\n" % ln)
            else:
                buf.write("  sciunit %-18s  %s\n" % ln)
    out.write(buf.getvalue())


def err1(msg):
    sys.stderr.write("sciunit: %s\n" % (msg,))


def err2(msg1, msg2):
    sys.stderr.write("sciunit: %s: %s\n" % (msg1, msg2))


def main():
    try:
        _main(sys.argv[1:])
    except CommandLineError:
        short_usage(sys.stderr)
        sys.exit(2)
    except GetoptError as exc:
        err1(exc.msg)
        short_usage(sys.stderr)
        sys.exit(2)
    except EnvironmentError as exc:
        if hasattr(exc, 'filename') and exc.filename is not None:
            err2(exc.filename, exc.strerror)
        else:  # pragma: no cover
            err1(exc.strerror)
        sys.exit(1)


def _main(args):
    optlist, args = getopt(args, '', ['help', 'version'])
    if not optlist and args:
        for cls in __cmds__:
            if args[0] == cls.name:
                cmd = cls()
                try:
                    cmd.run(args[1:])
                except CommandLineError:
                    subcommand_usage(sys.stderr, [cmd])
                    sys.exit(2)
                except GetoptError as exc:
                    err2(cls.name, exc.msg)
                    subcommand_usage(sys.stderr, [cmd])
                    sys.exit(2)
                except CommandError as exc:
                    err2(cls.name, exc.message)
                    sys.exit(1)
                break
        else:
            raise GetoptError('subcommand %r unrecognized' % args[0])
    elif optlist:
        op, _ = optlist[0]
        if op == '--help':
            short_usage(sys.stdout)
            print
            subcommand_usage(sys.stdout, [cls() for cls in __cmds__])
        elif op == '--version':
            print pkg_resources.require("sciunit2")[0]
        else:  # unreachable
            pass
    else:
        raise CommandLineError
