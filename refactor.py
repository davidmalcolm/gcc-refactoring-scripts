from collections import namedtuple, OrderedDict
from datetime import date
from difflib import unified_diff
import os
import re
from subprocess import check_output # 2.7
import sys
import textwrap

############################################################################
# Regex components
############################################################################
ws = '\s+'
opt_ws = '\s*'
identifier = '[_a-zA-Z][_a-zA-Z0-9]*?'
identifier_group = '(%s)' % identifier
def named_identifier_group(name):
    return '(?P<%s>%s)' % (name, identifier)

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
        self._lasttext_per_dir = {}

    def add_file(self, path, clog):
        """
        Add Changelog instance about a file at a given path to the
        appropriate ChangeLog, potentially adding a header if this is the
        first touch that this refactoring has made to that ChangeLog
        """
        dir_ = self.cll.locate_dir(path)
        lasttext = self._lasttext_per_dir.get(dir_, None)
        filetext, self._lasttext_per_dir[dir_] = clog.as_text(lasttext)
        if not filetext:
            return
        assert filetext.endswith('\n')
        if dir_ not in self.text_per_dir:
            header = '%s  %s  <%s>' % (self.isodate,
                                       self.author.name,
                                       self.author.email)
            self.text_per_dir[dir_] = (header + '\n\n'
                                       + self.headertext + '\n')
        self.text_per_dir[dir_] += filetext

    def apply(self, printdiff):
        """
        Apply the changes to the ChangeLog files on disk
        """
        for dir_ in self.text_per_dir:
            filename = os.path.join(dir_, 'ChangeLog')
            with open(filename, 'r') as f:
                old_contents = f.read()
            new_contents = self.text_per_dir[dir_] + '\n' + old_contents
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
        self.scope_to_text = OrderedDict()

    def as_text(self, lasttext):
        """
        Generate textual form of log, potentially abbreviating successive
        duplicate entries to "Likewise."
        """
        result = ''
        for scope, text in self.scope_to_text.iteritems():
            if text == lasttext:
                text = 'Likewise.'
            else:
                lasttext = text
            if result == '':
                result += wrap('* %s (%s): %s\n' % (self.filename, scope, text))
            else:
                result += wrap('(%s): %s\n' % (scope, text))
        return result, lasttext

    def append(self, scope, text):
        assert text.endswith('.')
        if scope in self.scope_to_text:
            self.scope_to_text[scope] += '  %s' % text
        else:
            self.scope_to_text[scope] = '%s' % text

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
    assert '\t' not in line
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
        self._str = s

        # self.changes: set of indices where changes have happened
        if changes:
            self.changes = changes
        else:
            self.changes = set()

    def str(self, as_tabs=0):
        # Convert to tab-based representation on output:
        if as_tabs:
            return tabify(self._str)
        else:
            return self._str

    def get_line_at(self, index):
        start = self._str.rfind('\n', 0, index) + 1
        if start == -1:
            start = 0
        end = self._str.find('\n', index)
        if end == -1:
            end = len(self._str)
        return self._str[start:end]

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
        """
        Return the matches in reverse order so that changes later on
        don't disturb indices into the string earlier on.
        """
        return list(re.finditer(pattern, self._str))[::-1]

    def search(self, pattern):
        return re.search(pattern, self._str)

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

    def within_string_literal_at(self, idx):
        # Have we seen an odd number of quotes?
        # This doesn't handle escaped quotes, and quotes within comments
        return self._str[:idx].count('"') % 2

    FUNC_PATTERN = ('^' + named_identifier_group('FUNCNAME')
                    + r' \((?P<PARAMS>.*?)\)\n{')
    METHOD_PATTERN = (r'(?P<CLASS_NAME>[_a-zA-Z][^\n]*?)::'
                      + named_identifier_group('METHOD_NAME')
                      + r'\s+\((?P<PARAMS>.*?)\)\n{')
    MACRO_PATTERN=r'^#define (?P<MACRO>[_a-zA-Z0-9]+)\(.*?\)\s+\\\n'
    FUNC_PARAMS_PATTERN = (ws + named_identifier_group('FUNCNAME') + opt_ws + '\($')
    CLASS_PATTERN = (r'^struct GTY\(\(.+\)\)' + ws + named_identifier_group('CLASS')
                     + ws + ':' + ws + 'public' + ws + '$')
    FUNC_RETURN_PATTERN = (r'(?P<RETURN_TYPE>.+?)\s+' + named_identifier_group('FUNCNAME') + opt_ws + '\(')
    GLOBAL_PATTERN = (r'(?P<TYPE>.+?)\s+' + named_identifier_group('GLOBAL') + opt_ws + ';')
    def get_change_scope_at(self, idx, raise_exception=False):
        src = self._str[:idx]
        if 0:
            print('get_change_scope_at: %r' % src)
        # Get last matches, if any:
        m = None
        for m in re.finditer(self.FUNC_PATTERN, src, re.MULTILINE | re.DOTALL):
            pass
        if m:
            return m.groupdict()['FUNCNAME']
        for m in re.finditer(self.METHOD_PATTERN, src, re.MULTILINE | re.DOTALL):
            pass
        if m:
            gd = m.groupdict()
            return ('%s::%s' %
                    (gd['CLASS_NAME'], gd['METHOD_NAME']))
        for m in re.finditer(self.MACRO_PATTERN, src, re.MULTILINE | re.DOTALL):
            pass
        if m:
            return m.groupdict()['MACRO']
        for m in re.finditer(self.FUNC_PARAMS_PATTERN, src, re.MULTILINE | re.DOTALL):
            pass
        if m:
            return m.groupdict()['FUNCNAME']
        for m in re.finditer(self.CLASS_PATTERN, src, re.MULTILINE | re.DOTALL):
            pass
        if m:
            return m.groupdict()['CLASS']
        line = self.get_line_at(idx)
        for m in re.finditer(self.FUNC_RETURN_PATTERN, line, re.MULTILINE | re.DOTALL):
            pass
        if m:
            return m.groupdict()['FUNCNAME']
        for m in re.finditer(self.GLOBAL_PATTERN, line, re.MULTILINE | re.DOTALL):
            pass
        if m:
            return m.groupdict()['GLOBAL']

        # Not found
        if raise_exception:
            raise ValueError('could not locate scope at line: %r'
                             % self.get_line_at(idx))

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

    def wrap(self, just_changed=1, tabify_changes=1):
        # See http://www.gnu.org/prep/standards/standards.html#Formatting
        new_lines = []
        old_lines = self.get_changed_lines()
        for line, touched in old_lines:
            if touched or not just_changed:
                line = untabify(line)
                while len(line) > 80:
                    # Add parens to changed long lines with ternary ? : that
                    # lack them:
                    m = re.match('(?P<lhs>[^=]+) = (?P<condition>.+) \?'
                                 ' (?P<on_true>.+) : (?P<on_false>.+);', line)
                    if m:
                        gd = m.groupdict()
                        # Parenthesize nontrivial conditions:
                        if not gd['condition'].isalnum():
                            gd['condition'] = '(%s)' % gd['condition']
                        line = ('%(lhs)s = (%(condition)s'
                                ' ? %(on_true)s : %(on_false)s);' % gd)

                    wrapped, remainder = self._get_split_point(line)
                    if wrapped:
                        if tabify_changes:
                            wrapped = tabify(wrapped)
                        new_lines.append(wrapped)
                        line = self._indent(remainder, new_lines)
                    else:
                        # No wrapping was possible:
                        break
                if tabify_changes:
                    line = tabify(line)
            new_lines.append(line)
        return Source(('\n'.join(new_lines)) + '\n')

    def _get_split_point(self, line, max_length=80):
        """
        Calculate the best split of the line
        """
        assert '\t' not in line
        def _at_invocation():
            # Avoid breaking invocations:
            if line[split_at:][:2] == ' (':
                if split_at > 0:
                    if line[split_at - 1].isalpha():
                        return True

        split_at = max_length
        while line[split_at] != ' ' or _at_invocation():
            split_at -= 1

        # Break at ternary operators:
        if ' ? ' in line:
            split_at = line.rfind(' ? ')

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

        if line[:split_at][-2:] in (' |', ):
            split_at -= 2

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
        assert '\t' not in line
        def _get_opening(_line):
            # Track the open parens and their locations in last_line using
            # a stack:
            _line = untabify(_line)
            assert '\t' not in _line
            stack = []
            for i, ch in enumerate(_line):
                if ch in '[({':
                    stack.append( (i, ch) )
                if ch in '])}':
                    if stack:
                        stack.pop()
                    else:
                        # unmatched parens on this line:
                        return
            if stack:
                indent, ch = stack[-1]
                return indent, ch

        def _get_last_opening():
            for prev_line in previous_lines[::-1]:
                opening = _get_opening(prev_line)
                if opening:
                    return opening

        # Line up after the most-recently still-open paren:
        opening = _get_last_opening()
        if opening:
            indent, ch = opening
            return (' ' * (indent + 1)) + line
        else:
            return line

