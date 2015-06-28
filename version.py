#!/usr/bin/python

"""
Include lines depending on program version.

The task class 'ver' provided herein, processes a single input file
conditionally including lines containing version compatibility markers. These
markers may be placed anywhere in the line. They consist of the name of a
program, followed by a comparison operator (one of <, <=, >, >= or ==), and a
version number, all enclosed in @ symbols.

E.g. with the setup

    def build(bld):
        bld(
            versions={"ssh": (5, )}
        ).create_task('ver',
            source="in.ver",
            target="out"
        )

lines in the file "in" containing "@ssh>6@" will be omitted from "out".
Markers like "@ssh<7@" will be removed, the lines containing them left intact.

If any comparison operator is immediately followed by a question mark, the
comparison discards further components when version strings differ in length,
for example yielding 8==?8.1. Alternatively, the task class "subver" can be
used instead to turn all comparisons to act this fuzzy.

The components of a version number that are usually separated by periods, like
major, minor and patch, are comprised as a tuple for the context of this tool.
"""

from waflib.Task import Task, store_task_type
from waflib.Errors import WafError
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
                except KeyError as program:
                    raise WafError('version missing for program ' + str(program)) from program
            else:
                yield line
        self.generator.bld.raw_deps[self.uid()] = programs

    def get_version(self, program):
        """Looks for a version tuple in the dictionary given to the
        generator, or queries the environment alternatively."""
        generator = self.generator
        try:
            return self.generator.versions[program]
        except KeyError:
            return self.generator.versions[program.upper()]

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
