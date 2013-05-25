from collections import namedtuple
from datetime import date
from difflib import unified_diff
import os
import re
from subprocess import check_output # 2.7
import sys
import textwrap

############################################################################
# Generic hooks
############################################################################
FUNC_PATTERN=r'^(?P<FUNCNAME>[_a-zA-Z0-9]+) \(.*\)\n{'
MACRO_PATTERN=r'^#define (?P<MACRO>[_a-zA-Z0-9]+)\(.*\)\s+\\\n'
def get_change_scope(src, idx):
    src = src[:idx]
    m = re.search(FUNC_PATTERN, src, re.MULTILINE | re.DOTALL)
    if m:
        return m.groupdict()['FUNCNAME']
    m = re.search(MACRO_PATTERN, src, re.MULTILINE | re.DOTALL)
    if m:
        return m.groupdict()['MACRO']

def within_comment(src, idx):
    src = src[:idx]
    final_open_comment = src.rfind('/*')
    if final_open_comment == -1:
        return False
    src = src[final_open_comment:]
    return '*/' not in src

class ChangeLogLayout:
    """
    A collection of ChangeLog files in a directory hierarchy, thus
    indicating which ChangeLog covers which files
    """
    def __init__(self, basedir):
        self.dirs = []
        os.path.walk(basedir, self._visit, None)
        self.dirs = sorted(self.dirs)

    def _visit(self, arg, dirname, names):
        if 'ChangeLog' in names:
            self.dirs.append(dirname)

    def locate_dir(self, path):
        """
        Which directory's ChangeLog "owns" this path?
        """
        # Longest path that matches initial part of input path:
        return max([dir_ for dir_ in self.dirs
                    if path.startswith('%s/' % dir_)],
                   key=len)

class ChangeLogAdditions:
    """
    A set of ChangeLog additions, referenced by a ChangeLogLayout
    """
    def __init__(self, cll, isodate, author, headertext):
        self.cll = cll
        self.isodate = isodate
        self.author = author
        self.headertext = headertext
        # Mapping from directory
        self.text_per_dir = {}

    def add_text(self, path, filetext):
        """
        Add text about a file at a given path to the appropriate
        ChangeLog, potentially adding a header if this is the first
        touch that this refactoring has made to that ChangeLog
        """
        if not filetext:
            return
        dir_ = self.cll.locate_dir(path)
        if dir_ not in self.text_per_dir:
            header = '%s  %s  <%s>' % (self.isodate,
                                       self.author.name,
                                       self.author.email)
            self.text_per_dir[dir_] = (header + '\n\n'
                                       + self.headertext + '\n')
        self.text_per_dir[dir_] += filetext + '\n'

    def apply(self, printdiff):
        """
        Apply the changes to the ChangeLog files on disk
        """
        for dir_ in self.text_per_dir:
            filename = os.path.join(dir_, 'ChangeLog')
            with open(filename, 'r') as f:
                old_contents = f.read()
            new_contents = self.text_per_dir[dir_] + old_contents
            if printdiff:
                for line in unified_diff(old_contents.splitlines(),
                                         new_contents.splitlines(),
                                         fromfile=filename,
                                         tofile=filename):
                    sys.stdout.write('%s\n' % line)
            with open(filename, 'w') as f:
                f.write(new_contents)

class Changelog:
    """
    A set of entries in a ChangeLog describing changes to one specific file
    """
    def __init__(self, filename):
        self.filename = filename
        self.content = ''

    def append(self, text):
        assert text.endswith('\n')
        if self.content == '':
            self.content += wrap('* %s %s' % (self.filename, text))
        else:
            self.content += wrap('%s' % text)
        assert self.content.endswith('\n')

def wrap(text):
    """
    Word-wrap (to 70 columns) then add leading tab
    """
    result = ''
    for line in text.splitlines():
        result += '\n'.join(['\t%s' % wl
                             for wl in textwrap.wrap(line)])
        result += '\n'
    return result

def tabify_line(line):
    stripped = line.lstrip()
    indent = len(line) - len(stripped)
    tabs = indent / 8
    spaces = indent % 8
    return ('\t' * tabs) + (' ' * spaces) + stripped

def tabify(s):
    """
    Convert str s from space-based indentation to tab-based, assuming 8-space
    tabs
    """
    lines = s.splitlines()
    if s.endswith('\n'):
        lines += ['']
    return '\n'.join([tabify_line(line)
                      for line in lines])


def refactor_file(path, refactoring, printdiff, applychanges):
    with open(path) as f:
        src = f.read()
    #print(src)
    assert path.startswith('../src/gcc/')
    filename = path[len('../src/gcc/'):]
    dst, changelog = refactoring(filename, src)
    #print(dst)

    if printdiff:
        for line in unified_diff(src.splitlines(),
                                 dst.splitlines(),
                                 fromfile=path, tofile=path):
            sys.stdout.write('%s\n' % line)
    if applychanges and src != dst:
        with open(path, 'w') as f:
            f.write(dst)

    return changelog

class Author(namedtuple('Author', ('name', 'email'))):
    pass

def get_revision():
    return check_output(['git', 'rev-parse', 'HEAD']).strip()

AUTHOR = Author('David Malcolm', 'dmalcolm@redhat.com')
GIT_URL = 'https://github.com/davidmalcolm/gcc-refactoring-scripts'

def main(script, refactoring):
    cll = ChangeLogLayout('../src')

    revision = get_revision()
    headertext = wrap(('Patch autogenerated by %s from\n'
                       '%s\n'
                       'revision %s')
                      % (script, GIT_URL, revision))
    today = date.today()
    cla = ChangeLogAdditions(cll, today.isoformat(), AUTHOR, headertext)
    def visit(arg, dirname, names):
        for name in sorted(names):
            path = os.path.join(dirname, name)
            if os.path.isfile(path) \
                    and (path.endswith('.c') or
                         path.endswith('.h')):
                print(path)
                clogtext = refactor_file(path,
                                         refactoring,
                                         printdiff=True,
                                         applychanges=True)
                cla.add_text(path, clogtext)
    os.path.walk('../src/gcc', visit, None)
    cla.apply(printdiff=True)

if __name__ == '__main__':
    main('refactor.py', refactor_pass_initializers)