def refactor_file(path, relative_path, refactoring, printdiff,
                  applychanges):
    with open(path) as f:
        srctext = f.read()
        srcobj = Source(srctext)
    #print(src)
    assert path.startswith('../src/gcc/')
    dsttext, changelog = refactoring(relative_path, srcobj)
    assert isinstance(changelog, Changelog)
    #print(dst)

    if printdiff:
        for line in unified_diff(srctext.splitlines(),
                                 dsttext.splitlines(),
                                 fromfile=path, tofile=path):
            sys.stdout.write('%s\n' % line)
    if applychanges and srctext != dsttext:
        with open(path, 'w') as f:
            f.write(dsttext)

    return changelog

class Author(namedtuple('Author', ('name', 'email'))):
    pass

def get_revision():
    return check_output(['git', 'rev-parse', 'HEAD']).strip()

AUTHOR = Author('David Malcolm', 'dmalcolm@redhat.com')
GIT_URL = 'https://github.com/davidmalcolm/gcc-refactoring-scripts'

def main(script, refactoring, argv, skip_testsuite=False):
    cll = ChangeLogLayout('../src')

    revision = get_revision()
    headertext = wrap(('Patch autogenerated by %s from\n'
                       '%s\n'
                       'revision %s')
                      % (script, GIT_URL, revision))
    today = date.today()
    cla = ChangeLogAdditions(cll, today.isoformat(), AUTHOR, headertext)
    def visit(arg, dirname, names):
        if skip_testsuite:
            if 'testsuite' in names:
                names.remove('testsuite')
        for name in sorted(names):
            path = os.path.join(dirname, name)
            if os.path.isfile(path) \
                    and (path.endswith('.c') or
                         path.endswith('.h')):
                print(path)
                relative_path = cll.get_path_relative_to_changelog(path)
                changelog = refactor_file(path,
                                          relative_path,
                                          refactoring,
                                          printdiff=True,
                                          applychanges=True)
                assert isinstance(changelog, Changelog)
                cla.add_file(path, changelog)
    if len(argv) > 1:
        for path in argv[1:]:
            print(path)
            relative_path = cll.get_path_relative_to_changelog(path)
            changelog = refactor_file(path,
                                      relative_path,
                                      refactoring,
                                      printdiff=True,
                                      applychanges=True)
            assert isinstance(changelog, Changelog)
            cla.add_file(path, changelog)
    else:
        os.path.walk('../src/gcc', visit, None)
    cla.apply(printdiff=True)
