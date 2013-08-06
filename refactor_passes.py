from collections import namedtuple
import re
import sys

from refactor import main, Changelog, tabify

MAX_LINE_LENGTH = 76

MULTI_INSTANCE_PASSES = frozenset( (
    'pass_asan', # 2
    'pass_ccp', # 4
    'pass_cd_dce', # 2
    'pass_cleanup_eh', # 2
    'pass_copy_prop', # 8
    'pass_dce', # 3
    'pass_dce_loop', # 3
    'pass_dominator', # 2
    'pass_dse', # 2
    'pass_fixup_cfg', # 2
    'pass_fold_builtins', # 2
    'pass_forwprop', # 4
    'pass_fre', # 2
    'pass_inline_parameters', # 2
    'pass_late_warn_uninitialized', # 2
    'pass_lim', # 3
    'pass_local_pure_const', # 3
    'pass_lower_complex', # 2
    'pass_lower_vector_ssa', # 2
    'pass_merge_phi', # 2
    'pass_object_sizes', # 2
    'pass_phi_only_cprop', # 2
    'pass_phiopt', # 3
    'pass_reassoc', # 2
    'pass_rebuild_cgraph_edges', # 2
    'pass_remove_cgraph_callee_edges', # 3
    'pass_rename_ssa_copies', # 5
    'pass_rtl_cprop', # 3
    'pass_strip_predict_hints', # 2
    'pass_tail_recursion', # 2
    'pass_tsan', # 2
    'pass_uncprop', # 2
    'pass_vrp', # 2
    ) )

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

def to_flags(value):
    """
    Convert a string of the form 'flagA | flagB | flagC'
    to a list of strings: ['flagA', 'flagB', 'flagC']
    where 0 becomes ['0']
    """
    return [flag.strip()
            for flag in value.split('|')]

def clean_field(field):
    # Strip out C comments:
    field = re.sub(r'(/\*.*\*/)', '', field)
    # Strip out leading/trailing whitespace:
    field = field.strip()
    field = field.replace('\n', ' ')
    if '|' in field:
        field = ' | '.join(to_flags(field))
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

def make_data(d):
    if d['classname'].startswith('pass_'):
        d['dataname'] = 'pass_data_%s' % d['classname'][5:]
    else:
        assert d['classname'] == 'one_pass'
        d['dataname'] = 'pass_data_%s' % d['classname']

    def make_field(name, value):
        return '  %s, /* %s */\n' % (value, name)

    def make_simple_field(name):
        return make_field(name, d[name])

    def make_flags_field(name):
        """
        Add line-wraps so that long flag fields line-wrap like this:
          ( TODO_verify_flow | TODO_verify_stmts
            | TODO_update_ssa ), /* todo_flags_finish */
        """
        value = d[name]
        if '|' in value:
            flags = to_flags(value)
            termstr = ' ), /* %s */\n' % name
            result = '  ( %s' % flags[0]
            for flag in flags[1:]:
                next_ = ' | %s' % flag
                if len(result + next_ + termstr) > MAX_LINE_LENGTH:
                    result += '\n   '
                result += next_
            result += termstr
            return result
        else:
            return make_field(name, value)

    s = 'namespace {\n\n'
    s += 'const pass_data %(dataname)s =\n{\n' % d
    s += make_simple_field('type')
    s += make_simple_field('name')
    s += make_simple_field('optinfo_flags')
    s += make_field('has_gate',
                    'false' if is_null(d['gate']) else 'true')
    s += make_field('has_execute',
                    'false' if is_null(d['execute']) else 'true')
    s += make_simple_field('tv_id')
    s += make_flags_field('properties_required')
    s += make_flags_field('properties_provided')
    s += make_flags_field('properties_destroyed')
    s += make_flags_field('todo_flags_start')
    s += make_flags_field('todo_flags_finish')
    s += '};\n\n'
    return s

