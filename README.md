# waftool for program version dependent inclusion

This tool teaches [Waf](http://waf.io) to pre-process files dependent on program versions. During configuration, the versions of installed programs can be queried. When building, files can then be marked up to include or leave out spans of their content according to these version numbers.
