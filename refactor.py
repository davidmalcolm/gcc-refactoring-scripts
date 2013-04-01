from collections import namedtuple
from difflib import unified_diff
import re
import sys

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

TEMPLATE = '''class %(classname)s : public %(passkind)s
{
 public:
  %(classname)s(context &ctxt)
    : %(passkind)s(ctxt,
                   %(name)s,				/* name */
                   %(optinfo_flags)s,                   /* optinfo_flags */
                   %(tv_id)s,				/* tv_id */
                   pass_properties(%(properties_required)s, %(properties_provided)s, %(properties_destroyed)s),
                   pass_todo_flags(%(todo_flags_start)s,
                                   %(todo_flags_finish)s))
  {}

  bool gate() { return %(gate)s(); }
  unsigned int execute() { return %(execute)s(); }
};

%(passkind)s *
make_%(classname)s (context &ctxt)
{
  return new %(classname)s (ctxt);
}'''

TEMPLATE2 = '''class %(classname)s : public %(passkind)s
{
 public:
  %(classname)s(context &ctxt)
    : %(passkind)s(ctxt,
                   %(name)s,				/* name */
                   %(optinfo_flags)s,                   /* optinfo_flags */
                   %(tv_id)s,				/* tv_id */
                   pass_properties(%(properties_required)s, %(properties_provided)s, %(properties_destroyed)s),
                   pass_todo_flags(%(todo_flags_start)s,
                                   %(todo_flags_finish)s),
                   %(function_transform_todo_flags_start)s) /* function_transform_todo_flags_start */
  {}

  bool gate() { return %(gate)s(); }
  unsigned int execute() { return %(execute)s(); }

  void generate_summary() { %(generate_summary)s (); }
  void write_summary() { %(write_summary)s (); }
  void read_summary() { %(read_summary)s (); }
  void write_optimization_summary() { %(write_optimization_summary)s (); }
  void read_optimization_summary() { %(read_optimization_summary)s (); }
  void stmt_fixup(struct cgraph_node *node, gimple *stmt) {
    %(stmt_fixup)s (node, stmt);
  }
  unsigned int function_transform(struct cgraph_node *node) {
    return %(function_transform)s (node);
  }
  void variable_transform(struct varpool_node *node) {
    %(variable_transform)s (node);
  }

};

%(passkind)s *
make_%(classname)s (context &ctxt)
{
  return new %(classname)s (ctxt);
}'''

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

def refactor_pass_initializers(src):
    while 1:
        m = pattern.search(src)
        if m:
            gd = m.groupdict()
            pi = parse_basic_fields(gd)
            d = pi._asdict()
            d['classname'] = pi.passname
            replacement = TEMPLATE % d
            src = (src[:m.start()] + replacement + src[m.end():])
            # FIXME: what about NULL gate?
            # FIXME: what about NULL execute?
        else:
            m = pattern2.search(src)
            if m:
                gd = m.groupdict()
                pi = parse_basic_fields(gd)
                d = pi._asdict()
                d['classname'] = pi.passname
                extra = parse_extra_fields(gd)
                d.update(extra._asdict())
                replacement = TEMPLATE2 % d
                src = (src[:m.start()] + replacement + src[m.end():])
                # FIXME: what about NULL callbacks?
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

