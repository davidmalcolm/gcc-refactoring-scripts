import unittest

from refactor import wrap, Source
from refactor_options import Options, parse_record, \
    Variable, Option, find_opt_files

def make_expected_changelog(filename, scope, text):
    return wrap('\t* %s (%s): %s' % (filename, scope, text))

class TestParsingTests(unittest.TestCase):
    def assertParsesAs(self, lines, expected):
        self.assertEqual(parse_record(lines), expected)

class VariableTests(TestParsingTests):
    def test_simple(self):
        self.assertParsesAs(['Variable',
                             'int optimize'],
                            Variable('int', 'optimize'))

    def test_initializer(self):
        self.assertParsesAs(['Variable',
                             'int flag_complex_method = 1'],
                            Variable('int', 'flag_complex_method'))

    def test_pointer(self):
        self.assertParsesAs(['Variable',
                             'void *flag_instrument_functions_exclude_functions'],
                            Variable('void *',
                                     'flag_instrument_functions_exclude_functions'))

    def test_enum_with_initializer(self):
        self.assertParsesAs(['Variable',
                            'enum debug_struct_file debug_struct_generic[DINFO_USAGE_NUM_ENUMS] = { DINFO_STRUCT_FILE_ANY, DINFO_STRUCT_FILE_ANY, DINFO_STRUCT_FILE_ANY }'],
                            Variable('enum debug_struct_file',
                                     'debug_struct_generic'))

    def test_ix86_isa_flags(self):
        self.assertParsesAs(['Variable',
                             'HOST_WIDE_INT ix86_isa_flags = TARGET_64BIT_DEFAULT | TARGET_SUBTARGET_ISA_DEFAULT'],
                            Variable('HOST_WIDE_INT',
                                     'ix86_isa_flags'))

    def test_target_variable(self):
        self.assertParsesAs(['TargetVariable',
                             'int recip_mask = RECIP_MASK_DEFAULT'],
                            Variable('int',
                                     'recip_mask'))

class OptionTests(TestParsingTests):
    def test_find_opt_files(self):
        paths = find_opt_files('../src/gcc')
        self.assertIn('../src/gcc/common.opt', paths)
        self.assertIn('../src/gcc/c-family/c.opt', paths)
        self.assertIn('../src/gcc/config/microblaze/microblaze.opt', paths)
        self.assertIn('../src/gcc/config/i386/i386.opt', paths)

    def test_split_into_properties(self):
        for line, expected_props in [
                ('Common Report Var(flag_tree_builtin_call_dce) Init(0) Optimization',
                 ['Common', 'Report', 'Var(flag_tree_builtin_call_dce)',
                  'Init(0)', 'Optimization']),
                ('C ObjC C++ ObjC++ Var(flag_no_builtin, 0)',
                 ['C', 'ObjC', 'C++', 'ObjC++', 'Var(flag_no_builtin, 0)']),
                ('Name(tls_model) Type(enum tls_model) UnknownError(unknown TLS model %qs)',
                 ['Name(tls_model)', 'Type(enum tls_model)', 'UnknownError(unknown TLS model %qs)'])
        ]:
            self.assertEqual(Option.split_into_properties(line),
                             expected_props)

    def test_simple(self):
        self.assertParsesAs(
            ['ftree-vrp',
             'Common Report Var(flag_tree_vrp) Init(0) Optimization',
             'Perform Value Range Propagation on trees'],
            Option(name='ftree-vrp',
                   availability='Common',
                   kind='Optimization',
                   driver=False,
                   report=True,
                   var='flag_tree_vrp',
                   init='0',
                   helptext='Perform Value Range Propagation on trees'))

    def test_var_with_two_args(self):
        self.assertParsesAs(
            ['fcommon',
             'Common Report Var(flag_no_common,0) Optimization',
             'Do not put uninitialized globals in the common section'],
            Option(name='fcommon',
                   availability='Common',
                   kind='Optimization',
                   driver=False,
                   report=True,
                   var='flag_no_common',
                   init=None,
                   helptext='Do not put uninitialized globals in the common section'))

    def test_flag_no_builtin(self):
        opt = parse_record(['fbuiltin',
                            'C ObjC C++ ObjC++ Var(flag_no_builtin, 0)'
                            'Recognize built-in functions'])
        self.assertEqual(opt.var, 'flag_no_builtin')

    def test_wformat(self):
        opt = parse_record(['Wformat=',
                            'C ObjC C++ ObjC++ Joined RejectNegative UInteger Var(warn_format) Warning LangEnabledBy(C ObjC C++ ObjC++,Wall, 1, 0)\n'
                            'Warn about printf/scanf/strftime/strfmon format string anomalies\n'])
        self.assertEqual(opt.var, 'warn_format')

