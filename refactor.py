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

ws = r'\s+'
optws = r'\s*'

PATTERN = (
    'struct' + ws + '(?P<passkind>\S+_opt_pass)' + ws +r'(?P<passname>\S+)' + optws + '=' + optws +
    '{' + optws + '{' + optws +
    '(?P<fields>.*)' +
    '}' + optws + '}' + optws + ';'
)
pattern = re.compile(PATTERN, re.MULTILINE | re.DOTALL)

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

rtl_opt_pass *
make_%(classname)s (context &ctxt)
{
  return new %(classname)s (ctxt);
}'''

def refactor_pass_initializers(src):
    while 1:
        m = pattern.search(src)
        if m:
            gd = m.groupdict()
            fields = []
            for field in gd['fields'].split(','):
                # Strip out C comments:
                field = re.sub(r'(/\*.*\*/)', '', field)
                # Strip out leading/trailing whitespace:
                field = field.strip()
                field = field.replace('\n', ' ')
                fields.append(field)

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

            d = pi._asdict()
            d['classname'] = pi.passname
            #d['passkind'] = pi.passkind
            replacement = TEMPLATE % d
            src = (src[:m.start()] + replacement + src[m.end():])
            # FIXME: what about NULL gate?
            # FIXME: what about NULL execute?
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

