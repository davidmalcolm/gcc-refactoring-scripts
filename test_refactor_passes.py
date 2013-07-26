import unittest

from refactor import Source
from refactor_passes import refactor_pass_initializers

class PassConversionTests(unittest.TestCase):
    def assertRefactoringEquals(self,
                                src, filename,
                                expected_code, expected_changelog):
        actual_code, actual_changelog = refactor_pass_initializers(filename, Source(src))
        self.maxDiff = 8192
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
        self.assertMultiLineEqual(expected_changelog,
                                  actual_changelog.as_text(None)[0]) # 2.7+

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

namespace {

const pass_data pass_data_jump2 =
{
  RTL_PASS, /* type */
  "jump2", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  false, /* has_gate */
  true, /* has_execute */
  TV_JUMP, /* tv_id */
  0, /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  TODO_ggc_collect, /* todo_flags_start */
  TODO_verify_rtl_sharing, /* todo_flags_finish */
};

class pass_jump2 : public rtl_opt_pass
{
public:
  pass_jump2(gcc::context *ctxt)
    : rtl_opt_pass(pass_data_jump2, ctxt)
  {}

  /* opt_pass methods: */
  unsigned int execute () { return execute_jump2 (); }

}; // class pass_jump2

} // anon namespace

rtl_opt_pass *
make_pass_jump2 (gcc::context *ctxt)
{
  return new pass_jump2 (ctxt);
}

baz qux
"""
        expected_changelog = \
            ('\t* cfgcleanup.c (pass_jump2): Convert from a global struct to a\n'
             '\tsubclass of rtl_opt_pass along with...\n'
             '\t(pass_data_jump2): ...new pass_data instance and...\n'
             '\t(make_pass_jump2): ...new function.\n')

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
namespace {

const pass_data pass_data_mudflap_1 =
{
  GIMPLE_PASS, /* type */
  "mudflap1", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  true, /* has_gate */
  true, /* has_execute */
  TV_NONE, /* tv_id */
  PROP_gimple_any, /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  0, /* todo_flags_finish */
};

class pass_mudflap_1 : public gimple_opt_pass
{
public:
  pass_mudflap_1(gcc::context *ctxt)
    : gimple_opt_pass(pass_data_mudflap_1, ctxt)
  {}

  /* opt_pass methods: */
  bool gate () { return gate_mudflap (); }
  unsigned int execute () { return execute_mudflap_function_decls (); }

}; // class pass_mudflap_1

} // anon namespace

gimple_opt_pass *
make_pass_mudflap_1 (gcc::context *ctxt)
{
  return new pass_mudflap_1 (ctxt);
}
"""
        expected_changelog = \
            ('\t* tree-mudflap.c (pass_mudflap_1): Convert from a global struct to a\n'
             '\tsubclass of gimple_opt_pass along with...\n'
             '\t(pass_data_mudflap_1): ...new pass_data instance and...\n'
             '\t(make_pass_mudflap_1): ...new function.\n')

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
namespace {

const pass_data pass_data_mudflap_2 =
{
  GIMPLE_PASS, /* type */
  "mudflap2", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  true, /* has_gate */
  true, /* has_execute */
  TV_NONE, /* tv_id */
  ( PROP_ssa | PROP_cfg | PROP_gimple_leh ), /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  ( TODO_verify_flow | TODO_verify_stmts
    | TODO_update_ssa ), /* todo_flags_finish */
};

class pass_mudflap_2 : public gimple_opt_pass
{
public:
  pass_mudflap_2(gcc::context *ctxt)
    : gimple_opt_pass(pass_data_mudflap_2, ctxt)
  {}

  /* opt_pass methods: */
  bool gate () { return gate_mudflap (); }
  unsigned int execute () { return execute_mudflap_function_ops (); }

}; // class pass_mudflap_2

} // anon namespace

