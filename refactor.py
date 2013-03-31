from difflib import unified_diff
import re
import sys

ws = r'\s+'
optws = r'\s*'
def make_field(name):
    return (('(?P<%s>.*),' % name) + optws + "/\* (.*) \*/" + optws)

def make_final_field(name):
    # trailing comma is optional:
    return (('(?P<%s>.*),?' % name) + optws + "/\* (.*) \*/" + optws)

PATTERN = (
    'struct' + ws + '(?P<passkind>\S+_opt_pass)' + ws +r'(?P<classname>\S+)' + optws + '=' + optws +
    '{' + optws + '{' + optws +
    '(\S+_PASS),' + optws +
    make_field('name') +
    make_field('optinfo_flags') +
    make_field('gate') +
    make_field('execute') +
    make_field('sub') +
    make_field('next') +
    make_field('static_pass_number') +
    make_field('tv_id') +
    make_field('properties_required') +
    make_field('properties_provided') +
    make_field('properties_destroyed') +
    make_field('todo_flags_start') +
    make_final_field('todo_flags_finish') +
    '}' + optws + '}' + optws + ';'
)

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
        m = re.search(PATTERN, src, re.MULTILINE)
        if m:
            # print(m.groups())
            d = m.groupdict()
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

