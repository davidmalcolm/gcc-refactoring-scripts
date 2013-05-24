from collections import namedtuple
from datetime import date
from difflib import unified_diff
import os
import re
from subprocess import check_output # 2.7
import sys
import textwrap

############################################################################
# Parsing input
############################################################################

FIELDS = ('type',
          'name',
          'optinfo_flags',
          'gate',
          'execute',
          'sub',
          'next',
          'static_pass_number',
          'tv_id',
          'properties_required',
          'properties_provided',
          'properties_destroyed',
          'todo_flags_start',
          'todo_flags_finish')

class PassInitializer(namedtuple('PassInitializer',
                                 tuple(['static', 'passkind', 'passname'] + list(FIELDS)))):
    pass

EXTRA_FIELDS = (
    'generate_summary',
    'write_summary',
    'read_summary',
    'write_optimization_summary',
    'read_optimization_summary',
    'stmt_fixup',
    'function_transform_todo_flags_start',
    'function_transform',
    'variable_transform')

class ExtraFields(namedtuple('ExtraFields',
                             tuple(EXTRA_FIELDS))):
    pass

ws = r'\s+'
optws = r'\s*'

PATTERN = (
    '(?P<static>static )?struct' + ws + '(?P<passkind>\S+_opt_pass)' + ws +r'(?P<passname>\S+)' + optws + '=' + optws +
    '{' + optws + '{' + optws +
    '(?P<fields>[^}]*)' +
    '}' +',?' + optws + '}' + optws + ';'
)
pattern = re.compile(PATTERN, re.MULTILINE | re.DOTALL)

# struct ipa_opt_pass_d is more complicated due to extra fields at the end:
PATTERN2 = (
    '(?P<static>static )?struct' + ws + '(?P<passkind>ipa_opt_pass_d)' + ws +r'(?P<passname>\S+)' + optws + '=' + optws +
    '{' + optws + '{' + optws +
    '(?P<fields>[^}]*)' +
    '},' + '(?P<extrafields>[^}]*)' + '}' + optws + ';'
)
pattern2 = re.compile(PATTERN2, re.MULTILINE | re.DOTALL)

PATTERN3 = ('extern struct (?P<passkind>gimple_opt_pass|simple_ipa_opt_pass|ipa_opt_pass_d|rtl_opt_pass) (?P<passname>pass_\S+);')
pattern3 = re.compile(PATTERN3)

def clean_field(field):
    # Strip out C comments:
    field = re.sub(r'(/\*.*\*/)', '', field)
    # Strip out leading/trailing whitespace:
    field = field.strip()
    field = field.replace('\n', ' ')
    if '|' in field:
        field = ' | '.join([flag.strip()
                            for flag in field.split('|')])
    return field

def parse_basic_fields(gd):
    fields = []
    for field in gd['fields'].split(','):
        fields.append(clean_field(field))

    # Deal with trailing comma:
    if len(fields) == 15 and fields[14] == '':
        fields = fields[:14]

    if len(fields) != 14:
        print(fields)
    assert len(fields) == 14

    pi = PassInitializer(gd['static'] if gd['static'] else '',
                         gd['passkind'],
                         gd['passname'],
                         *fields)
    assert pi.sub == 'NULL'
    assert pi.next == 'NULL'
    assert pi.static_pass_number == '0'
    return pi

def parse_extra_fields(gd):
    fields = []
    for field in gd['extrafields'].split(','):
        field = clean_field(field)
        if field != '':
            fields.append(field)
    extra = ExtraFields(*fields)
    return extra

############################################################################
# Generating output
############################################################################

TEMPLATE_START_OF_CLASS = '''class %(classname)s : public %(passkind)s
{
public:
  %(classname)s(context &ctxt)
'''

def flags_ctor(indent, name, d, prefix, argnames, trailingtext):
    s = indent + '%s(' % name
    indent = ' ' * len(s)
    argvals = ['%s' % d[argname]
               for argname in argnames]
    argctors = ['%s(%s)' % (argname[len(prefix) + 1:], d[argname])
                for argname in argnames]
    # If all flags are 0, do on a single line:
    if 0: #all([argval == '0' for argval in argvals]):
        s += ')'
        s += trailingtext
    else:
        # Otherwise, split so that each argument is on a separate line:
        for i, (argctor, argnames) in enumerate(zip(argctors, argnames)):
            islastarg = (i == len(argctors) - 1)
            if i != 0:
                s += indent
            s += argctor
            if islastarg:
                s += ')'
                s += trailingtext
            else:
                s += ','
            if not islastarg:
                s += '\n'
    return s

def finish_pass_constructor(d, trailingtext):
    s = '    : %(passkind)s(' % d
    indent = ' ' * len(s)
    s += 'ctxt,\n'
    s += indent + '%(name)s,\n' % d
    s += indent + '%(optinfo_flags)s,\n' % d
    s += indent + '%(tv_id)s,\n' % d
    s += flags_ctor(indent, 'pass_properties', d,
                    'properties',
                    ('properties_required',
                     'properties_provided',
                     'properties_destroyed'),
                    ',')
    s += '\n'
    s += flags_ctor(indent, 'pass_todo_flags', d,
                    'todo_flags',
                    ('todo_flags_start',
                     'todo_flags_finish'),
                    trailingtext)
    s += '\n'
    return s

TEMPLATE_FACTORY_FUNCTION = '''%(static)s%(passkind)s *
make_%(classname)s (context &ctxt)
{
  return new %(classname)s (ctxt);
}'''

TEMPLATE_CLOG = ('(struct %(passkind)s %(classname)s): Convert from a global struct to a subclass of %(passkind)s.\n'
                 '(make_%(classname)s): New function to create an instance of the new class %(classname)s.\n')

