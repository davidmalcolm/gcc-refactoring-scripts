from collections import namedtuple
import re
import sys

from refactor import main, Changelog, tabify

############################################################################
# Parsing input
############################################################################
ws = r'\s+'
optws = r'\s*'

PATTERN = (
    'namespace {' + ws
    + r'const pass_data (?P<pass_data_name>\S+?) =(?P<point_a>\n{)'
    + '[^}]+?(?P<point_b>});\n\n'
    + 'class (?P<pass_name>\S+?) : public .*\n'
)

pattern = re.compile(PATTERN, re.MULTILINE | re.DOTALL)

def add_locations_to_pass_data(filename, src):
    changelog = Changelog(filename)
    while 1:
        m = src.search(pattern)
        if m:
            from pprint import pprint
            gd = m.groupdict()
            #pprint(gd)
            src = src.replace(m.start('point_b'), m.end('point_b'),
                              '  "%s" /* classname */\n)' % gd['pass_name'])
            src = src.replace(m.start('point_a'), m.end('point_a'),
                              ' PASS_DATA_INIT (')
            changelog.append('%(pass_data_name)s' % gd,
                             'Use PASS_DATA_INIT macro and supply a value for "classname".')
            continue

        # no matches:
        break

    src = src.wrap(tabify_changes=1)
    return src.str(as_tabs=0), changelog

if __name__ == '__main__':
    main('add_locations_to_pass_data.py', add_locations_to_pass_data, sys.argv,
         skip_testsuite=False)
