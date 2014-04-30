import unittest

from refactor import wrap, Source
from rename_gimple import rename_types

def make_expected_changelog(filename, scope, text):
    return wrap('\t* %s (%s): %s' % (filename, scope, text))

class Tests(unittest.TestCase):
    def assertRefactoredCodeEquals(self,
                                   src, filename,
                                   expected_code):
        actual_code, actual_changelog = rename_types(filename, Source(src))
        self.maxDiff = 32768
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
    def assertRefactoringEquals(self,
                                src, filename,
                                expected_code, expected_changelog):
        actual_code, actual_changelog = rename_types(filename, Source(src))
        self.maxDiff = 8192
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
        self.assertMultiLineEqual(expected_changelog,
                                  actual_changelog.as_text(None)[0]) # 2.7+
    def assertUnchanged(self, src, filename):
        self.assertRefactoringEquals(src, filename, src, '')

    def test_ssa_use_operand_t(self):
        src = (
            'struct GTY(()) ssa_use_operand_t {\n'
            '  struct ssa_use_operand_t* GTY((skip(""))) prev;\n'
            '  struct ssa_use_operand_t* GTY((skip(""))) next;\n'
            '  /* Immediate uses for a given SSA name are maintained as a cyclic\n'
            '     list.  To recognize the root of this list, the location field\n'
            '     needs to point to the original SSA name.  Since statements and\n'
            '     SSA names are of different data types, we need this union.  See\n'
            '     the explanation in struct imm_use_iterator.  */\n'
            '  union { gimple stmt; tree ssa_name; } GTY((skip(""))) loc;\n'
            '  tree *GTY((skip(""))) use;\n'
            '};\n')
        expected_code = (
            'struct GTY(()) ssa_use_operand_t {\n'
            '  struct ssa_use_operand_t* GTY((skip(""))) prev;\n'
            '  struct ssa_use_operand_t* GTY((skip(""))) next;\n'
            '  /* Immediate uses for a given SSA name are maintained as a cyclic\n'
            '     list.  To recognize the root of this list, the location field\n'
            '     needs to point to the original SSA name.  Since statements and\n'
            '     SSA names are of different data types, we need this union.  See\n'
            '     the explanation in struct imm_use_iterator.  */\n'
            '  union { gimple_stmt *stmt; tree ssa_name; } GTY((skip(""))) loc;\n'
            '  tree *GTY((skip(""))) use;\n'
            '};\n')

        expected_changelog = \
            ('\t* tree-core.h (struct ssa_use_operand_t): Replace "gimple" typedef\n'
             '\twith "gimple_stmt *".\n')
        self.assertRefactoringEquals(src, 'tree-core.h',
                                     expected_code, expected_changelog)

    def test_const_gimple_decl(self):
        src = (
            'bool gimple_call_same_target_p (const_gimple, const_gimple);\n')
        expected_code = (
            'bool gimple_call_same_target_p (const gimple_stmt *, const gimple_stmt *);\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_call_same_target_p): Replace "gimple" typedef with\n'
             '\t"gimple_stmt *".\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_not_within_comments(self):
        src = (
            '/* Expand one gimple statement STMT and return the last RTL instruction\n'
            '   before any of the newly generated ones. */\n')
        self.assertUnchanged(src, 'cfgexpand.c')

    def test_not_includes(self):
        src = '#include "gimple-expr.h"\n'
        self.assertUnchanged(src, 'alias.c')

if __name__ == '__main__':
    unittest.main()