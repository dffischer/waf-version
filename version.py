#!/usr/bin/python

"""
Include lines depending on program version.

The rule for source files with the extension '.ver', provided herein, processes
a input files conditionally including lines containing version compatibility
markers. These markers may be placed anywhere in the line. They consist of the
name of a program, followed by a comparison operator (one of <, <=, >, >= or
==), and a version number, all enclosed in @ symbols.

E.g., assuming bash is installed with version 4.4, with the setup

    def configure(cnf):
        cnf.find_version("bash")

    def build(bld):
        bld(source="file.ver")

lines in the "file.ver" containing "@bash>6@" will be omitted from "file".
Markers like "@bash<7@" will be removed, the lines containing them left intact.

If any comparison operator is immediately followed by a question mark, the
comparison discards further components when version strings differ in length,
for example yielding 8==?8.1. Alternatively, the task class "subver" can be
used instead to turn all comparisons to act this fuzzy.

Explicit version tuples for programs can be given in a dictionary passed to the
task generator as an argument named "versions". If no respective entry is dound
therein, it will be retrieved from an environment variable named like the
program prepended by "_VERSION", all uppercase. A configuration function
find_version is provided which can be used instead of find_program to set this
variable on the fly.

The components of a version number that are usually separated by periods, like
major, minor and patch, are comprised as a tuple for the context of this tool.

The install_path attribute may be specified at task generator creation to
specify a location to install the processed files.
"""

from waflib.Task import Task, store_task_type
from waflib.Errors import WafError
from waflib.Configure import conf
from waflib.TaskGen import extension, task_gen
from waflib.Utils import O644
from re import compile, escape
from operator import lt, le, gt, ge, eq, ne, itemgetter
from contextlib import suppress

class compose_match(store_task_type):
    """Metaclass composing the marker regular expression to look for exactly
    the set of operators defined as a class attribute."""
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        if 'operators' in attrs:
            cls.marker = compile('@'
                    '(?P<program>\w+)'
                    '(?P<operator>'
                        + '|'.join(map(escape, attrs['operators'].keys())) +
                    ')(?P<version>\d[\.\d]*)'
                    '@\s*')

class ver_base(Task, metaclass=compose_match):
    """Copy a file, including only lines without or with matching version
    markers."""

    operators = {
            "<" : lt, "<=" : le,
            ">" : gt, ">=" : ge,
            "==" : eq, "!=" : ne}
    """Defines all valid operators and the functions used to process them. It
    is possible to add new operators by customizing this dictionary for a
    subclass. All functions have to accept exactly two numeric arguments and
    return a boolesch value."""

    ext_in = ('.ver', )
    ext_out = ('', )

    def run(self):
        self.outputs[0].write('\n'.join(
            self.compatible(self.inputs[0].read().splitlines())))

        # make sure the signature is updated
        with suppress(AttributeError):
            del(self.cache_sig)

    def compatible(self, text):
        """Checks the lines of text and yields all of them that have compatible
        version markers, all markers removed."""
        programs = set()
        for line in text:
            match = self.marker.search(line)
            if match:
                program = match.group("program")
                programs.add(program)
                try:
                    if self.operators[match.group("operator")](
                            self.get_version(program),
                            version(match.group("version"))):
                        yield self.marker.sub('', line)
                except TypeError:
                    raise WafError('version missing for program ' + program)
            else:
                yield line
        self.generator.bld.raw_deps[self.uid()] = programs

    def get_version(self, program):
        """Looks for a version tuple in the dictionary given to the
        generator, or queries the environment alternatively."""
        generator = self.generator
        try:
            try:
                return generator.versions[program]
            except KeyError:
                return generator.versions[program.upper()]
        except (KeyError, AttributeError):
            return generator.env[program.upper() + '_VERSION']

    def keyword(self):
        return "Versioning"

    def sig_vars(self):
        super().sig_vars()
        upd = self.m.update
        for program in sorted(
                self.generator.bld.raw_deps.get(self.uid(), set())):
            upd(program.encode())
            try:
                upd('.'.join(map(str, self.get_version(program))).encode())
            except KeyError:
                upd(''.encode())
        return self.m.digest()

def fuzzy(cmp):
    """Wraps a function to consider sequences only up to the length of the
    shortest argument. This makes comparison of version tuples consider
    subversions equal."""
    return lambda *args: cmp(*(map(
            itemgetter(slice(min(map(len, args)))),
            args)))

class subver(ver_base):
    """Compare all version strings fuzzy."""
    operators = {operator: fuzzy(function)
            for operator, function in ver_base.operators.items()}

class ver(ver_base):
    """Provide fuzzy comparison of version strings through suffixing operators
    with a question mark."""
    operators = dict(ver_base.operators,
            **{operator + "?": fuzzy(function)
                for operator, function in ver_base.operators.items()})


def version(str):
    """Parse a version string into a tuple."""
    return tuple(map(int, str.split('.')))


@conf
def find_version(self, program, argument='--version',
        string=compile("\d+(\.\d+)*"), **kw):
    """Find the version of a program. Normally, the standard output of the
    program is searched for a versions string. If the program exits with an
    errorneous return code, the standard error output is examined instead.

    :param var: Store the result to conf.env[var.upper() + "_VERSION"], by
        default use the program name.
    :type var: string
    :param argument: Pass this argument to the program to make it output its
        version, '--version' by default. If the program only includes a version
        in its error output consider passing an invalid switch here.
    :type argument: string
    :param string: Consider the first match of this regular expression to be
        the version string. The entire matching string has to be appropriate as
        an arguemnt to the version function. To fix the match into a context,
        consider look-arund expressions. By default, the first sequence of
        numbers, possibly separated by dots, is used.
    :type string: re.regex

    This includes a call to find_program, which the program, the parameter
    'var' and all further keyword arguments will be passed to."""
    self.env[kw.get('var', program).upper() + "_VERSION"] = version(
            string.search(handle(WafError, lambda e: e.stderr,
                self.cmd_and_log,
                (self.find_program(program, **kw)[0], argument)
            )).group(0))

def handle(exception, handler, process, *args, **kwargs):
    """Execute process with all further arguments, processing an exception with
    the given handler."""
    try:
        return process(*args, **kwargs)
    except exception as e:
        return handler(e)

@extension(".ver")
def add_verfile(self, node):
    output = node.change_ext('', '.ver')
    self.create_task('ver', node, output)

    if output.suffix() in task_gen.mappings.keys():
        self.source.append(output)

    inst_to = getattr(self, 'install_path', None)
    if inst_to:
        self.bld.install_files(inst_to, output,
                chmod=getattr(self, 'chmod', O644))
