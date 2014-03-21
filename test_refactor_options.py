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

class OptionTests(TestParsingTests):
    def test_find_opt_files(self):
        paths = find_opt_files('../src/gcc')
        self.assertIn('../src/gcc/common.opt', paths)
        self.assertIn('../src/gcc/c-family/c.opt', paths)
        self.assertIn('../src/gcc/config/microblaze/microblaze.opt', paths)

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

options = Options()

class IntegrationTests(unittest.TestCase):
    def assertRefactoredCodeEquals(self,
                                   src, filename,
                                   expected_code):
        actual_code, actual_changelog = \
            options.make_macros_visible(filename, Source(src))
        self.maxDiff = 32768
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
    def assertRefactoringEquals(self,
                                src, filename,
                                expected_code, expected_changelog):
        actual_code, actual_changelog = \
            options.make_macros_visible(filename, Source(src))
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


if __name__ == '__main__':
    unittest.main()
