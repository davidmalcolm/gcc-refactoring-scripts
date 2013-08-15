import unittest

from refactor import wrap, Source
from refactor_options import make_macros_visible

def make_expected_changelog(filename, scope, text):
    return wrap('\t* %s (%s): %s' % (filename, scope, text))

class Tests(unittest.TestCase):
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