TEMPLATE_START_OF_CLASS = '''class %(classname)s : public %(passkind)s
{
public:
  %(classname)s(gcc::context *ctxt)
    : %(passkind)s(%(dataname)s, ctxt'''

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

TEMPLATE_FACTORY_FUNCTION = '''%(static)s%(passkind)s *
make_%(classname)s (gcc::context *ctxt)
{
  return new %(classname)s (ctxt);
}'''

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

def is_null(ptr):
    return ptr in ('NULL', '0')

def make_pass_methods(pi):
    d = pi._asdict()
    s = '\n'
    s += '  /* opt_pass methods: */\n'
    if d['passname'] in MULTI_INSTANCE_PASSES:
        s += make_method('opt_pass *', 'clone', (),
                         'return new %s (ctxt_);' % d['passname'], True)
    if d['gate'] not in ('NULL', '0'):
        s += make_method('bool', 'gate', (),
                         'return %s ();' % d['gate'], True)
    if d['execute'] not in ('NULL', '0'):
        s += make_method('unsigned int', 'execute', (),
                         'return %s ();' % d['execute'], True)
    return s

def add_to_changelog(d, changelog):
    changelog.append('%(classname)s' % d,
                     ('Convert from a global struct to a subclass of'
                      ' %(passkind)s along with...' % d))
    changelog.append('%(dataname)s' % d,
                     '...new pass_data instance and...')
    changelog.append('make_%(classname)s' % d,
                     '...new function.')

def finish_class(d):
    result = '\n}; // class %s\n\n' % d['classname']
    result += '} // anon namespace\n\n'
    return result

def make_replacement(pi, changelog):
    d = pi._asdict()
    d['classname'] = pi.passname
    s = make_data(d)
    s += TEMPLATE_START_OF_CLASS % d
    s += ')\n  {}\n'
    s += make_pass_methods(pi)
    s += finish_class(d)
    s += TEMPLATE_FACTORY_FUNCTION % d

    add_to_changelog(d, changelog)

    return s

def make_replacement2(pi, extra, changelog):
    d = pi._asdict()
    d.update(extra._asdict())
    d['classname'] = pi.passname
    s = make_data(d)
    s += TEMPLATE_START_OF_CLASS % d
    s += ',\n'
    for extra in EXTRA_FIELDS[:-1]:
        assert extra != d[extra]
        s += '                     %s, /* %s */\n' % (d[extra], extra)
    extra = EXTRA_FIELDS[-1]
    assert extra != d[extra]
    s += '                     %s) /* %s */\n' % (d[extra], extra)
    s += '  {}\n'
    s += make_pass_methods(pi)
    s += finish_class(d)

    s += TEMPLATE_FACTORY_FUNCTION % d

    add_to_changelog(d, changelog)

    return s

def refactor_pass_initializers(filename, src):
    changelog = Changelog(filename)
    while 1:
        m = src.search(pattern)
        if m:
            gd = m.groupdict()
            pi = parse_basic_fields(gd)
            replacement = make_replacement(pi, changelog)
            src = src.replace(m.start(), m.end(), tabify(replacement))
            continue

        m = src.search(pattern2)
        if m:
            gd = m.groupdict()
            pi = parse_basic_fields(gd)
            extra = parse_extra_fields(gd)
            replacement = make_replacement2(pi, extra, changelog)
            src = src.replace(m.start(), m.end(), tabify(replacement))
            continue

        m = src.search(pattern3)
        if m:
            gd = m.groupdict()
            replacement = 'extern %(passkind)s *make_%(passname)s (gcc::context *ctxt);' % gd
            changelog.append('%(passname)s' % gd,
                             'Replace declaration with that of...')
            changelog.append('make_%(passname)s' % gd,
                             '...new function.')
            src = src.replace(m.start(), m.end(), tabify(replacement))
            continue

        # no matches:
        break

    src = src.wrap(tabify_changes=1)
    return src.str(as_tabs=0), changelog

if __name__ == '__main__':
    main('refactor_passes.py', refactor_pass_initializers, sys.argv)
