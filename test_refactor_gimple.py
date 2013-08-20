import unittest

from refactor import wrap, Source
from refactor_gimple import convert_to_inheritance, GimpleTypes

def make_expected_changelog(filename, scope, text):
    return wrap('\t* %s (%s): %s' % (filename, scope, text))

"""
+template <>
+template <>
+inline bool
+is_a_helper <gimple_statement_transaction>::test (gimple gs)
+{
+  return gs->code == GIMPLE_TRANSACTION;
+}
+
+template <>
+template <>
+inline bool
+is_a_helper <const gimple_statement_transaction>::test (const_gimple gs)
+{
+  return gs->code == GIMPLE_TRANSACTION;
+}
+
"""

class Tests(unittest.TestCase):
    def assertRefactoredCodeEquals(self,
                                   src, filename,
                                   expected_code):
        actual_code, actual_changelog = convert_to_inheritance(filename, Source(src))
        self.maxDiff = 32768
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
    def assertRefactoringEquals(self,
                                src, filename,
                                expected_code, expected_changelog):
        actual_code, actual_changelog = convert_to_inheritance(filename, Source(src))
        self.maxDiff = 8192
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
        self.assertMultiLineEqual(expected_changelog,
                                  actual_changelog.as_text(None)[0]) # 2.7+
    def assertUnchanged(self, src, filename):
        self.assertRefactoringEquals(src, filename, src, '')

    def test_gimple_types(self):
        # Verify that we're correctly parsing gimple.def and gsstruct.def
        gt = GimpleTypes()
        self.assertIn(('GSS_OMP_FOR', 'gimple_statement_omp_for', 'false'),
                      gt.gsdefs)
        self.assertIn(('GIMPLE_OMP_FOR', 'gimple_omp_for', 'GSS_OMP_FOR'),
                      gt.gimple_defs)
        self.assertEqual(gt.gsscodes['GSS_OMP_FOR'],
                         ('gimple_statement_omp_for', 'false'))
        self.assertEqual(gt.gimplecodes['GIMPLE_OMP_FOR'],
                         ('gimple_omp_for', 'GSS_OMP_FOR'))

        # Ensure we handle the ones that are split across multiple lines:
        self.assertEqual(gt.gimplecodes['GIMPLE_OMP_ATOMIC_LOAD'],
                         ("gimple_omp_atomic_load", 'GSS_OMP_ATOMIC_LOAD'))


    def test_removing_gsbase(self):
        src = (
            'static inline enum gimple_code\n'
            'gimple_code (const_gimple g)\n'
            '{\n'
            '  return g->gsbase.code;\n'
            '}\n')
        expected_code = (
            'static inline enum gimple_code\n'
            'gimple_code (const_gimple g)\n'
            '{\n'
            '  return g->code;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_code): Update for conversion of gimple types to a\n'
             '\ttrue class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_adding_as_a(self):
        src = (
            'static inline void\n'
            'gimple_eh_else_set_e_body (gimple gs, gimple_seq seq)\n'
            '{\n'
            '  GIMPLE_CHECK (gs, GIMPLE_EH_ELSE);\n'
            '  gs->gimple_eh_else.e_body = seq;\n'
            '}\n')
        expected_code = (
            'static inline void\n'
            'gimple_eh_else_set_e_body (gimple gs, gimple_seq seq)\n'
            '{\n'
            '  gimple_statement_eh_else *eh_else_stmt = as_a <gimple_statement_eh_else> (gs);\n'
            '  eh_else_stmt->e_body = seq;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_eh_else_set_e_body): Update for conversion of\n'
             '\tgimple types to a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_gimple_omp_for_set_cond(self):
        """
        This tests converting multiple sites to use of the subclass ptr.
        """
        src = (
            'static inline void\n'
            'gimple_omp_for_set_cond (gimple gs, size_t i, enum tree_code cond)\n'
            '{\n'
            '  GIMPLE_CHECK (gs, GIMPLE_OMP_FOR);\n'
            '  gcc_gimple_checking_assert (TREE_CODE_CLASS (cond) == tcc_comparison\n'
            '\t\t\t      && i < gs->gimple_omp_for.collapse);\n'
            '  gs->gimple_omp_for.iter[i].cond = cond;\n'
            '}\n')
        expected_code = (
            'static inline void\n'
            'gimple_omp_for_set_cond (gimple gs, size_t i, enum tree_code cond)\n'
            '{\n'
            '  gimple_statement_omp_for *omp_for_stmt = as_a <gimple_statement_omp_for> (gs);\n'
            '  gcc_gimple_checking_assert (TREE_CODE_CLASS (cond) == tcc_comparison\n'
            '\t\t\t      && i < omp_for_stmt->collapse);\n'
            '  omp_for_stmt->iter[i].cond = cond;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_omp_for_set_cond): Update for conversion of gimple\n'
             '\ttypes to a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_no_use_of_subclass(self):
        src = (
            'static inline tree\n'
            'gimple_assign_lhs (const_gimple gs)\n'
            '{\n'
            '  GIMPLE_CHECK (gs, GIMPLE_ASSIGN);\n'
            '  return gimple_op (gs, 0);\n'
            '}\n')
        self.assertUnchanged(src, 'gimple.h')

    def test_no_reserved_words(self):
        # "asm" would be a syntax error
        src = (
            'static inline void\n'
            'gimple_asm_set_clobber_op (gimple gs, unsigned index, tree clobber_op)\n'
            '{\n'
            '  GIMPLE_CHECK (gs, GIMPLE_ASM);\n'
            '  gcc_gimple_checking_assert (index < gs->gimple_asm.nc\n'
            '\t\t\t      && TREE_CODE (clobber_op) == TREE_LIST);\n'
            '  gimple_set_op (gs, index + gs->gimple_asm.ni + gs->gimple_asm.no, clobber_op);\n'
            '}\n')
        expected_code = (
            'static inline void\n'
            'gimple_asm_set_clobber_op (gimple gs, unsigned index, tree clobber_op)\n'
            '{\n'
            '  gimple_statement_asm *asm_stmt = as_a <gimple_statement_asm> (gs);\n'
            '  gcc_gimple_checking_assert (index < asm_stmt->nc\n'
            '\t\t\t      && TREE_CODE (clobber_op) == TREE_LIST);\n'
            '  gimple_set_op (gs, index + asm_stmt->ni + asm_stmt->no, clobber_op);\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_asm_set_clobber_op): Update for conversion of\n'
             '\tgimple types to a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_atomic_load(self):
        # This one is split across multiple lines in the gimple.def,
        # and uses "g" rather than "gs" for the param
        src = (
            'static inline void\n'
            'gimple_omp_atomic_load_set_lhs (gimple g, tree lhs)\n'
            '{\n'
            '  GIMPLE_CHECK (g, GIMPLE_OMP_ATOMIC_LOAD);\n'
            '  g->gimple_omp_atomic_load.lhs = lhs;\n'
            '}\n')
        expected_code = (
            'static inline void\n'
            'gimple_omp_atomic_load_set_lhs (gimple g, tree lhs)\n'
            '{\n'
            '  gimple_statement_omp_atomic_load *omp_atomic_load_stmt = as_a <gimple_statement_omp_atomic_load> (g);\n'
            '  omp_atomic_load_stmt->lhs = lhs;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_omp_atomic_load_set_lhs): Update for conversion of\n'
             '\tgimple types to a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

if __name__ == '__main__':
    unittest.main()
