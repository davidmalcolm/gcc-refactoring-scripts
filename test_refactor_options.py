import unittest

from refactor import wrap, Source
from refactor_options import make_macros_visible, parse_record, \
    Variable, Option

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

class IntegrationTests(unittest.TestCase):
    def assertRefactoredCodeEquals(self,
                                   src, filename,
                                   expected_code):
        actual_code, actual_changelog = make_macros_visible(filename, Source(src))
        self.maxDiff = 32768
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
    def assertRefactoringEquals(self,
                                src, filename,
                                expected_code, expected_changelog):
        actual_code, actual_changelog = make_macros_visible(filename, Source(src))
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

if __name__ == '__main__':
    unittest.main()
