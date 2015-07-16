# waftool for program version dependent inclusion

This tool teaches [Waf](http://waf.io) to pre-process files dependent on program versions. During configuration, the versions of installed programs can be queried. When building, files can then be marked up to include or leave out spans of their content according to these version numbers. This is, for example, useful

- to adapt configuration files to dynamically use features only available from a certain version on,
- adapt wrappers to arguments that were added, removed or modified,
- adapt to API changes introduced with a dedicated version or
- work around bugs only present in old versions.


## Usage

[The included example](example/wscript) shows how to use it in a wafscript.

The tool can readily be loaded as long as it is found by the python module import mechanism. This is normally done by prepending the directory it resides in to the PYTHONPATH environment variable. So the following command build a waf executable from git including this tool.

```bash
git clone https://github.com/waf-project/waf
cd waf
git clone https://github.com/dffischer/waf-version
./waf-light configure --prefix=/usr \
  build --make-waf --tools='waf-version/gse.py'
```
