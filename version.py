#!/usr/bin/python

from waflib.Task import Task
from re import compile

class ver(Task):
    marker = compile('@(?P<program>\w+)>(?P<version>\d[\.\d]*)@\s*')

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
