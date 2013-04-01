from collections import namedtuple
from difflib import unified_diff
import re
import sys

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
                                 tuple(['passkind', 'passname'] + list(FIELDS)))):
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
    'struct' + ws + '(?P<passkind>\S+_opt_pass)' + ws +r'(?P<passname>\S+)' + optws + '=' + optws +
    '{' + optws + '{' + optws +
    '(?P<fields>.*)' +
    '}' + optws + '}' + optws + ';'
)
pattern = re.compile(PATTERN, re.MULTILINE | re.DOTALL)

# struct ipa_opt_pass_d is more complicated due to extra fields at the end:
PATTERN2 = (
    'struct' + ws + '(?P<passkind>ipa_opt_pass_d)' + ws +r'(?P<passname>\S+)' + optws + '=' + optws +
    '{' + optws + '{' + optws +
    '(?P<fields>.*)' +
    '}' + '(?P<extrafields>.*)' + '}' + optws + ';'
)
pattern2 = re.compile(PATTERN2, re.MULTILINE | re.DOTALL)

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

    assert len(fields) == 14

    pi = PassInitializer(gd['passkind'],
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

TEMPLATE_FACTORY_FUNCTION = '''%(passkind)s *
make_%(classname)s (context &ctxt)
{
  return new %(classname)s (ctxt);
}'''

def make_method(d, returntype, name, args):
    argdecl = ', '.join(['%s%s' % (type_, argname)
                         for type_, argname in args])
    argusage = ', '.join([argname
                         for type_, argname in args])
    optreturn = 'return ' if returntype != 'void' else ''
    existingfn = d[name]
    if existingfn == 'NULL':
        if returntype == 'void':
            # Assume a NULL function ptr "returning" void is to become
            # a do-nothing hook:
            body = ''
        else:
            assert name == 'gate'
            body = 'return true;'
    else:
        body = ('%s%s (%s);'
                % (optreturn, existingfn, argusage))
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

def make_pass_methods(pi):
    d = pi._asdict()
    s = '\n'
    s += '  /* opt_pass methods: */\n'
    s += make_method(d, 'bool', 'gate', () )
    s += make_method(d, 'unsigned int', 'execute', () )
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

    return s

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
    s += '\n'
    s += '  /* ipa_opt_pass_d methods: */\n'
    s += make_method(d, 'void', 'generate_summary', [] )
    s += make_method(d, 'void', 'write_summary', [] )
    s += make_method(d, 'void', 'read_summary', [] )
    s += make_method(d, 'void', 'write_optimization_summary', [] )
    s += make_method(d, 'void', 'read_optimization_summary', [] )
    s += make_method(d, 'void', 'stmt_fixup',
                     [('struct cgraph_node *', 'node'),
                      ('gimple *', 'stmt')])
    s += make_method(d, 'unsigned int', 'function_transform',
                     [('struct cgraph_node *', 'node')])
    s += make_method(d, 'void', 'variable_transform',
                     [('struct varpool_node *', 'node')])
    s += '\n};\n\n'

    s += TEMPLATE_FACTORY_FUNCTION % d

    return s

def refactor_pass_initializers(src):
    while 1:
        m = pattern.search(src)
        if m:
            gd = m.groupdict()
            pi = parse_basic_fields(gd)
            replacement = make_replacement(pi)
            src = (src[:m.start()] + replacement + src[m.end():])
        else:
            m = pattern2.search(src)
            if m:
                gd = m.groupdict()
                pi = parse_basic_fields(gd)
                extra = parse_extra_fields(gd)
                replacement = make_replacement2(pi, extra)
                src = (src[:m.start()] + replacement + src[m.end():])
            else:
                break
    return src

def refactor_file(path):
    with open(path) as f:
        src = f.read()
    #print(src)
    dst = refactor_pass_initializers(src)
    #print(dst)

    for line in unified_diff(src.splitlines(),
                             dst.splitlines(),
                             fromfile=path, tofile=path):
        sys.stdout.write('%s\n' % line)

if __name__ == '__main__':
    # examples of "struct rtl_opt_pass foo = {};"
    refactor_file('../src/gcc/cfgrtl.c')

    # examples of "struct gimple_opt_pass foo = {};"
    refactor_file('../src/gcc/tree-mudflap.c')

