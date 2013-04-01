from refactor import refactor_pass_initializers
import unittest

class Tests(unittest.TestCase):
    def assertRefactoringEquals(self, src, expected):
        actual = refactor_pass_initializers(src)
        self.maxDiff = 4096
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
                                   TODO_verify_rtl_sharing))
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
                                   0))
  {}

  bool gate() { return gate_mudflap(); }
  unsigned int execute() { return execute_mudflap_function_decls(); }
};

gimple_opt_pass *
make_pass_mudflap_1 (context &ctxt)
{
  return new pass_mudflap_1 (ctxt);
}
"""
        self.assertRefactoringEquals(src, expected)

    def test_pass_mudflap2(self):
        # This one has non-trivial properties and flags
        src = r"""
struct gimple_opt_pass pass_mudflap_2 =
{
 {
  GIMPLE_PASS,
  "mudflap2",                           /* name */
  OPTGROUP_NONE,                        /* optinfo_flags */
  gate_mudflap,                         /* gate */
  execute_mudflap_function_ops,         /* execute */
  NULL,                                 /* sub */
  NULL,                                 /* next */
  0,                                    /* static_pass_number */
  TV_NONE,                              /* tv_id */
  PROP_ssa | PROP_cfg | PROP_gimple_leh,/* properties_required */
  0,                                    /* properties_provided */
  0,                                    /* properties_destroyed */
  0,                                    /* todo_flags_start */
  TODO_verify_flow | TODO_verify_stmts
  | TODO_update_ssa                     /* todo_flags_finish */
 }
};
"""
        expected = r"""
class pass_mudflap_2 : public gimple_opt_pass
{
 public:
  pass_mudflap_2(context &ctxt)
    : gimple_opt_pass(ctxt,
                   "mudflap2",				/* name */
                   OPTGROUP_NONE,                   /* optinfo_flags */
                   TV_NONE,				/* tv_id */
                   pass_properties(PROP_ssa | PROP_cfg | PROP_gimple_leh, 0, 0),
                   pass_todo_flags(0,
                                   TODO_verify_flow | TODO_verify_stmts   | TODO_update_ssa))
  {}

  bool gate() { return gate_mudflap(); }
  unsigned int execute() { return execute_mudflap_function_ops(); }
};

gimple_opt_pass *
make_pass_mudflap_2 (context &ctxt)
{
  return new pass_mudflap_2 (ctxt);
}
"""
        self.assertRefactoringEquals(src, expected)

    def test_pass_ipa_pta(self):
        # Test of a simple_ipa_opt_pass (from gcc/tree-ssa-structalias.c)
        src = r"""struct simple_ipa_opt_pass pass_ipa_pta =
{
 {
  SIMPLE_IPA_PASS,
  "pta",		                /* name */
  OPTGROUP_NONE,                        /* optinfo_flags */
  gate_ipa_pta,			/* gate */
  ipa_pta_execute,			/* execute */
  NULL,					/* sub */
  NULL,					/* next */
  0,					/* static_pass_number */
  TV_IPA_PTA,		        /* tv_id */
  0,	                                /* properties_required */
  0,					/* properties_provided */
  0,					/* properties_destroyed */
  0,					/* todo_flags_start */
  TODO_update_ssa                       /* todo_flags_finish */
 }
};
"""
        expected = r"""class pass_ipa_pta : public simple_ipa_opt_pass
{
 public:
  pass_ipa_pta(context &ctxt)
    : simple_ipa_opt_pass(ctxt,
                   "pta",				/* name */
                   OPTGROUP_NONE,                   /* optinfo_flags */
                   TV_IPA_PTA,				/* tv_id */
                   pass_properties(0, 0, 0),
                   pass_todo_flags(0,
                                   TODO_update_ssa))
  {}

  bool gate() { return gate_ipa_pta(); }
  unsigned int execute() { return ipa_pta_execute(); }
};

simple_ipa_opt_pass *
make_pass_ipa_pta (context &ctxt)
{
  return new pass_ipa_pta (ctxt);
}
"""
        self.assertRefactoringEquals(src, expected)

    def test_pass_ipa_cp(self):
        # Test of a ipa_opt_pass_d (from gcc/ipa-cp.c)
        # struct ipa_opt_pass_d pass_ipa_cp;
        src = r"""
