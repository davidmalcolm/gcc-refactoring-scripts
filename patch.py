from collections import OrderedDict
from email.parser import Parser
import os.path
import re

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

    def parse_payload(self):
        # For a git-generated patch, we expect this format:
        #    optional text
        #    ---
        #    diffstat
        #    diffs
        #    --
        #    git version
        # Split on the first "---" line
        payload = self.msg.get_payload()
        if 0:
            print(payload)
        DIFFSTAT_SEPARATOR = '\n---\n'
        idx = payload.find(DIFFSTAT_SEPARATOR)
        before_diffstat = payload[:idx]
        diffstat_onwards = payload[idx + len(DIFFSTAT_SEPARATOR):]

        # Parse before the diffstat:
        state = 'LEADING_TEXT'
        clogs = OrderedDict({'LEADING_TEXT':''})
        for line in before_diffstat.splitlines():
            if 0:
                print(line)
            if line == 'Conflicts:':
                state = 'CONFLICTS'
                clogs[state] = ''
                continue
            # Match a changelog line like: "gcc/"
            m = re.match(r'^(\S*)/$', line)
            if m:
                if 0:
                    print('MATCH: %r' % (m.groups(), ))
                state = m.group(1)
                if state not in clogs:
                    clogs[state] = ''
            else:
                clogs[state] += line + '\n'
        leading_text = clogs['LEADING_TEXT']
        conflicts = clogs.get('CONFLICTS')
        del clogs['LEADING_TEXT']
        if 'CONFLICTS' in clogs:
            del clogs['CONFLICTS']

        return Payload(leading_text, clogs, conflicts, diffstat_onwards)

class Payload:
    def __init__(self, leading_text, clogs, conflicts, diffstat_onwards):
        self.leading_text = leading_text
        self.clogs = clogs
        self.conflicts = conflicts
        self.diffstat_onwards = diffstat_onwards
