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
