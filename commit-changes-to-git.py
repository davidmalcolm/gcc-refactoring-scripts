from collections import namedtuple
import os
import re
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile

start_of_line = r'^'
number = '[0-9]'
ws = r'\s'
end_of_line = r'$'

# e.g. '2013-08-14  David Malcolm  <dmalcolm@redhat.com>\n'
PATTERN = (start_of_line
           + (number * 4) + '-' + (number * 2) + '-' + (number * 2)
           + ws
           + r'(.*)' # name&email of author
           + end_of_line)
pattern = re.compile(PATTERN)

def is_changelog_header(line):
    return pattern.match(line)

class ChangelogEntry(namedtuple('ChangelogEntry', ('header', 'body'))):
    pass

def parse_changelog(path):
    """
    Parse the changelog at the given path into a list of ChangelogEntry
    instances.
    """
    entries = []
    header = None
    body = ''
    with open(path) as f:
        for line in f:
            if is_changelog_header(line):
                if header:
                    entries.append(ChangelogEntry(header, body))
                header = line
                body = ''
            else:
                if header:
                    body += line
    return entries

# "git add" every changed file that's not a ChangeLog
os.system("git add $(git diff | diffstat -lp1 | grep -v ChangeLog)")

# Locate changed ChangeLogs, using it to build a commit message
p = Popen("git diff | diffstat -lp1", stdout=PIPE, shell=True)
out, err = p.communicate()
commit_msg = ''
for changelog_path in out.splitlines():
    from pprint import pprint
    entries = parse_changelog(changelog_path)
    commit_msg += '%s\n' % changelog_path[:-9] # drop "ChangeLog" suffix
    commit_msg += entries[0].body
print(commit_msg)

# Commit the files we added above (i.e. everything that's not a ChangeLog),
# using the commit message
p = Popen(['git', 'commit', '-F', '-'], stdin=PIPE)
p.communicate(commit_msg)

# Now purge the locally changed changelogs:
os.system("git checkout $(git diff | diffstat -lp1 | grep ChangeLog)")
