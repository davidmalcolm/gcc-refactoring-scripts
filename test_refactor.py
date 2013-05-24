from refactor import refactor_pass_initializers, tabify
import unittest

class GeneralTests(unittest.TestCase):
    def assertTabifyEquals(self, input_code, expected_result):
        actual_result = tabify(input_code)
        self.maxDiff = 8192
        self.assertMultiLineEqual(expected_result, actual_result) # 2.7+

    def test_tabify(self):
        self.assertTabifyEquals(
            input_code=('public:\n'
                        '  pass_jump2(context &ctxt)\n'
                        '    : rtl_opt_pass(ctxt,\n'
                        '                   "jump2",\n'
                        '                   OPTGROUP_NONE,\n'),
            expected_result=('public:\n'
                             '  pass_jump2(context &ctxt)\n'
                             '    : rtl_opt_pass(ctxt,\n'
                             '\t\t   "jump2",\n'
                             '\t\t   OPTGROUP_NONE,\n'))

class PassConversionTests(unittest.TestCase):
    def assertRefactoringEquals(self,
                                src, filename,
                                expected_code, expected_changelog):
        actual_code, actual_changelog = refactor_pass_initializers(filename, src)
        self.maxDiff = 8192
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
        self.assertMultiLineEqual(expected_changelog, actual_changelog) # 2.7+

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
        expected_code = """
foo bar

class pass_jump2 : public rtl_opt_pass
{
public:
  pass_jump2(context &ctxt)
    : rtl_opt_pass(ctxt,
\t\t   "jump2",
\t\t   OPTGROUP_NONE,
\t\t   TV_JUMP,
\t\t   pass_properties(required(0),
\t\t\t\t   provided(0),
\t\t\t\t   destroyed(0)),
\t\t   pass_todo_flags(start(TODO_ggc_collect),
\t\t\t\t   finish(TODO_verify_rtl_sharing)))
  {}

  /* opt_pass methods: */
  bool has_gate () { return false; }
  bool gate () { return true; }

  bool has_execute () { return true; }
  unsigned int impl_execute () { return execute_jump2 (); }

}; // class pass_jump2

rtl_opt_pass *
make_pass_jump2 (context &ctxt)
{
  return new pass_jump2 (ctxt);
}

baz qux
"""
        expected_changelog = \
            ('\t* cfgcleanup.c (struct rtl_opt_pass pass_jump2): Convert from a global\n'
             '\tstruct to a subclass of rtl_opt_pass.\n'
             '\t(make_pass_jump2): New function to create an instance of the new class\n'
             '\tpass_jump2.\n')

        self.assertRefactoringEquals(src, 'cfgcleanup.c',
                                     expected_code, expected_changelog)


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
        expected_code = """
class pass_mudflap_1 : public gimple_opt_pass
{
public:
  pass_mudflap_1(context &ctxt)
    : gimple_opt_pass(ctxt,
\t\t      "mudflap1",
\t\t      OPTGROUP_NONE,
\t\t      TV_NONE,
\t\t      pass_properties(required(PROP_gimple_any),
\t\t\t\t      provided(0),
\t\t\t\t      destroyed(0)),
\t\t      pass_todo_flags(start(0),
\t\t\t\t      finish(0)))
  {}

  /* opt_pass methods: */
  bool has_gate () { return true; }
  bool gate () { return gate_mudflap (); }

  bool has_execute () { return true; }
  unsigned int impl_execute () {
    return execute_mudflap_function_decls ();
  }

}; // class pass_mudflap_1

gimple_opt_pass *
make_pass_mudflap_1 (context &ctxt)
{
  return new pass_mudflap_1 (ctxt);
}
"""
        expected_changelog = \
            ('\t* tree-mudflap.c (struct gimple_opt_pass pass_mudflap_1): Convert from\n'
             '\ta global struct to a subclass of gimple_opt_pass.\n'
             '\t(make_pass_mudflap_1): New function to create an instance of the new\n'
             '\tclass pass_mudflap_1.\n')

        self.assertRefactoringEquals(src, 'tree-mudflap.c',
                                     expected_code, expected_changelog)

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
        expected_code = """
class pass_mudflap_2 : public gimple_opt_pass
{
public:
  pass_mudflap_2(context &ctxt)
    : gimple_opt_pass(ctxt,
\t\t      "mudflap2",
\t\t      OPTGROUP_NONE,
\t\t      TV_NONE,
\t\t      pass_properties(required(PROP_ssa | PROP_cfg | PROP_gimple_leh),
\t\t\t\t      provided(0),
\t\t\t\t      destroyed(0)),
\t\t      pass_todo_flags(start(0),
\t\t\t\t      finish(TODO_verify_flow | TODO_verify_stmts | TODO_update_ssa)))
  {}

  /* opt_pass methods: */
  bool has_gate () { return true; }
  bool gate () { return gate_mudflap (); }

  bool has_execute () { return true; }
  unsigned int impl_execute () { return execute_mudflap_function_ops (); }

}; // class pass_mudflap_2

gimple_opt_pass *
make_pass_mudflap_2 (context &ctxt)
{
  return new pass_mudflap_2 (ctxt);
}
"""
        expected_changelog = \
            ('\t* tree-mudflap.c (struct gimple_opt_pass pass_mudflap_2): Convert from\n'
             '\ta global struct to a subclass of gimple_opt_pass.\n'
             '\t(make_pass_mudflap_2): New function to create an instance of the new\n'
             '\tclass pass_mudflap_2.\n')

        self.assertRefactoringEquals(src, 'tree-mudflap.c',
                                     expected_code, expected_changelog)

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
        expected_code = """class pass_ipa_pta : public simple_ipa_opt_pass
{
public:
  pass_ipa_pta(context &ctxt)
    : simple_ipa_opt_pass(ctxt,
\t\t\t  "pta",
\t\t\t  OPTGROUP_NONE,
\t\t\t  TV_IPA_PTA,
\t\t\t  pass_properties(required(0),
\t\t\t\t\t  provided(0),
\t\t\t\t\t  destroyed(0)),
\t\t\t  pass_todo_flags(start(0),
\t\t\t\t\t  finish(TODO_update_ssa)))
  {}

  /* opt_pass methods: */
  bool has_gate () { return true; }
  bool gate () { return gate_ipa_pta (); }

  bool has_execute () { return true; }
  unsigned int impl_execute () { return ipa_pta_execute (); }

}; // class pass_ipa_pta

simple_ipa_opt_pass *
make_pass_ipa_pta (context &ctxt)
{
  return new pass_ipa_pta (ctxt);
}
"""
        expected_changelog = \
            ('\t* tree-ssa-structalias.c (struct simple_ipa_opt_pass pass_ipa_pta):\n'
             '\tConvert from a global struct to a subclass of simple_ipa_opt_pass.\n'
             '\t(make_pass_ipa_pta): New function to create an instance of the new\n'
             '\tclass pass_ipa_pta.\n')

        self.assertRefactoringEquals(src, 'tree-ssa-structalias.c',
                                     expected_code, expected_changelog)

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
        expected_code = """
class pass_ipa_cp : public ipa_opt_pass_d
{
public:
  pass_ipa_cp(context &ctxt)
    : ipa_opt_pass_d(ctxt,
\t\t     "cp",
\t\t     OPTGROUP_NONE,
\t\t     TV_IPA_CONSTANT_PROP,
\t\t     pass_properties(required(0),
\t\t\t\t     provided(0),
\t\t\t\t     destroyed(0)),
\t\t     pass_todo_flags(start(0),
\t\t\t\t     finish(TODO_dump_symtab | TODO_remove_functions | TODO_ggc_collect)),
\t\t     0) /* function_transform_todo_flags_start */
  {}

  /* opt_pass methods: */
  bool has_gate () { return true; }
  bool gate () { return cgraph_gate_cp (); }

  bool has_execute () { return true; }
  unsigned int impl_execute () { return ipcp_driver (); }

  /* ipa_opt_pass_d methods: */
  bool has_generate_summary () { return true; }
  void impl_generate_summary () { ipcp_generate_summary (); }

  bool has_write_summary () { return true; }
  void impl_write_summary () { ipcp_write_summary (); }

  bool has_read_summary () { return true; }
  void impl_read_summary () { ipcp_read_summary (); }

  bool has_write_optimization_summary () { return true; }
  void impl_write_optimization_summary () {
    ipa_prop_write_all_agg_replacement ();
  }

  bool has_read_optimization_summary () { return true; }
  void impl_read_optimization_summary () {
    ipa_prop_read_all_agg_replacement ();
  }

  bool has_stmt_fixup () { return false; }
  void impl_stmt_fixup (struct cgraph_node *, gimple *) { }

  bool has_function_transform () { return true; }
  unsigned int impl_function_transform (struct cgraph_node *node) {
    return ipcp_transform_function (node);
  }

  bool has_variable_transform () { return false; }
  void impl_variable_transform (struct varpool_node *) { }

}; // class pass_ipa_cp

ipa_opt_pass_d *
make_pass_ipa_cp (context &ctxt)
{
  return new pass_ipa_cp (ctxt);
}
"""
        expected_changelog = \
            ('\t* ipa-cp.c (struct ipa_opt_pass_d pass_ipa_cp): Convert from a global\n'
             '\tstruct to a subclass of ipa_opt_pass_d.\n'
             '\t(make_pass_ipa_cp): New function to create an instance of the new\n'
             '\tclass pass_ipa_cp.\n')

        self.assertRefactoringEquals(src, 'ipa-cp.c',
                                     expected_code, expected_changelog)

    def test_pass_ipa_whole_program_visibility(self):
        # Ensure regexps aren't too greedy, thus splitting
        # these two
        # Also, test of NULL for ipa_opt_pass_d callbacks
        src = r"""
struct ipa_opt_pass_d pass_ipa_whole_program_visibility =
{
 {
  IPA_PASS,
  "whole-program",			/* name */
  OPTGROUP_NONE,                        /* optinfo_flags */
  gate_whole_program_function_and_variable_visibility,/* gate */
  whole_program_function_and_variable_visibility,/* execute */
  NULL,					/* sub */
  NULL,					/* next */
  0,					/* static_pass_number */
  TV_CGRAPHOPT,				/* tv_id */
  0,	                                /* properties_required */
  0,					/* properties_provided */
  0,					/* properties_destroyed */
  0,					/* todo_flags_start */
  TODO_remove_functions | TODO_dump_symtab
  | TODO_ggc_collect			/* todo_flags_finish */
 },
 NULL,					/* generate_summary */
 NULL,					/* write_summary */
 NULL,					/* read_summary */
 NULL,					/* write_optimization_summary */
 NULL,					/* read_optimization_summary */
 NULL,					/* stmt_fixup */
 0,					/* TODOs */
 NULL,					/* function_transform */
 NULL,					/* variable_transform */
};

/* lots of content here, which should *not* be matched */

struct ipa_opt_pass_d pass_ipa_cdtor_merge =
{
 {
  IPA_PASS,
  "cdtor",				/* name */
  OPTGROUP_NONE,                        /* optinfo_flags */
  gate_ipa_cdtor_merge,			/* gate */
  ipa_cdtor_merge,		        /* execute */
  NULL,					/* sub */
  NULL,					/* next */
  0,					/* static_pass_number */
  TV_CGRAPHOPT,			        /* tv_id */
  0,	                                /* properties_required */
  0,					/* properties_provided */
  0,					/* properties_destroyed */
  0,					/* todo_flags_start */
  0                                     /* todo_flags_finish */
 },
 NULL,				        /* generate_summary */
 NULL,					/* write_summary */
 NULL,					/* read_summary */
 NULL,					/* write_optimization_summary */
 NULL,					/* read_optimization_summary */
 NULL,					/* stmt_fixup */
 0,					/* TODOs */
 NULL,			                /* function_transform */
 NULL					/* variable_transform */
};
"""
        expected_code = """
class pass_ipa_whole_program_visibility : public ipa_opt_pass_d
{
public:
  pass_ipa_whole_program_visibility(context &ctxt)
    : ipa_opt_pass_d(ctxt,
\t\t     "whole-program",
\t\t     OPTGROUP_NONE,
\t\t     TV_CGRAPHOPT,
\t\t     pass_properties(required(0),
\t\t\t\t     provided(0),
\t\t\t\t     destroyed(0)),
\t\t     pass_todo_flags(start(0),
\t\t\t\t     finish(TODO_remove_functions | TODO_dump_symtab | TODO_ggc_collect)),
\t\t     0) /* function_transform_todo_flags_start */
  {}

  /* opt_pass methods: */
  bool has_gate () { return true; }
  bool gate () {
    return gate_whole_program_function_and_variable_visibility ();
  }

  bool has_execute () { return true; }
  unsigned int impl_execute () {
    return whole_program_function_and_variable_visibility ();
  }

  /* ipa_opt_pass_d methods: */
  bool has_generate_summary () { return false; }
  void impl_generate_summary () { }

  bool has_write_summary () { return false; }
  void impl_write_summary () { }

  bool has_read_summary () { return false; }
  void impl_read_summary () { }

  bool has_write_optimization_summary () { return false; }
  void impl_write_optimization_summary () { }

  bool has_read_optimization_summary () { return false; }
  void impl_read_optimization_summary () { }

  bool has_stmt_fixup () { return false; }
  void impl_stmt_fixup (struct cgraph_node *, gimple *) { }

  bool has_function_transform () { return false; }
  unsigned int impl_function_transform (struct cgraph_node *) { return 0; }

  bool has_variable_transform () { return false; }
  void impl_variable_transform (struct varpool_node *) { }

}; // class pass_ipa_whole_program_visibility

ipa_opt_pass_d *
make_pass_ipa_whole_program_visibility (context &ctxt)
{
  return new pass_ipa_whole_program_visibility (ctxt);
}

/* lots of content here, which should *not* be matched */

class pass_ipa_cdtor_merge : public ipa_opt_pass_d
{
public:
  pass_ipa_cdtor_merge(context &ctxt)
    : ipa_opt_pass_d(ctxt,
\t\t     "cdtor",
\t\t     OPTGROUP_NONE,
\t\t     TV_CGRAPHOPT,
\t\t     pass_properties(required(0),
\t\t\t\t     provided(0),
\t\t\t\t     destroyed(0)),
\t\t     pass_todo_flags(start(0),
\t\t\t\t     finish(0)),
\t\t     0) /* function_transform_todo_flags_start */
  {}

  /* opt_pass methods: */
  bool has_gate () { return true; }
  bool gate () { return gate_ipa_cdtor_merge (); }

  bool has_execute () { return true; }
  unsigned int impl_execute () { return ipa_cdtor_merge (); }

  /* ipa_opt_pass_d methods: */
  bool has_generate_summary () { return false; }
  void impl_generate_summary () { }

  bool has_write_summary () { return false; }
  void impl_write_summary () { }

  bool has_read_summary () { return false; }
  void impl_read_summary () { }

  bool has_write_optimization_summary () { return false; }
  void impl_write_optimization_summary () { }

  bool has_read_optimization_summary () { return false; }
  void impl_read_optimization_summary () { }

  bool has_stmt_fixup () { return false; }
  void impl_stmt_fixup (struct cgraph_node *, gimple *) { }

  bool has_function_transform () { return false; }
  unsigned int impl_function_transform (struct cgraph_node *) { return 0; }

  bool has_variable_transform () { return false; }
  void impl_variable_transform (struct varpool_node *) { }

}; // class pass_ipa_cdtor_merge

ipa_opt_pass_d *
make_pass_ipa_cdtor_merge (context &ctxt)
{
  return new pass_ipa_cdtor_merge (ctxt);
}
"""
        expected_changelog = \
            ('\t* ipa.c (struct ipa_opt_pass_d pass_ipa_whole_program_visibility):\n'
             '\tConvert from a global struct to a subclass of ipa_opt_pass_d.\n'
             '\t(make_pass_ipa_whole_program_visibility): New function to create an\n'
             '\tinstance of the new class pass_ipa_whole_program_visibility.\n'
             '\t(struct ipa_opt_pass_d pass_ipa_cdtor_merge): Convert from a global\n'
             '\tstruct to a subclass of ipa_opt_pass_d.\n'
             '\t(make_pass_ipa_cdtor_merge): New function to create an instance of the\n'
             '\tnew class pass_ipa_cdtor_merge.\n')

        self.assertRefactoringEquals(src, 'ipa.c',
                                     expected_code, expected_changelog)

    def test_pass_all_optimizations_g(self):
        # Example of a pass with a NULL execute
        # and a "static" qualifier:
        src = r"""
static struct gimple_opt_pass pass_all_optimizations_g =
{
 {
  GIMPLE_PASS,
  "*all_optimizations_g",		/* name */
  OPTGROUP_NONE,                        /* optinfo_flags */
  gate_all_optimizations_g,		/* gate */
  NULL,					/* execute */
  NULL,					/* sub */
  NULL,					/* next */
  0,					/* static_pass_number */
  TV_OPTIMIZE,				/* tv_id */
  0,					/* properties_required */
  0,					/* properties_provided */
  0,					/* properties_destroyed */
  0,					/* todo_flags_start */
  0					/* todo_flags_finish */
 }
};
"""
        expected_code = """
class pass_all_optimizations_g : public gimple_opt_pass
{
public:
  pass_all_optimizations_g(context &ctxt)
    : gimple_opt_pass(ctxt,
\t\t      "*all_optimizations_g",
\t\t      OPTGROUP_NONE,
\t\t      TV_OPTIMIZE,
\t\t      pass_properties(required(0),
\t\t\t\t      provided(0),
\t\t\t\t      destroyed(0)),
\t\t      pass_todo_flags(start(0),
\t\t\t\t      finish(0)))
  {}

  /* opt_pass methods: */
  bool has_gate () { return true; }
  bool gate () { return gate_all_optimizations_g (); }

  bool has_execute () { return false; }
  unsigned int impl_execute () { return 0; }

}; // class pass_all_optimizations_g

static gimple_opt_pass *
make_pass_all_optimizations_g (context &ctxt)
{
  return new pass_all_optimizations_g (ctxt);
}
"""
        expected_changelog = \
            ('\t* passes.c (struct gimple_opt_pass pass_all_optimizations_g): Convert\n'
             '\tfrom a global struct to a subclass of gimple_opt_pass.\n'
             '\t(make_pass_all_optimizations_g): New function to create an instance of\n'
             '\tthe new class pass_all_optimizations_g.\n')

        self.assertRefactoringEquals(src, 'passes.c',
                                     expected_code, expected_changelog)

    def test_pass_ipa_tm(self):
        # This wasn't matched due to trailing comma:
        src = r"""

struct simple_ipa_opt_pass pass_ipa_tm =
{
 {
  SIMPLE_IPA_PASS,
  "tmipa",				/* name */
  OPTGROUP_NONE,                        /* optinfo_flags */
  gate_tm,				/* gate */
  ipa_tm_execute,			/* execute */
  NULL,					/* sub */
  NULL,					/* next */
  0,					/* static_pass_number */
  TV_TRANS_MEM,				/* tv_id */
  PROP_ssa | PROP_cfg,			/* properties_required */
  0,			                /* properties_provided */
  0,					/* properties_destroyed */
  0,					/* todo_flags_start */
  0,					/* todo_flags_finish */
 },
};
"""
        expected_code = """

class pass_ipa_tm : public simple_ipa_opt_pass
{
public:
  pass_ipa_tm(context &ctxt)
    : simple_ipa_opt_pass(ctxt,
\t\t\t  "tmipa",
\t\t\t  OPTGROUP_NONE,
\t\t\t  TV_TRANS_MEM,
\t\t\t  pass_properties(required(PROP_ssa | PROP_cfg),
\t\t\t\t\t  provided(0),
\t\t\t\t\t  destroyed(0)),
\t\t\t  pass_todo_flags(start(0),
\t\t\t\t\t  finish(0)))
  {}

  /* opt_pass methods: */
  bool has_gate () { return true; }
  bool gate () { return gate_tm (); }

  bool has_execute () { return true; }
  unsigned int impl_execute () { return ipa_tm_execute (); }

}; // class pass_ipa_tm

simple_ipa_opt_pass *
make_pass_ipa_tm (context &ctxt)
{
  return new pass_ipa_tm (ctxt);
}
"""
        expected_changelog = \
            ('\t* trans-mem.c (struct simple_ipa_opt_pass pass_ipa_tm): Convert from a\n'
             '\tglobal struct to a subclass of simple_ipa_opt_pass.\n'
             '\t(make_pass_ipa_tm): New function to create an instance of the new\n'
             '\tclass pass_ipa_tm.\n')

        self.assertRefactoringEquals(src, 'trans-mem.c',
                                     expected_code, expected_changelog)

    def test_0_callback(self):
        # Ensure that 0 can be used as a synonym for NULL
        # (here within the gate callback):
        src = r"""
struct gimple_opt_pass pass_lower_complex =
{
 {
  GIMPLE_PASS,
  "cplxlower",                         /* name */
  OPTGROUP_NONE,                       /* optinfo_flags */
  0,                                   /* gate */
  tree_lower_complex,                  /* execute */
  NULL,                                        /* sub */
  NULL,                                        /* next */
  0,                                   /* static_pass_number */
  TV_NONE,                             /* tv_id */
  PROP_ssa,                            /* properties_required */
  PROP_gimple_lcx,                     /* properties_provided */
  0,                                   /* properties_destroyed */
  0,                                   /* todo_flags_start */
    TODO_ggc_collect
    | TODO_update_ssa
    | TODO_verify_stmts                        /* todo_flags_finish */
 }
};
"""
        expected_code = """
class pass_lower_complex : public gimple_opt_pass
{
public:
  pass_lower_complex(context &ctxt)
    : gimple_opt_pass(ctxt,
\t\t      "cplxlower",
\t\t      OPTGROUP_NONE,
\t\t      TV_NONE,
\t\t      pass_properties(required(PROP_ssa),
\t\t\t\t      provided(PROP_gimple_lcx),
\t\t\t\t      destroyed(0)),
\t\t      pass_todo_flags(start(0),
\t\t\t\t      finish(TODO_ggc_collect | TODO_update_ssa | TODO_verify_stmts)))
  {}

  /* opt_pass methods: */
  bool has_gate () { return false; }
  bool gate () { return true; }

  bool has_execute () { return true; }
  unsigned int impl_execute () { return tree_lower_complex (); }

}; // class pass_lower_complex

gimple_opt_pass *
make_pass_lower_complex (context &ctxt)
{
  return new pass_lower_complex (ctxt);
}
"""
        expected_changelog = \
            ('\t* tree-complex.c (struct gimple_opt_pass pass_lower_complex): Convert\n'
             '\tfrom a global struct to a subclass of gimple_opt_pass.\n'
             '\t(make_pass_lower_complex): New function to create an instance of the\n'
             '\tnew class pass_lower_complex.\n')

        self.assertRefactoringEquals(src, 'tree-complex.c',
                                     expected_code, expected_changelog)


    def test_factory_fn_decls(self):
        src = r"""
extern struct gimple_opt_pass pass_sra;
extern struct simple_ipa_opt_pass pass_ipa_lower_emutls;
extern struct ipa_opt_pass_d pass_ipa_whole_program_visibility;
extern struct rtl_opt_pass pass_cse;
"""
        expected_code = r"""
extern gimple_opt_pass *make_pass_sra (context &ctxt);
extern simple_ipa_opt_pass *make_pass_ipa_lower_emutls (context &ctxt);
extern ipa_opt_pass_d *make_pass_ipa_whole_program_visibility (context &ctxt);
extern rtl_opt_pass *make_pass_cse (context &ctxt);
"""
        expected_changelog = ('\t* tree-pass.h (struct gimple_opt_pass pass_sra): Replace declaration\n'
                              '\twith that of new function make_pass_sra.\n'
                              '\t(struct simple_ipa_opt_pass pass_ipa_lower_emutls): Replace\n'
                              '\tdeclaration with that of new function make_pass_ipa_lower_emutls.\n'
                              '\t(struct ipa_opt_pass_d pass_ipa_whole_program_visibility): Replace\n'
                              '\tdeclaration with that of new function\n'
                              '\tmake_pass_ipa_whole_program_visibility.\n'
                              '\t(struct rtl_opt_pass pass_cse): Replace declaration with that of new\n'
                              '\tfunction make_pass_cse.\n')
        self.assertRefactoringEquals(src, "tree-pass.h",
                                     expected_code, expected_changelog)

if __name__ == '__main__':
    unittest.main()
