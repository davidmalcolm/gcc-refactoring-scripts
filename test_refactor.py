from refactor import refactor_pass_initializers
import unittest

class Tests(unittest.TestCase):
    def test_pass_jump2(self):
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
        expected = r"""
foo bar

class pass_jump2 : public rtl_opt_pass
{
 public:
  pass_jump2(context &ctxt)
    : rtl_opt_pass(ctxt,
                   "jump2",				/* name */
                   OPTGROUP_NONE,                   /* optinfo_flags */
                   TV_JUMP,				/* tv_id */
                   pass_properties(0, 0, 0),
                   pass_todo_flags(TODO_ggc_collect,
                                   TODO_verify_rtl_sharing,		))
  {}

  bool gate() { return NULL(); }
  unsigned int execute() { return execute_jump2(); }
};

rtl_opt_pass *
make_pass_jump2 (context &ctxt)
{
  return new pass_jump2 (ctxt);
}

baz qux
"""
        actual = refactor_pass_initializers(src)
        self.maxDiff = 1024
        self.assertMultiLineEqual(expected, actual) # 2.7+

if __name__ == '__main__':
    unittest.main()