def make_method(returntype, name, args, body, uses_args):
    if uses_args:
        argdecl = ', '.join(['%s%s' % (type_, argname)
                             for type_, argname in args])
    else:
        argdecl = ', '.join([type_
                             for type_, argname in args])
    if body:
        block = '{ %s }' % body
    else:
        block = '{ }'
    result = ('  %s %s (%s) %s\n'
                % (returntype, name, argdecl, block))
    # line-wrap at 76 chars:
    if len(result) > 76:
        result = ('  %s %s (%s) {\n'
                  '    %s\n'
                  '  }\n'
                  % (returntype, name, argdecl, body))
    return result

def make_method_pair(d, returntype, name, args):
    """
    The pre-existing code has plenty of places where a pass' callback fn
    is compared against NULL.  I believe that there isn't a portable way
    to do this for a C++ vfunc, so each callback becomes *two* vtable
    entries:
       bool has_FOO ()   // equivalent to (pass->FOO != NULL) in old code
    and
       impl_FOO ()       // equivalent to (pass->FOO ()) in old code
    """
    existingfn = d[name]
    if existingfn in ('NULL', '0'):
        body_of_has = 'return false;'
        if returntype == 'void':
            # Assume a NULL function ptr "returning" void is to become
            # a do-nothing hook:
            body_of_impl = ''
        else:
            if name == 'gate':
                body_of_impl = 'return true;'
            elif name == 'execute':
                body_of_impl = 'return 0;'
            elif name == 'function_transform':
                # this returns a "todo_after" which appears to be yet
                # another set of flags:
                body_of_impl = 'return 0;'
            else:
                raise ValueError("don't know how to refactor NULL %s" % name)
        impl_uses_args = False
    else:
        body_of_has = 'return true;'

        optreturn = 'return ' if returntype != 'void' else ''
        argusage = ', '.join([argname
                              for type_, argname in args])
        body_of_impl = ('%s%s (%s);'
                        % (optreturn, existingfn, argusage))
        impl_uses_args = True

    s = make_method('bool', 'has_%s' % name, [], body_of_has, uses_args=False)
    s += make_method(returntype,
                     'gate' if name == 'gate' else ('impl_%s' % name),
                     args, body_of_impl, impl_uses_args)
    s += '\n'
    return s

def make_pass_methods(pi):
    d = pi._asdict()
    s = '\n'
    s += '  /* opt_pass methods: */\n'
    s += make_method_pair(d, 'bool', 'gate', () )
    s += make_method_pair(d, 'unsigned int', 'execute', () )
    return s

def make_replacement(pi):
    d = pi._asdict()
    d['classname'] = pi.passname
    s = TEMPLATE_START_OF_CLASS % d
    s += finish_pass_constructor(d, ')')
    s += r'''  {}
'''
    s += make_pass_methods(pi)
    s += '}; // class %s\n\n' % d['classname']

    s += TEMPLATE_FACTORY_FUNCTION % d

    clog = TEMPLATE_CLOG % d

    return s, clog

def make_replacement2(pi, extra):
    d = pi._asdict()
    d.update(extra._asdict())
    d['classname'] = pi.passname
    s = TEMPLATE_START_OF_CLASS % d
    s += finish_pass_constructor(d, ',')
    s += r'''                     %(function_transform_todo_flags_start)s) /* function_transform_todo_flags_start */
  {}
''' % d
    s += make_pass_methods(pi)
    s += '  /* ipa_opt_pass_d methods: */\n'
    s += make_method_pair(d, 'void', 'generate_summary', [] )
    s += make_method_pair(d, 'void', 'write_summary', [] )
    s += make_method_pair(d, 'void', 'read_summary', [] )
    s += make_method_pair(d, 'void', 'write_optimization_summary', [] )
    s += make_method_pair(d, 'void', 'read_optimization_summary', [] )
    s += make_method_pair(d, 'void', 'stmt_fixup',
                          [('struct cgraph_node *', 'node'),
                           ('gimple *', 'stmt')])
    s += make_method_pair(d, 'unsigned int', 'function_transform',
                          [('struct cgraph_node *', 'node')])
    s += make_method_pair(d, 'void', 'variable_transform',
                          [('struct varpool_node *', 'node')])
    s += '}; // class %s\n\n' % d['classname']

    s += TEMPLATE_FACTORY_FUNCTION % d

    clog = TEMPLATE_CLOG % d

    return s, clog

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

def refactor_pass_initializers(filename, src):
    changelog = Changelog(filename)
    while 1:
        m = pattern.search(src)
        if m:
            gd = m.groupdict()
            pi = parse_basic_fields(gd)
            replacement, clog = make_replacement(pi)
            changelog.append(clog)
            src = (src[:m.start()] + tabify(replacement) + src[m.end():])
            continue

        m = pattern2.search(src)
        if m:
            gd = m.groupdict()
            pi = parse_basic_fields(gd)
            extra = parse_extra_fields(gd)
            replacement, clog = make_replacement2(pi, extra)
            changelog.append(clog)
            src = (src[:m.start()] + tabify(replacement) + src[m.end():])
            continue

        m = pattern3.search(src)
        if m:
            gd = m.groupdict()
            replacement = 'extern %(passkind)s *make_%(passname)s (context &ctxt);' % gd
            clog = '(struct %(passkind)s %(passname)s): Replace declaration with that of new function make_%(passname)s.\n' % gd
            changelog.append(clog)
            src = (src[:m.start()] + tabify(replacement) + src[m.end():])
            continue

        # no matches:
        break

    return src, changelog.content

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
