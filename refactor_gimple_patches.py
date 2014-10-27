import glob
import os
import textwrap

from gcc_mail_archive import MailArchive
from gimple_approvals import APPROVALS
from patch import Patch

INDEX_URL = 'https://gcc.gnu.org/ml/gcc-patches/2014-04/index.html'
IN_DIR = '../src/v11-patches'
OUT_DIR = '../src/generated-patches'

def main():
    # Read mail archive
    ma = MailArchive('gcc-patches-2014-04-index.html')

    # Open directory of candidate .patch files
    for i, f in enumerate(sorted(glob.glob(os.path.join(IN_DIR, '*.patch')))):
        print(f)
        p = Patch(f)
        print('  was: %r' % p.subject)
        if 'Update gimple.texi for' in p.subject:
            continue
        summary = p.summary
        if 0:
            print(repr(summary))

        if 0:
            # Update the subclasses in the patch:
            text = str(p.msg.get_payload())
            text = rename_types_in_str(text, 'patch')
            p.msg.set_payload(text)

            # and in the Subject:
            p.msg.replace_header('Subject',
                                 rename_types_in_str(p.msg['Subject'], 'subject'))

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

        print('  now: %r' % p.subject)

        with open(os.path.join(OUT_DIR, p.basename), 'w') as f:
            f.write(str(p.msg))

if __name__ == '__main__':
    main()
