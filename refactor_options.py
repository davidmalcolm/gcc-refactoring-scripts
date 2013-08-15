from collections import OrderedDict
import re
import sys

from refactor import main, Changelog

optnames = ['flag_tree_vrp']
patterns = [re.compile(r'[^\(] (%s)' % optname, re.MULTILINE | re.DOTALL)
            for optname in optnames]

def make_macros_visible(clog_filename, src):
    changelog = Changelog(clog_filename)
    scopes = OrderedDict()
    while 1:
        match = 0
        for pattern in patterns:
            m = src.search(pattern)
            if m:
                scope = src.get_change_scope_at(m.start())
                replacement = 'GCC_OPTION (%s)' % m.group(1)
                src = src.replace(m.start(1), m.end(1), replacement)
                if scope not in scopes:
                    scopes[scope] = scope
                match = 1

        # no matches:
        if not match:
            break

    for scope in scopes:
        changelog.append(scope,
                         'Wrap option usage in GCC_OPTION macro.')

    return src.str(), changelog

if __name__ == '__main__':
    main('refactor_options.py', make_macros_visible, sys.argv,
         skip_testsuite=True)
