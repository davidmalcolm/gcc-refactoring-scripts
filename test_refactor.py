from refactor import refactor_pass_initializers
import unittest

class Tests(unittest.TestCase):
    def assertRefactoringEquals(self, src, expected):
        actual = refactor_pass_initializers(src)
        self.maxDiff = 1024
        self.assertMultiLineEqual(expected, actual) # 2.7+

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
        self.assertRefactoringEquals(src, expected)


    def test_pass_mudflap1(self):
        src = r"""
struct gimple_opt_pass pass_mudflap_1 =
{
 {
  GIMPLE_PASS,
  "mudflap1",                           /* name */
  OPTGROUP_NONE,                        /* optinfo_flags */
  gate_mudflap,                         /* gate */
  execute_mudflap_function_decls,       /* execute */
  NULL,                                 /* sub */
  NULL,                                 /* next */
  0,                                    /* static_pass_number */
  TV_NONE,                              /* tv_id */
  PROP_gimple_any,                      /* properties_required */
  0,                                    /* properties_provided */
  0,                                    /* properties_destroyed */
  0,                                    /* todo_flags_start */
  0                                     /* todo_flags_finish */
 }
};
"""
        expected = r"""
class pass_mudflap_1 : public gimple_opt_pass
{
 public:
  pass_mudflap_1(context &ctxt)
    : gimple_opt_pass(ctxt,
                   "mudflap1",				/* name */
                   OPTGROUP_NONE,                   /* optinfo_flags */
                   TV_NONE,				/* tv_id */
                   pass_properties(PROP_gimple_any, 0, 0),
                   pass_todo_flags(0,
                                   0                                     ))
  {}

  bool gate() { return gate_mudflap(); }
  unsigned int execute() { return execute_mudflap_function_decls(); }
};

rtl_opt_pass *
make_pass_mudflap_1 (context &ctxt)
{
  return new pass_mudflap_1 (ctxt);
}
"""
        self.assertRefactoringEquals(src, expected)


if __name__ == '__main__':
    unittest.main()
