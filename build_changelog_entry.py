# Parse a patch, extracting the ChangeLog fragment from the header,
# applying it to actual ChangeLog files
from datetime import date
import os
import sys

from patch import Patch
from refactor import AUTHOR

def main(argv):
    print(sys.argv)
    patchfile = sys.argv[-2]
    clogname = sys.argv[-1]
    p = Patch(patchfile)
    payload = p.parse_payload()
    for subdir, text in payload.clogs.iteritems():
        print('subdir: %r' % subdir)
        print('text:\n%s' % text)
        clogfile = os.path.join(subdir, clogname)
        if os.path.exists(clogfile):
            with open(clogfile) as f:
                content = f.read()
        else:
            content = """Copyright (C) 2014 Free Software Foundation, Inc.

Copying and distribution of this file, with or without modification,
are permitted in any medium without royalty provided the copyright
notice and this notice are preserved.
"""

        today = date.today()
        header = '%s  %s  <%s>\n\n' % (today.isoformat(),
                                       AUTHOR.name,
                                       AUTHOR.email)
        content = (header + ('\t%s\n\n' % p.summary) + text.rstrip() + '\n\n' + content)
        with open(clogfile, 'w') as f:
            f.write(content)

if __name__ == '__main__':
    main(sys.argv)