struct ipa_opt_pass_d pass_ipa_cp =
{
 {
  IPA_PASS,
  "cp",				/* name */
  OPTGROUP_NONE,                /* optinfo_flags */
  cgraph_gate_cp,		/* gate */
  ipcp_driver,			/* execute */
  NULL,				/* sub */
  NULL,				/* next */
  0,				/* static_pass_number */
  TV_IPA_CONSTANT_PROP,		/* tv_id */
  0,				/* properties_required */
  0,				/* properties_provided */
  0,				/* properties_destroyed */
  0,				/* todo_flags_start */
  TODO_dump_symtab |
  TODO_remove_functions | TODO_ggc_collect /* todo_flags_finish */
 },
 ipcp_generate_summary,			/* generate_summary */
 ipcp_write_summary,			/* write_summary */
 ipcp_read_summary,			/* read_summary */
 ipa_prop_write_all_agg_replacement,	/* write_optimization_summary */
 ipa_prop_read_all_agg_replacement,	/* read_optimization_summary */
 NULL,			 		/* stmt_fixup */
 0,					/* TODOs */
 ipcp_transform_function,		/* function_transform */
 NULL,					/* variable_transform */
};
"""
        expected = r"""
"""
        self.assertRefactoringEquals(src, expected)

    def test_pass_ipa_cp(self):
        # Test of a ipa_opt_pass_d (from gcc/ipa-cp.c)
        # struct ipa_opt_pass_d pass_ipa_cp;
        src = r"""
struct ipa_opt_pass_d pass_ipa_cp =
{
 {
  IPA_PASS,
  "cp",				/* name */
  OPTGROUP_NONE,                /* optinfo_flags */
  cgraph_gate_cp,		/* gate */
  ipcp_driver,			/* execute */
  NULL,				/* sub */
  NULL,				/* next */
  0,				/* static_pass_number */
  TV_IPA_CONSTANT_PROP,		/* tv_id */
  0,				/* properties_required */
  0,				/* properties_provided */
  0,				/* properties_destroyed */
  0,				/* todo_flags_start */
  TODO_dump_symtab |
  TODO_remove_functions | TODO_ggc_collect /* todo_flags_finish */
 },
 ipcp_generate_summary,			/* generate_summary */
 ipcp_write_summary,			/* write_summary */
 ipcp_read_summary,			/* read_summary */
 ipa_prop_write_all_agg_replacement,	/* write_optimization_summary */
 ipa_prop_read_all_agg_replacement,	/* read_optimization_summary */
 NULL,			 		/* stmt_fixup */
 0,					/* TODOs */
 ipcp_transform_function,		/* function_transform */
 NULL,					/* variable_transform */
};
"""
        expected = r"""
class pass_ipa_cp : public ipa_opt_pass_d
{
 public:
  pass_ipa_cp(context &ctxt)
    : ipa_opt_pass_d(ctxt,
                   "cp",				/* name */
                   OPTGROUP_NONE,                   /* optinfo_flags */
                   TV_IPA_CONSTANT_PROP,				/* tv_id */
                   pass_properties(0, 0, 0),
                   pass_todo_flags(0,
                                   TODO_dump_symtab |   TODO_remove_functions | TODO_ggc_collect),
                   0) /* function_transform_todo_flags_start */
  {}

  bool gate() { return cgraph_gate_cp(); }
  unsigned int execute() { return ipcp_driver(); }

  void generate_summary() { ipcp_generate_summary (); }
  void write_summary() { ipcp_write_summary (); }
  void read_summary() { ipcp_read_summary (); }
  void write_optimization_summary() { ipa_prop_write_all_agg_replacement (); }
  void read_optimization_summary() { ipa_prop_read_all_agg_replacement (); }
  void stmt_fixup(struct cgraph_node *node, gimple *stmt) {
    NULL (node, stmt);  // FIXME!
  }
  unsigned int function_transform(struct cgraph_node *node) {
    return ipcp_transform_function (node);
  }
  void variable_transform(struct varpool_node *node) {
    NULL (node);  // FIXME!
  }

};

ipa_opt_pass_d *
make_pass_ipa_cp (context &ctxt)
{
  return new pass_ipa_cp (ctxt);
}
"""
        self.assertRefactoringEquals(src, expected)

if __name__ == '__main__':
    unittest.main()
