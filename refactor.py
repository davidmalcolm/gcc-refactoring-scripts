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

    def get_path_relative_to_changelog(self, path):
        dir_ = self.locate_dir(path)
        assert path.startswith(dir_)
        return path[len(dir_) + 1:]

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

def untabify(s):
    """
    Convert str s from tab-based indentation to space-based, assuming 8-space
    tabs
    """
    return s.expandtabs(8)

class Source:
    def __init__(self, s, changes=None):
        # Work in a space-based representation to make wordwrapping easier:
        s = untabify(s)
        self._str = s

        # self.changes: set of indices where changes have happened
        if changes:
            self.changes = changes
        else:
            self.changes = set()

    def str(self, as_tabs=1):
        # Convert back to tab-based representation on output:
        if as_tabs:
            return tabify(self._str)
        else:
            return self._str

    def show_changes(self):
        sys.stdout.write('\n\n')
        sys.stdout.write(self._str)
        for i, ch in enumerate(self._str):
            if ch == '\n':
                sys.stdout.write('\n')
            else:
                sys.stdout.write('*'
                                 if i in self.changes
                                 else (' '
                                       if ch.isspace()
                                       else '.'))

    def finditer(self, pattern):
        return re.finditer(pattern, self._str)

    def replace(self, from_idx, to_idx, replacement):
        # Inherit changes from before the replacement:
        changes = set([idx
                       for idx in self.changes
                       if idx < from_idx])
        # Everything within the replacement is regarded as changed:
        changes |= set([from_idx + i
                       for i in range(len(replacement))])
        # Inherit changes from after the replacement, offsetting
        # by the new location:
        changes |= set([from_idx + len(replacement) + (idx - to_idx)
                        for idx in self.changes
                        if idx >= to_idx])
        result =  Source(self._str[:from_idx] + replacement + self._str[to_idx:],
                         changes)
        #result.show_changes()
        return result

    def within_comment_at(self, idx):
        src = self._str[:idx]
        final_open_comment = src.rfind('/*')
        if final_open_comment == -1:
            return False
        src = src[final_open_comment:]
        return '*/' not in src

    FUNC_PATTERN=r'^(?P<FUNCNAME>[_a-zA-Z0-9]+) \(.*\)\n{'
    MACRO_PATTERN=r'^#define (?P<MACRO>[_a-zA-Z0-9]+)\(.*\)\s+\\\n'
    def get_change_scope_at(self, idx):
        src = self._str[:idx]
        m = re.search(self.FUNC_PATTERN, src, re.MULTILINE | re.DOTALL)
        if m:
            return m.groupdict()['FUNCNAME']
        m = re.search(self.MACRO_PATTERN, src, re.MULTILINE | re.DOTALL)
        if m:
            return m.groupdict()['MACRO']

    def get_changed_lines(self):
        """
        Get a list of (line, touched) pairs i.e. (str, bool) pairs
        """
        result = []
        line = ''
        touched = False
        for i, ch in enumerate(self._str):
            if ch == '\n':
                result.append( (line, touched) )
                line = ''
                touched = False
            else:
                line += ch
                if i in self.changes:
                    touched = True
        if line:
            result.append( (line, touched) )
        return result

    def wrap(self, just_changed=1):
        # See http://www.gnu.org/prep/standards/standards.html#Formatting
        new_lines = []
        old_lines = self.get_changed_lines()
        for line, touched in old_lines:
            if touched or not just_changed:
                while len(line) > 80:
                    wrapped, remainder = self._get_split_point(line)
                    if wrapped:
                        new_lines.append(wrapped)
                        line = self._indent(remainder, new_lines)
                    else:
                        # No wrapping was possible:
                        break
            new_lines.append(line)
        return Source(('\n'.join(new_lines)) + '\n')

    def _get_split_point(self, line, max_length=80):
        """
        Calculate the best split of the line
        """
        split_at = max_length
        while line[split_at] != ' ':
            split_at -= 1

        # Break before operators:
        if line[:split_at][-3:] in (' ==', ' !='):
            split_at -= 3
            newline = line[:split_at]
            if ' &&' in newline:
                split_at = newline.rfind(' &&')
            elif ' ""' in newline:
                split_at = newline.rfind(' ||')

        if line[:split_at][-3:] in (' &&', ' ||'):
            split_at -= 3

        assert line[split_at] == ' '

        # Omit the whitespace char at the split:
        wrapped, remainder = line[:split_at], line[(split_at + 1):]
        if wrapped.isspace():
            # No wrapping is possible:
            return '', line
        return wrapped, remainder

    def _indent(self, line, previous_lines):
        """
        Indent the content of line according to the context given
        in previous_lines
        """
        last_line = previous_lines[-1]
        if '(' in last_line:
            indent = last_line.rfind('(') + 1
            return (' ' * indent) + line
        else:
            return line

def refactor_file(path, relative_path, refactoring, printdiff,
                  applychanges):
    with open(path) as f:
        src = Source(f.read())
    #print(src)
    assert path.startswith('../src/gcc/')
    dst, changelog = refactoring(relative_path, src)
    #print(dst)

    if printdiff:
        for line in unified_diff(src.str().splitlines(),
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
                relative_path = cll.get_path_relative_to_changelog(path)
                clogtext = refactor_file(path,
                                         relative_path,
                                         refactoring,
                                         printdiff=True,
                                         applychanges=True)
                cla.add_text(path, clogtext)
    os.path.walk('../src/gcc', visit, None)
    cla.apply(printdiff=True)

if __name__ == '__main__':
    main('refactor.py', refactor_pass_initializers)