gimple_opt_pass *
make_pass_mudflap_2 (gcc::context *ctxt)
{
  return new pass_mudflap_2 (ctxt);
}
"""
        expected_changelog = \
            ('\t* tree-mudflap.c (pass_mudflap_2): Convert from a global struct to a\n'
             '\tsubclass of gimple_opt_pass along with...\n'
             '\t(pass_data_mudflap_2): ...new pass_data instance and...\n'
             '\t(make_pass_mudflap_2): ...new function.\n')

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
        expected_code = """namespace {

const pass_data pass_data_ipa_pta =
{
  SIMPLE_IPA_PASS, /* type */
  "pta", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  true, /* has_gate */
  true, /* has_execute */
  TV_IPA_PTA, /* tv_id */
  0, /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  TODO_update_ssa, /* todo_flags_finish */
};

class pass_ipa_pta : public simple_ipa_opt_pass
{
public:
  pass_ipa_pta(gcc::context *ctxt)
    : simple_ipa_opt_pass(pass_data_ipa_pta, ctxt)
  {}

  /* opt_pass methods: */
  bool gate () { return gate_ipa_pta (); }
  unsigned int execute () { return ipa_pta_execute (); }

}; // class pass_ipa_pta

} // anon namespace

simple_ipa_opt_pass *
make_pass_ipa_pta (gcc::context *ctxt)
{
  return new pass_ipa_pta (ctxt);
}
"""
        expected_changelog = \
            ('\t* tree-ssa-structalias.c (pass_ipa_pta): Convert from a global struct\n'
             '\tto a subclass of simple_ipa_opt_pass along with...\n'
             '\t(pass_data_ipa_pta): ...new pass_data instance and...\n'
             '\t(make_pass_ipa_pta): ...new function.\n')

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
 ipa_prop_write_all_agg_replacement,	/*write_optimization_summary */
 ipa_prop_read_all_agg_replacement,	/* read_optimization_summary */
 NULL,			 		/* stmt_fixup */
 0,					/* TODOs */
 ipcp_transform_function,		/* function_transform */
 NULL,					/* variable_transform */
};
"""
        expected_code = """
namespace {

const pass_data pass_data_ipa_cp =
{
  IPA_PASS, /* type */
  "cp", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  true, /* has_gate */
  true, /* has_execute */
  TV_IPA_CONSTANT_PROP, /* tv_id */
  0, /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  ( TODO_dump_symtab | TODO_remove_functions
    | TODO_ggc_collect ), /* todo_flags_finish */
};

class pass_ipa_cp : public ipa_opt_pass_d
{
public:
  pass_ipa_cp(gcc::context *ctxt)
    : ipa_opt_pass_d(pass_data_ipa_cp, ctxt,
\t\t     ipcp_generate_summary, /* generate_summary */
\t\t     ipcp_write_summary, /* write_summary */
\t\t     ipcp_read_summary, /* read_summary */
\t\t     ipa_prop_write_all_agg_replacement, /*
\t\t     write_optimization_summary */
\t\t     ipa_prop_read_all_agg_replacement, /*
\t\t     read_optimization_summary */
\t\t     NULL, /* stmt_fixup */
\t\t     0, /* function_transform_todo_flags_start */
\t\t     ipcp_transform_function, /* function_transform */
\t\t     NULL) /* variable_transform */
  {}

  /* opt_pass methods: */
  bool gate () { return cgraph_gate_cp (); }
  unsigned int execute () { return ipcp_driver (); }

}; // class pass_ipa_cp

} // anon namespace

ipa_opt_pass_d *
make_pass_ipa_cp (gcc::context *ctxt)
{
  return new pass_ipa_cp (ctxt);
}
"""
        expected_changelog = \
            ('\t* ipa-cp.c (pass_ipa_cp): Convert from a global struct to a subclass\n'
             '\tof ipa_opt_pass_d along with...\n'
             '\t(pass_data_ipa_cp): ...new pass_data instance and...\n'
             '\t(make_pass_ipa_cp): ...new function.\n')

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
namespace {

const pass_data pass_data_ipa_whole_program_visibility =
{
  IPA_PASS, /* type */
  "whole-program", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  true, /* has_gate */
  true, /* has_execute */
  TV_CGRAPHOPT, /* tv_id */
  0, /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  ( TODO_remove_functions | TODO_dump_symtab
    | TODO_ggc_collect ), /* todo_flags_finish */
};

class pass_ipa_whole_program_visibility : public ipa_opt_pass_d
{
public:
  pass_ipa_whole_program_visibility(gcc::context *ctxt)
    : ipa_opt_pass_d(pass_data_ipa_whole_program_visibility, ctxt,
\t\t     NULL, /* generate_summary */
\t\t     NULL, /* write_summary */
\t\t     NULL, /* read_summary */
\t\t     NULL, /* write_optimization_summary */
\t\t     NULL, /* read_optimization_summary */
\t\t     NULL, /* stmt_fixup */
\t\t     0, /* function_transform_todo_flags_start */
\t\t     NULL, /* function_transform */
\t\t     NULL) /* variable_transform */
  {}

