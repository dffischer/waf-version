#!/usr/bin/python

"""
Include lines depending on program version.

The task class 'ver' provided herein, processes a single input file
conditionally including lines containing version compatibility markers. These
markers may be placed anywhere in the line. They consist of the name of a
program, followed by the comparison operator >, and a version number, all
enclosed in @ symbols.

E.g. with the setup

    def build(bld):
        bld(
            versions={"ssh": 5}
        ).create_task('ver',
            source="in.ver",
            target="out"
        )

lines in the file "in" containing "@ssh>6@" will be omitted from "out".
Markers like "@ssh>4@" will be removed, the lines containing them left intact.
"""

from waflib.Task import Task
from re import compile

class ver(Task):
    """Copy a file, including only lines without or with matching version
    markers."""

    marker = compile('@(?P<program>\w+)>(?P<version>\d[\.\d]*)@\s*')
    """pattern matching version markers"""

    def run(self):
        self.outputs[0].write('\n'.join(
            self.compatible(self.inputs[0].read().splitlines())))

    def compatible(self, text):
        """Checks the lines of text and yields all of them that have compatible
        version markers, all markers removed."""
        for line in text:
            match = self.marker.search(line)
            if match:
                if float(match.group("version")) < \
                        self.generator.versions[match.group("program")]:
                    yield self.marker.sub('', line)
            else:
                yield line
