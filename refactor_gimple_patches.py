from collections import namedtuple
from email.parser import Parser
import glob
import os
import re
import textwrap

from gcc_mail_archive import MailArchive
from gimple_approvals import APPROVALS
from refactor import Source, not_identifier
from rename_gimple import _add_stars_in_decls

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
        m = re.match(pat, self.subject, re.DOTALL)
        summary = m.group(3)
        summary = summary.replace('\n', '')
        return summary

class StmtClass(namedtuple('StmtClass',
                           ('orig_name', 'typedef', 'new_name'))):
    pass

stmt_classes = [
    StmtClass('gimple_statement_cond',
              'gimple_cond',
              'gcond'),
    StmtClass('gimple_statement_debug',
              'gimple_debug',
              'gdebug'),
    StmtClass('gimple_statement_goto',
              'gimple_goto',
              'ggoto'),
    StmtClass('gimple_statement_label',
              'gimple_label',
              'glabel'),
    StmtClass('gimple_statement_switch',
              'gimple_switch',
              'gswitch'),
    StmtClass('gimple_statement_assign',
              'gimple_assign',
              'gassign'),
    StmtClass('gimple_statement_asm',
              'gimple_asm',
              'gasm'),
    StmtClass('gimple_statement_call',
              'gimple_call',
              'gcall'),
    StmtClass('gimple_statement_transaction',
              'gimple_transaction',
              'gtransaction'),
    StmtClass('gimple_statement_return',
              'gimple_return',
              'greturn'),
    StmtClass('gimple_statement_bind',
              'gimple_bind',
              'gbind'),
    StmtClass('gimple_statement_catch',
              'gimple_catch',
              'gcatch'),
    StmtClass('gimple_statement_eh_filter',
              'gimple_eh_filter',
              'geh_filter'),
    StmtClass('gimple_statement_eh_mnt',
              'gimple_eh_must_not_throw',
              'geh_mnt'),
    StmtClass('gimple_statement_eh_else',
              'gimple_eh_else',
              'geh_else'),
    StmtClass('gimple_statement_resx',
              'gimple_resx',
              'gresx'),
    StmtClass('gimple_statement_eh_dispatch',
              'gimple_eh_dispatch',
              'geh_dispatch'),
    StmtClass('gimple_statement_phi',
              'gimple_phi',
              'gphi'),
    StmtClass('gimple_statement_try',
              'gimple_try',
              'gtry'),
    StmtClass('gimple_statement_omp_atomic_load',
              'gimple_omp_atomic_load',
              'gomp_atomic_load'),
    StmtClass('gimple_statement_omp_atomic_store',
              'gimple_omp_atomic_store',
              'gomp_atomic_store'),
    StmtClass('gimple_statement_omp_continue',
              'gimple_omp_continue',
              'gomp_continue'),
    StmtClass('gimple_statement_omp_critical',
              'gimple_omp_critical',
              'gomp_critical'),
    StmtClass('gimple_statement_omp_for',
              'gimple_omp_for',
              'gomp_for'),
    StmtClass('gimple_statement_omp_parallel',
              'gimple_omp_parallel',
              'gomp_parallel'),
    StmtClass('gimple_statement_omp_task',
              'gimple_omp_task',
              'gomp_task'),
    StmtClass('gimple_statement_omp_sections',
              'gimple_omp_sections',
              'gomp_sections'),
    StmtClass('gimple_statement_omp_single',
              'gimple_omp_single',
              'gomp_single'),
    StmtClass('gimple_statement_omp_target',
              'gimple_omp_target',
              'gomp_target'),
    StmtClass('gimple_statement_omp_teams',
              'gimple_omp_teams',
              'gomp_teams'),
]

def rename_types(text, where):
    """
    Update patches to follow the naming convention from
      https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00346.html

    Rename new types:
      "ORIG_NAME" -> "NEW_NAME"
      "TYPEDEF" -> "NEW_NAME *"
      "const_TYPEDEF" -> "const NEW_NAME *"
    e.g.
      "gimple_statement_switch" -> "gswitch"
      "gimple_switch" -> "gswitch *"
      "const_gimple_switch" -> "const gswitch *"
    FIXME: Only touch lines in ChangeLog, and those beginning with a +???
    FIXME: but we need to touch the - as well sometimes
    """
    assert where in ('subject', 'patch')
    src = Source(text)
    patterns = []
    for subclass in stmt_classes:
        for old, new in ((subclass.orig_name,
                          subclass.new_name),
                         (subclass.typedef,
                          '%s *' % subclass.new_name),
                         ('const_%s' % subclass.typedef,
                          'const %s *' % subclass.new_name)):
            patterns.append((old, new, not_identifier + ('(%s)' % old) + not_identifier))
            # Also match at the very end:
            patterns.append((old, new, not_identifier + ('(%s)$' % old)))

    patterns.append( ('gimple_phi_iterator', 'gphi_iterator',
                      not_identifier + '(gimple_phi_iterator)' + not_identifier) )
    patterns.append( ('gimple_phi_iterator', 'gphi_iterator',
                      not_identifier + '(gimple_phi_iterator)$') )

    for old, new, pattern in patterns:
            # this works backwards through the file
            for m in src.finditer_multiline(pattern):
                if 0:
                    print(m.start(1))
                    print(m.end(1))
                    print(src._str[m.start(1):m.end(1)])
                replacement = new
                start, end = m.start(1), m.end(1)

                replacement = new
                start, end = m.start(1), m.end(1)

                if new.endswith(' *'):
                    src = _add_stars_in_decls(src, old, new, start, end,
                                              within_patch=1)

                # Avoid turning:
                #   gimple_switch stmt
                # into
                #   gswitch * stmt
                # converting into
                #   gswitch *stmt
                # instead.
                if where == 'patch':
                    if new.endswith(' *') and src._str[end] == ' ':
                        end += 1

                src = src.replace(start, end, replacement)
    return src.str()

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

        # Update the subclasses in the patch:
        text = str(p.msg.get_payload())
        text = rename_types(text, 'patch')
        p.msg.set_payload(text)

        # and in the Subject:
        p.msg.replace_header('Subject',
                             rename_types(p.msg['Subject'], 'subject'))

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
