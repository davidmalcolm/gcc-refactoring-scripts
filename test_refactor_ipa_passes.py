import unittest

from refactor import Source
from refactor_ipa_passes import refactor_ipa_passes

class IpaPassConversionTests(unittest.TestCase):
    def assertRefactoringEquals(self,
                                src, filename,
                                expected_code, expected_changelog):
        actual_code, actual_changelog = refactor_ipa_passes(filename, Source(src))
        self.maxDiff = 8192
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
        self.assertMultiLineEqual(expected_changelog,
                                  actual_changelog.as_text(None)[0]) # 2.7+

    def test_ipa_reference(self):
        src = """
namespace {

const pass_data pass_data_ipa_reference =
{
  IPA_PASS, /* type */
  "static-var", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  true, /* has_gate */
  true, /* has_execute */
  TV_IPA_REFERENCE, /* tv_id */
  0, /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  0, /* todo_flags_finish */
};

class pass_ipa_reference : public ipa_opt_pass_d
{
public:
  pass_ipa_reference(gcc::context *ctxt)
    : ipa_opt_pass_d(pass_data_ipa_reference, ctxt,
\t\t     NULL, /* generate_summary */
\t\t     NULL, /* write_summary */
\t\t     NULL, /* read_summary */
\t\t     ipa_reference_write_optimization_summary, /*
\t\t     write_optimization_summary */
\t\t     ipa_reference_read_optimization_summary, /*
\t\t     read_optimization_summary */
\t\t     NULL, /* stmt_fixup */
\t\t     0, /* function_transform_todo_flags_start */
\t\t     NULL, /* function_transform */
\t\t     NULL) /* variable_transform */
  {}

  /* opt_pass methods: */
  bool gate () { return gate_reference (); }
  unsigned int execute () { return propagate (); }

}; // class pass_ipa_reference

} // anon namespace
"""
        expected_code = """
namespace {

const pass_data pass_data_ipa_reference =
{
  IPA_PASS, /* type */
  "static-var", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  true, /* has_gate */
  true, /* has_execute */
  TV_IPA_REFERENCE, /* tv_id */
  0, /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  0, /* todo_flags_finish */
};

const ipa_pass_data ipa_pass_data_ipa_reference =
{
  false, /* has_generate_summary */
  false, /* has_write_summary */
  false, /* has_read_summary */
  true, /* has_write_optimization_summary */
  true, /* has_read_optimization_summary */
  false, /* has_stmt_fixup */
  0, /* function_transform_todo_flags_start */
  false, /* has_function_transform */
  false /* has_variable_transform */
};

class pass_ipa_reference : public ipa_opt_pass_d
{
public:
  pass_ipa_reference(gcc::context *ctxt)
    : ipa_opt_pass_d(pass_data_ipa_reference, ctxt,
\t\t     ipa_pass_data_ipa_reference)
  {}

  /* opt_pass methods: */
  bool gate () { return gate_reference (); }
  unsigned int execute () { return propagate (); }

  /* ipa_opt_pass_d methods: */
  void write_optimization_summary (void)
  {
    ipa_reference_write_optimization_summary ();
  }

  void read_optimization_summary (void)
  {
    ipa_reference_read_optimization_summary ();
  }

}; // class pass_ipa_reference

} // anon namespace
"""
        expected_changelog = \
            ('\t* ipa-reference.c (pass_ipa_reference): Convert to new API for IPA\n'
             '\tpasses.\n')

        self.assertRefactoringEquals(src, 'ipa-reference.c',
                                     expected_code, expected_changelog)

    def test_ipa_pure_const(self):
        src = (
"""
namespace {

const pass_data pass_data_ipa_pure_const =
{
  IPA_PASS, /* type */
  "pure-const", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  true, /* has_gate */
  true, /* has_execute */
  TV_IPA_PURE_CONST, /* tv_id */
  0, /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  0, /* todo_flags_finish */
};

class pass_ipa_pure_const : public ipa_opt_pass_d
{
public:
  pass_ipa_pure_const(gcc::context *ctxt)
    : ipa_opt_pass_d(pass_data_ipa_pure_const, ctxt,
\t\t     pure_const_generate_summary, /* generate_summary */
\t\t     pure_const_write_summary, /* write_summary */
\t\t     pure_const_read_summary, /* read_summary */
\t\t     NULL, /* write_optimization_summary */
\t\t     NULL, /* read_optimization_summary */
\t\t     NULL, /* stmt_fixup */
\t\t     0, /* function_transform_todo_flags_start */
\t\t     NULL, /* function_transform */
\t\t     NULL) /* variable_transform */
  {}

  /* opt_pass methods: */
  bool gate () { return gate_pure_const (); }
  unsigned int execute () { return propagate (); }

}; // class pass_ipa_pure_const

} // anon namespace
""")
        expected_code = (
"""
namespace {

const pass_data pass_data_ipa_pure_const =
{
  IPA_PASS, /* type */
  "pure-const", /* name */
  OPTGROUP_NONE, /* optinfo_flags */
  true, /* has_gate */
  true, /* has_execute */
  TV_IPA_PURE_CONST, /* tv_id */
  0, /* properties_required */
  0, /* properties_provided */
  0, /* properties_destroyed */
  0, /* todo_flags_start */
  0, /* todo_flags_finish */
};

const ipa_pass_data ipa_pass_data_ipa_pure_const =
{
  true, /* has_generate_summary */
  true, /* has_write_summary */
  true, /* has_read_summary */
  false, /* has_write_optimization_summary */
  false, /* has_read_optimization_summary */
  false, /* has_stmt_fixup */
  0, /* function_transform_todo_flags_start */
  false, /* has_function_transform */
  false /* has_variable_transform */
};

class pass_ipa_pure_const : public ipa_opt_pass_d
{
public:
  pass_ipa_pure_const(gcc::context *ctxt)
    : ipa_opt_pass_d(pass_data_ipa_pure_const, ctxt,
\t\t     ipa_pass_data_ipa_pure_const)
  {}

  /* opt_pass methods: */
  bool gate () { return gate_pure_const (); }
  unsigned int execute () { return propagate (); }

  /* ipa_opt_pass_d methods: */
  void generate_summary (void)
  {
    pure_const_generate_summary ();
  }

  void write_summary (void)
  {
    pure_const_write_summary ();
  }

  void read_summary (void)
  {
    pure_const_read_summary ();
  }

}; // class pass_ipa_pure_const

} // anon namespace
""")
        expected_changelog = \
            ('\t* ipa-pure-const.c (pass_ipa_pure_const): Convert to new API for IPA\n'
             '\tpasses.\n')

        self.assertRefactoringEquals(src, 'ipa-pure-const.c',
                                     expected_code, expected_changelog)

if __name__ == '__main__':
    unittest.main()