options = Options()

class IntegrationTests(unittest.TestCase):
    def assertRefactoredCodeEquals(self,
                                   src, filename,
                                   expected_code):
        actual_code, actual_changelog = \
            options.make_macros_visible(filename, Source(src, filename))
        self.maxDiff = 32768
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
    def assertRefactoringEquals(self,
                                src, filename,
                                expected_code, expected_changelog):
        actual_code, actual_changelog = \
            options.make_macros_visible(filename, Source(src, filename))
        self.maxDiff = 8192
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
        self.assertMultiLineEqual(expected_changelog,
                                  actual_changelog.as_text(None)[0]) # 2.7+
    def assertUnchanged(self, src, filename):
        self.assertRefactoringEquals(src, filename, src, '')

    def test_simple(self):
        src = (
            'static\n'
            'gate_vrp (void)\n'
            '{\n'
            '  return flag_tree_vrp != 0;\n'
            '}\n')
        expected_code = (
            'static\n'
            'gate_vrp (void)\n'
            '{\n'
            '  return GCC_OPTION (flag_tree_vrp) != 0;\n'
            '}\n')
        expected_changelog = \
            ('\t* tree-vrp.c (gate_vrp): Wrap option usage in GCC_OPTION macro.\n')
        self.assertRefactoringEquals(src, 'tree-vrp.c',
                                     expected_code, expected_changelog)

    def test_idempotency(self):
        src = (
            'static\n'
            'gate_vrp (void)\n'
            '{\n'
            '  return GCC_OPTION (flag_tree_vrp) != 0;\n'
            '}\n')
        self.assertUnchanged(src, 'tree-vrp.c')

    def test_trailing(self):
        src = (
            '   /* True if pedwarns are errors.  */\n'
            '   bool pedantic_errors;\n')
        self.assertUnchanged(src, 'diagnostic.h')

    def test_within_GENERATOR_FILE(self):
        # A couple of vars in print-rtl.c are wrapped within
        #   #ifdef GENERATOR_FILE
        # and must not be changed.
        src = ('int flag_dump_unnumbered = 0;\n')
        self.assertUnchanged(src, 'print-rtl.h')

    def test_optimize(self):
        # Ensure that "optimize" gets wrapped
        src = (
            'static bool\n'
            'gate_dse1 (void)\n'
            '{\n'
            '  return optimize > 0 && flag_dse\n'
            '    && dbg_cnt (dse1);\n'
            '}\n'
            '\n'
            'static bool\n'
            'gate_dse2 (void)\n'
            '{\n'
            '  return optimize > 0 && flag_dse\n'
            '    && dbg_cnt (dse2);\n'
            '}\n')
        expected_code = (
            'static bool\n'
            'gate_dse1 (void)\n'
            '{\n'
            '  return GCC_OPTION (optimize) > 0 && GCC_OPTION (flag_dse)\n'
            '    && dbg_cnt (dse1);\n'
            '}\n'
            '\n'
            'static bool\n'
            'gate_dse2 (void)\n'
            '{\n'
            '  return GCC_OPTION (optimize) > 0 && GCC_OPTION (flag_dse)\n'
            '    && dbg_cnt (dse2);\n'
            '}\n')
        expected_changelog = \
            ('\t* dse.c (gate_dse1): Wrap option usage in GCC_OPTION macro.\n'
             '\t(gate_dse2): Likewise.\n')
        self.assertRefactoringEquals(src, 'dse.c',
                                     expected_code, expected_changelog)

    def test_cpp_comment(self):
        src = (
            '  // The next optimize flag.  These are not in any order.\n'
            '  Go_optimize* next_;\n')
        self.assertUnchanged(src, 'go/gofrontend/go-optimize.h')

    def test_md_comment(self):
        # Don't touch the "optimize" within machine description comments
        src = (
            '; GAS relies on the order and position of instructions output below in order\n'
            '; to generate relocs for VMS link to potentially optimize the call.\n')
        self.assertUnchanged(src, 'config/alpha/alpha.md')

    def test_multiple_options(self):
        src = (
            'gate_handle_reorder_blocks (void)\n' # excerpt
            '{\n'
            '  return (optimize > 0\n'
            '          && (flag_reorder_blocks || flag_reorder_blocks_and_partition));\n'
            '}\n')
        expected_code = (
            'gate_handle_reorder_blocks (void)\n'
            '{\n'
            '  return (GCC_OPTION (optimize) > 0\n'
            '          && (GCC_OPTION (flag_reorder_blocks) || GCC_OPTION (flag_reorder_blocks_and_partition)));\n'
            '}\n')
        expected_changelog = \
            ('\t* bb-reorder.c (gate_handle_reorder_blocks): Wrap option usage in\n'
             '\tGCC_OPTION macro.\n')
        self.assertRefactoringEquals(src, 'bb-reorder.c',
                                     expected_code, expected_changelog)

    def test_opt_for_fn(self):
        src = (
            'static void\n'
            'determine_versionability (struct cgraph_node *node)\n'
            '{\n'
            # (excerpt)
            '  else if (!opt_for_fn (node->decl, optimize)\n'
            '\t   || !opt_for_fn (node->decl, flag_ipa_cp))\n'
            '    reason = "non-optimized function";\n')
        self.assertUnchanged(src, 'ipa-cp.c')

    def test_escaped_quote(self):
        # Ensure that Source.within_string_literal_at can cope with escaped
        # quotes
        s = Source('foo \\"bar')
        self.assert_(not s.within_string_literal_at(9))

    def test_literal_quote(self):
        s = Source("'\"' foo")
        self.assert_(not s.within_string_literal_at(5))

        s = Source('foo "*w\'" bar')
        self.assert_(not s.within_string_literal_at(12))

        s = Source('Look for range tests like "'
                   + "ch >= '0' && ch <= '9'"
                   +'".')
        self.assert_(not s.within_string_literal_at(1000))

    def test_quote_within_comment(self):
        s = Source('/*"*/ foo ')
        self.assert_(not s.within_string_literal_at(20))

    def test_spec_strings(self):
        # Must not touch the "pedantic" in the following:
        src = (
            'static const char *cpp_options =\n'
            '"%(cpp_unique_options) %1 %{m*} %{std*&ansi&trigraphs} %{W*&pedantic*} %{w}\\n'
            ' %{f*} %{g*:%{!g0:%{g*} %{!fno-working-directory:-fworking-directory}}} %{O*}\\n'
            ' %{undef} %{save-temps*:-fpch-preprocess}";\n')
        self.assertUnchanged(src, 'gcc.c')

    def test_macro(self):
        src = ('#if TARGET_ABI_OPEN_VMS == 0\n'
               '#define flag_vms_malloc64 0\n'
               '#endif\n')
        self.assertUnchanged(src, 'gcc/ada/gcc-interface/gigi.h')

    def test_attributes(self):
        src = ('void __gnat_sigtramp (int signo, void *si, void *sc,\n'
               '                      sighandler_t * handler)\n'
               '                      __attribute__((optimize(2)));\n')
        self.assertUnchanged(src, 'gcc/ada/sigtramp-armvxw.c')

    def test_ada_misc_c(self):
        src = ('int flag_short_enums;\n'
               'enum stack_check_type flag_stack_check = NO_STACK_CHECK;\n')
        self.assertUnchanged(src, 'gcc-interface/misc.c')

    def test_md_changelog(self):
        src = (
            '\n'
            '(define_insn "*recipsf2"\n'
            '  [(set (match_operand:SF 0 "register_operand" "=f")\n'
            '	(div:SF (match_operand:SF 1 "const_float_1_operand" "")\n'
            '		(match_operand:SF 2 "register_operand" "f")))]\n'
            '  "TARGET_HARD_FLOAT_RECIP && flag_unsafe_math_optimizations"\n'
            '  "recip.s\t%0, %2"\n'
            '  [(set_attr "type"	"fdiv")\n'
            '   (set_attr "mode"	"SF")\n'
            '   (set_attr "length"	"3")])\n')
        expected_code = (
            '\n'
            '(define_insn "*recipsf2"\n'
            '  [(set (match_operand:SF 0 "register_operand" "=f")\n'
            '	(div:SF (match_operand:SF 1 "const_float_1_operand" "")\n'
            '		(match_operand:SF 2 "register_operand" "f")))]\n'
            '  "TARGET_HARD_FLOAT_RECIP && GCC_OPTION (flag_unsafe_math_optimizations)"\n'
            '  "recip.s\t%0, %2"\n'
            '  [(set_attr "type"	"fdiv")\n'
            '   (set_attr "mode"	"SF")\n'
            '   (set_attr "length"	"3")])\n')
        expected_changelog = (
            '\t* gcc/config/xtensa/xtensa.md (*recipsf2): Wrap option usage in\n'
            '\tGCC_OPTION macro.\n')
        self.assertRefactoringEquals(src, 'gcc/config/xtensa/xtensa.md',
                                     expected_code, expected_changelog)

    def test_md_changelog_if(self):
        src = (
            ';; Return 1 if OP is a SYMBOL_REF for which we can make a call via bsr.\n'
            '(define_predicate "direct_call_operand"\n'
            '  (match_operand 0 "samegp_function_operand")\n'
            '{\n'
            '  /* If profiling is implemented via linker tricks, we can\'t jump\n'
            '     to the nogp alternate entry point.  Note that crtl->profile\n'
            '     would not be correct, since that doesn\'t indicate if the target\n'
            '     function uses profiling.  */\n'
            '  /* ??? TARGET_PROFILING_NEEDS_GP isn\'t really the right test,\n'
            '     but is approximately correct for the OSF ABIs.  Don\'t know\n'
            '     what to do for VMS, NT, or UMK.  */\n'
            '  if (!TARGET_PROFILING_NEEDS_GP && profile_flag)\n'
            '    return false;\n')
        expected_code = (
            ';; Return 1 if OP is a SYMBOL_REF for which we can make a call via bsr.\n'
            '(define_predicate "direct_call_operand"\n'
            '  (match_operand 0 "samegp_function_operand")\n'
            '{\n'
            '  /* If profiling is implemented via linker tricks, we can\'t jump\n'
            '     to the nogp alternate entry point.  Note that crtl->profile\n'
            '     would not be correct, since that doesn\'t indicate if the target\n'
            '     function uses profiling.  */\n'
            '  /* ??? TARGET_PROFILING_NEEDS_GP isn\'t really the right test,\n'
            '     but is approximately correct for the OSF ABIs.  Don\'t know\n'
            '     what to do for VMS, NT, or UMK.  */\n'
            '  if (!TARGET_PROFILING_NEEDS_GP && GCC_OPTION (profile_flag))\n'
            '    return false;\n')
        expected_changelog = (
            '\t* gcc/config/alpha/predicates.md (direct_call_operand): Wrap option\n'
            '\tusage in GCC_OPTION macro.\n')
        self.assertRefactoringEquals(src, 'gcc/config/alpha/predicates.md',
                                     expected_code, expected_changelog)





if __name__ == '__main__':
    unittest.main()
