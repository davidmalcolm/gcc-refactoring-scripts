from collections import OrderedDict
import re
import sys

from refactor import main, Changelog

PATTERN = r'->(symbol\.)(\S)'
pattern = re.compile(PATTERN, re.MULTILINE | re.DOTALL)

def convert_to_inheritance(clog_filename, src):
    """
    Look for code of the form:
        "->symbol."
    followed by non-whitespace, and replace it with:
        "->"
    """

    changelog = Changelog(clog_filename)
    scopes = OrderedDict()
    while 1:
        m = src.search(pattern)
        if m:
            scope = src.get_change_scope_at(m.start())
            replacement = '->' + m.group(2)
            src = src.replace(m.start(), m.end(), replacement)
            if scope not in scopes:
                scopes[scope] = scope
            continue

        # no matches:
        break

    for scope in scopes:
        changelog.append(scope,
                         'Update for conversion of symtab types to a true class hierarchy.')

    return src.str(), changelog

if __name__ == '__main__':
    main('refactor_symtab.py', convert_to_inheritance, sys.argv,
         skip_testsuite=True)