  /* opt_pass methods: */
  bool gate () {
    return gate_whole_program_function_and_variable_visibility ();
  }
  unsigned int execute () {
    return whole_program_function_and_variable_visibility ();
  }

}; // class pass_ipa_whole_program_visibility

} // anon namespace

ipa_opt_pass_d *
make_pass_ipa_whole_program_visibility (gcc::context *ctxt)
{
  return new pass_ipa_whole_program_visibility (ctxt);
}

/* lots of content here, which should *not* be matched */

namespace {

const pass_data pass_data_ipa_cdtor_merge =
{
  IPA_PASS, /* type */
  "cdtor", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  true, /* has_gate */
  true, /* has_execute */
  TV_CGRAPHOPT, /* tv_id */
  0, /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  0, /* todo_flags_finish */
};

class pass_ipa_cdtor_merge : public ipa_opt_pass_d
{
public:
  pass_ipa_cdtor_merge(gcc::context *ctxt)
    : ipa_opt_pass_d(pass_data_ipa_cdtor_merge, ctxt,
\t\t     NULL, /* generate_summary */
\t\t     NULL, /* write_summary */
\t\t     NULL, /* read_summary */
\t\t     NULL, /* write_optimization_summary */
\t\t     NULL, /* read_optimization_summary */
\t\t     NULL, /* stmt_fixup */
\t\t     0, /* function_transform_todo_flags_start */
\t\t     NULL, /* function_transform */
\t\t     NULL) /* variable_transform */
  {}

  /* opt_pass methods: */
  bool gate () { return gate_ipa_cdtor_merge (); }
  unsigned int execute () { return ipa_cdtor_merge (); }

}; // class pass_ipa_cdtor_merge

} // anon namespace

ipa_opt_pass_d *
make_pass_ipa_cdtor_merge (gcc::context *ctxt)
{
  return new pass_ipa_cdtor_merge (ctxt);
}
"""
        expected_changelog = \
            ('\t* ipa.c (pass_ipa_whole_program_visibility): Convert from a global\n'
             '\tstruct to a subclass of ipa_opt_pass_d along with...\n'
             '\t(pass_data_ipa_whole_program_visibility): ...new pass_data instance\n'
             '\tand...\n'
             '\t(make_pass_ipa_whole_program_visibility): ...new function.\n'
             '\t(pass_ipa_cdtor_merge): Convert from a global struct to a subclass of\n'
             '\tipa_opt_pass_d along with...\n'
             '\t(pass_data_ipa_cdtor_merge): ...new pass_data instance and...\n'
             '\t(make_pass_ipa_cdtor_merge): ...new function.\n')

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
namespace {

const pass_data pass_data_all_optimizations_g =
{
  GIMPLE_PASS, /* type */
  "*all_optimizations_g", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  true, /* has_gate */
  false, /* has_execute */
  TV_OPTIMIZE, /* tv_id */
  0, /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  0, /* todo_flags_finish */
};

class pass_all_optimizations_g : public gimple_opt_pass
{
public:
  pass_all_optimizations_g(gcc::context *ctxt)
    : gimple_opt_pass(pass_data_all_optimizations_g, ctxt)
  {}

  /* opt_pass methods: */
  bool gate () { return gate_all_optimizations_g (); }

}; // class pass_all_optimizations_g

} // anon namespace

static gimple_opt_pass *
make_pass_all_optimizations_g (gcc::context *ctxt)
{
  return new pass_all_optimizations_g (ctxt);
}
"""
        expected_changelog = \
            ('\t* passes.c (pass_all_optimizations_g): Convert from a global struct to\n'
             '\ta subclass of gimple_opt_pass along with...\n'
             '\t(pass_data_all_optimizations_g): ...new pass_data instance and...\n'
             '\t(make_pass_all_optimizations_g): ...new function.\n')

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

