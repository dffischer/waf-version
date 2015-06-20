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
            versions={"ssh": 5}
        ).create_task('ver',
            source="in.ver",
            target="out"
        )

lines in the file "in" containing "@ssh>6@" will be omitted from "out".
Markers like "@ssh<7@" will be removed, the lines containing them left intact.
"""

from waflib.Task import Task, store_task_type
from re import compile, escape
from operator import lt, le, gt, ge, eq, ne

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

class ver(Task, metaclass=compose_match):
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

    def compatible(self, text):
        """Checks the lines of text and yields all of them that have compatible
        version markers, all markers removed."""
        for line in text:
            match = self.marker.search(line)
            if match:
                if self.operators[match.group("operator")](
                        self.generator.versions[match.group("program")],
                        float(match.group("version"))):
                    yield self.marker.sub('', line)
            else:
                yield line
