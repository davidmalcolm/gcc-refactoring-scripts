src = r"""
foo bar

struct rtl_opt_pass pass_jump2 =
{
 {
  RTL_PASS,
  "jump2",				/* name */
  OPTGROUP_NONE,                        /* optinfo_flags */
  NULL,					/* gate */
  execute_jump2,			/* execute */
  NULL,					/* sub */
  NULL,					/* next */
  0,					/* static_pass_number */
  TV_JUMP,				/* tv_id */
  0,					/* properties_required */
  0,					/* properties_provided */
  0,					/* properties_destroyed */
  TODO_ggc_collect,			/* todo_flags_start */
  TODO_verify_rtl_sharing,		/* todo_flags_finish */
 }
};

baz qux
"""

import re
ws = r'\s+'
optws = r'\s*'
def make_field(name):
    return (('(?P<%s>.*),' % name) + optws + "/\* (.*) \*/" + optws)

PATTERN = (
    'struct' + ws + 'rtl_opt_pass' + ws +r'(?P<classname>\S+)' + optws + '=' + optws +
    '{' + optws + '{' + optws +
    'RTL_PASS,' + optws +
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
    make_field('todo_flags_finish') +
    '}' + optws + '}' + optws + ';'
)

m = re.search(PATTERN, src,
              re.MULTILINE)
print(m)
if m:
    print(m.groups())
    d = m.groupdict()
    replacement = ('''class %(classname)s : public rtl_opt_pass
{
 public:
  %(classname)s(context &ctxt)
    : rtl_opt_pass(ctxt,
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
}''' % d)
    # FIXME: what about NULL gate?
    # FIXME: what about NULL execute?
    print(src[:m.start()] + replacement + src[m.end():])