namespace {

const pass_data pass_data_ipa_tm =
{
  SIMPLE_IPA_PASS, /* type */
  "tmipa", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  true, /* has_gate */
  true, /* has_execute */
  TV_TRANS_MEM, /* tv_id */
  ( PROP_ssa | PROP_cfg ), /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  0, /* todo_flags_finish */
};

class pass_ipa_tm : public simple_ipa_opt_pass
{
public:
  pass_ipa_tm(gcc::context *ctxt)
    : simple_ipa_opt_pass(pass_data_ipa_tm, ctxt)
  {}

  /* opt_pass methods: */
  bool gate () { return gate_tm (); }
  unsigned int execute () { return ipa_tm_execute (); }

}; // class pass_ipa_tm

} // anon namespace

simple_ipa_opt_pass *
make_pass_ipa_tm (gcc::context *ctxt)
{
  return new pass_ipa_tm (ctxt);
}
"""
        expected_changelog = \
            ('\t* trans-mem.c (pass_ipa_tm): Convert from a global struct to a\n'
             '\tsubclass of simple_ipa_opt_pass along with...\n'
             '\t(pass_data_ipa_tm): ...new pass_data instance and...\n'
             '\t(make_pass_ipa_tm): ...new function.\n')

        self.assertRefactoringEquals(src, 'trans-mem.c',
                                     expected_code, expected_changelog)

    def test_0_callback(self):
        # Ensure that 0 can be used as a synonym for NULL
        # (here within the gate callback).
        # This is also a multi-instance pass, and thus
        # needs a clone method.
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
namespace {

const pass_data pass_data_lower_complex =
{
  GIMPLE_PASS, /* type */
  "cplxlower", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  false, /* has_gate */
  true, /* has_execute */
  TV_NONE, /* tv_id */
  PROP_ssa, /* properties_required */
  PROP_gimple_lcx, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  ( TODO_ggc_collect | TODO_update_ssa
    | TODO_verify_stmts ), /* todo_flags_finish */
};

class pass_lower_complex : public gimple_opt_pass
{
public:
  pass_lower_complex(gcc::context *ctxt)
    : gimple_opt_pass(pass_data_lower_complex, ctxt)
  {}

  /* opt_pass methods: */
  opt_pass * clone () { return new pass_lower_complex (ctxt_); }
  unsigned int execute () { return tree_lower_complex (); }

}; // class pass_lower_complex

} // anon namespace

gimple_opt_pass *
make_pass_lower_complex (gcc::context *ctxt)
{
  return new pass_lower_complex (ctxt);
}
"""
        expected_changelog = \
            ('\t* tree-complex.c (pass_lower_complex): Convert from a global struct to\n'
             '\ta subclass of gimple_opt_pass along with...\n'
             '\t(pass_data_lower_complex): ...new pass_data instance and...\n'
             '\t(make_pass_lower_complex): ...new function.\n')

        self.assertRefactoringEquals(src, 'tree-complex.c',
                                     expected_code, expected_changelog)


    def test_factory_fn_decls(self):
        src = r"""
extern struct gimple_opt_pass pass_sra;
extern struct simple_ipa_opt_pass pass_ipa_lower_emutls;
extern struct ipa_opt_pass_d pass_ipa_whole_program_visibility;
extern struct rtl_opt_pass pass_cse;
"""
        expected_code = """
extern gimple_opt_pass *make_pass_sra (gcc::context *ctxt);
extern simple_ipa_opt_pass *make_pass_ipa_lower_emutls (gcc::context *ctxt);
extern ipa_opt_pass_d *make_pass_ipa_whole_program_visibility (gcc::context
\t\t\t\t\t\t\t       *ctxt);
extern rtl_opt_pass *make_pass_cse (gcc::context *ctxt);
"""
        expected_changelog = ('\t* tree-pass.h (pass_sra): Replace declaration with that of...\n'
                              '\t(make_pass_sra): ...new function.\n'
                              '\t(pass_ipa_lower_emutls): Replace declaration with that of...\n'
                              '\t(make_pass_ipa_lower_emutls): ...new function.\n'
                              '\t(pass_ipa_whole_program_visibility): Replace declaration with that\n'
                              '\tof...\n'
                              '\t(make_pass_ipa_whole_program_visibility): ...new function.\n'
                              '\t(pass_cse): Replace declaration with that of...\n'
                              '\t(make_pass_cse): ...new function.\n')
        self.assertRefactoringEquals(src, "tree-pass.h",
                                     expected_code, expected_changelog)

if __name__ == '__main__':
    unittest.main()

