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
    : %(passkind)s(ctxt,
                   %(name)s,				/* name */
                   %(optinfo_flags)s,                   /* optinfo_flags */
                   %(tv_id)s,				/* tv_id */
                   pass_properties(%(properties_required)s, %(properties_provided)s, %(properties_destroyed)s),
                   pass_todo_flags(%(todo_flags_start)s,
                                   %(todo_flags_finish)s)'''

TEMPLATE_FACTORY_FUNCTION = '''%(static)s%(passkind)s *
make_%(classname)s (context &ctxt)
{
  return new %(classname)s (ctxt);
}'''

TEMPLATE_CLOG = ('(struct %(passkind)s %(classname)s): convert from a global struct to a subclass of %(passkind)s\n'
                 '(make_%(classname)s): New function to create an instance of the new class %(classname)s\n')

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
    result = ('  %s %s(%s) %s\n'
                % (returntype, name, argdecl, block))
    # line-wrap at 76 chars:
    if len(result) > 76:
        result = ('  %s %s(%s) {\n'
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
       bool has_FOO()   // equivalent to (pass->FOO != NULL) in old code
    and
       impl_FOO()       // equivalent to (pass->FOO ()) in old code
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
    s += r''')
  {}
'''
    s += make_pass_methods(pi)
    s += '};\n\n'

    s += TEMPLATE_FACTORY_FUNCTION % d

    clog = TEMPLATE_CLOG % d

    return s, clog

def make_replacement2(pi, extra):
    d = pi._asdict()
    d.update(extra._asdict())
    d['classname'] = pi.passname
    s = TEMPLATE_START_OF_CLASS % d
    s += r''',
                   %(function_transform_todo_flags_start)s) /* function_transform_todo_flags_start */
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
    s += '};\n\n'

    s += TEMPLATE_FACTORY_FUNCTION % d

    clog = TEMPLATE_CLOG % d

    return s, clog

class Changelog:
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

def refactor_pass_initializers(filename, src):
    changelog = Changelog(filename)
    while 1:
        m = pattern.search(src)
        if m:
            gd = m.groupdict()
            pi = parse_basic_fields(gd)
            replacement, clog = make_replacement(pi)
            changelog.append(clog)
            src = (src[:m.start()] + replacement + src[m.end():])
            continue

        m = pattern2.search(src)
        if m:
            gd = m.groupdict()
            pi = parse_basic_fields(gd)
            extra = parse_extra_fields(gd)
            replacement, clog = make_replacement2(pi, extra)
            changelog.append(clog)
            src = (src[:m.start()] + replacement + src[m.end():])
            continue

        m = pattern3.search(src)
        if m:
            gd = m.groupdict()
            replacement = 'extern %(passkind)s *make_%(passname)s (context &ctxt);' % gd
            clog = '(struct %(passkind)s %(passname)s): replace declaration with that of new function make_%(passname)s\n' % gd
            changelog.append(clog)
            src = (src[:m.start()] + replacement + src[m.end():])
            continue

        # no matches:
        break

    return src, changelog.content

def refactor_file(path, printdiff, applychanges):
    with open(path) as f:
        src = f.read()
    #print(src)
    assert path.startswith('../src/gcc/')
    filename = path[len('../src/gcc/'):]
    dst, changelog = refactor_pass_initializers(filename, src)
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

def add_to_changelog(filename, author, entry):
    with open(filename, 'r') as f:
        old_contents = f.read()
    today = date.today()
    header = '%s  %s  <%s>' % (today.isoformat(),
                               author.name,
                               author.email)
    new_contents = header + '\n\n' + entry + '\n' + old_contents
    with open(filename, 'w') as f:
        f.write(new_contents)

def get_revision():
    return check_output(['git', 'rev-parse', 'HEAD']).strip()

if __name__ == '__main__':
    AUTHOR = Author('David Malcolm', 'dmalcolm@redhat.com')
    SCRIPT = 'refactor.py'
    GIT_URL = 'https://github.com/davidmalcolm/gcc-refactoring-scripts'
    revision = get_revision()
    clog_entry = wrap('Patch autogenerated by %s from\n'
                      '%s\n'
                      'revision %s'
                      % (SCRIPT, GIT_URL, revision))
    clog_entry += '\n'
    def visit(arg, dirname, names):
        global clog_entry
        for name in sorted(names):
            path = os.path.join(dirname, name)
            if os.path.isfile(path) \
                    and (path.endswith('.c') or
                         path.endswith('.h')):
                print(path)
                clog_entry += refactor_file(path,
                                           printdiff=True,
                                           applychanges=True)
    os.path.walk('../src/gcc', visit, None)
    print(clog_entry)
    add_to_changelog('../src/gcc/ChangeLog', AUTHOR, clog_entry)
