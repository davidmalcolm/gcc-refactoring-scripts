from email.parser import Parser
import glob
import os
import re
import textwrap

from gcc_mail_archive import MailArchive
from gimple_approvals import APPROVALS

INDEX_URL = 'https://gcc.gnu.org/ml/gcc-patches/2014-04/index.html'
IN_DIR = '../src/v11-patches'
OUT_DIR = '../src/generated-patches'

class Patch:
    def __init__(self, path):
        self.path = path
        with open(path) as f:
            self.content = f.read()
        #print(repr(self.content))
        self.msg = Parser().parsestr(self.content)
        #print(self.msg)
        #print(self.msg['Subject'])

    @property
    def basename(self):
        return os.path.basename(self.path)

    @property
    def subject(self):
        return self.msg['Subject']

    @property
    def summary(self):
        pat = r'\[PATCH ([0-9]+)/([0-9]+)\] (.+)'
        m = re.match(pat, p.subject, re.DOTALL)
        summary = m.group(3)
        summary = summary.replace('\n', '')
        return summary

# Read mail archive
ma = MailArchive('gcc-patches-2014-04-index.html')

# Open directory of candidate .patch files

for i, f in enumerate(sorted(glob.glob(os.path.join(IN_DIR, '*.patch')))):
    print(f)
    p = Patch(f)
    print(repr(p.subject))
    if 'Update gimple.texi for' in p.subject:
        continue
    summary = p.summary
    if 0:
        print(repr(summary))

    # Locate the corresponding patch submitted in April 2014:
    pat = r'\[PATCH ([0-9]+)/89\] %s' % summary
    m = ma.find_by_subject(pat)
    if not m:
        raise ValueError("Couldn't find original patch with summary: %r"
                         % summary)
    msg = 'This corresponds to:\n'
    msg += '  %s\n' % m.subject
    msg += '  %s\n' % m.get_url(INDEX_URL)
    msg += 'from the original 89-patch kit\n'
    msg += '\n'

    approval_url, approval_text = APPROVALS[m.subject]
    if not approval_url:
        raise ValueError('approval URL not found')
    if not approval_text:
        raise ValueError('approval text not found')
    msg += 'That earlier patch was approved by Jeff:\n'
    for line in approval_text.splitlines():
        for line in textwrap.wrap(line):
            msg += '> %s\n' % line.strip()
    msg += 'in %s\n\n' % approval_url

    #print(msg)

    payload = p.msg.get_payload()
    payload = msg + payload
    p.msg.set_payload(payload)

    with open(os.path.join(OUT_DIR, p.basename), 'w') as f:
        f.write(str(p.msg))
