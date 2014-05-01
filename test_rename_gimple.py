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

    def test_multiple_vars(self):
        src = (
            'rtx\n'
            'expand_expr_real_2 (sepops ops, rtx target, enum machine_mode tmode,\n'
            '\tgimple def0, def2;\n')
        expected_code = (
            'rtx\n'
            'expand_expr_real_2 (sepops ops, rtx target, enum machine_mode tmode,\n'
            '\tgimple_stmt *def0, *def2;\n')
        expected_changelog = \
            ('\t* expr.c (expand_expr_real_2): Replace "gimple" typedef with\n'
             '\t"gimple_stmt *".\n')
        self.assertRefactoringEquals(src, 'expr.c',
                                     expected_code, expected_changelog)

    def test_initializer(self):
        # (heavily edited)
        src = (
            'static void\n'
            'build_check_stmt (location_t location, tree base, gimple_stmt_iterator *iter)\n'
            '{\n'
            '\t      gimple shadow_test = build_assign (NE_EXPR, shadow, 0);\n')
        expected_code = (
            'static void\n'
            'build_check_stmt (location_t location, tree base, gimple_stmt_iterator *iter)\n'
            '{\n'
            '\t      gimple_stmt *shadow_test = build_assign (NE_EXPR, shadow, 0);\n')
        expected_changelog = \
            ('\t* asan.c (build_check_stmt): Replace "gimple" typedef with\n'
             '\t"gimple_stmt *".\n')
        self.assertRefactoringEquals(src, 'asan.c',
                                     expected_code, expected_changelog)

    def test_initializer_2(self):
        # (heavily edited)
        src = (
            'static void\n'
            'maybe_move_debug_stmts_to_successors (copy_body_data *id, basic_block new_bb)\n'
            '{\n'
            '  gimple stmt = gsi_stmt (ssi), new_stmt;\n')
        expected_code = (
            'static void\n'
            'maybe_move_debug_stmts_to_successors (copy_body_data *id, basic_block new_bb)\n'
            '{\n'
            '  gimple_stmt *stmt = gsi_stmt (ssi), *new_stmt;\n')
        expected_changelog = \
            ('\t* tree-inline.c (maybe_move_debug_stmts_to_successors): Replace\n'
             '\t"gimple" typedef with "gimple_stmt *".\n')
        self.assertRefactoringEquals(src, 'tree-inline.c',
                                     expected_code, expected_changelog)

    def test_function_decl(self):
        src = ('\n'
               'struct cgraph_edge *cgraph_create_edge (struct cgraph_node *,\n'
               '                                        struct cgraph_node *,\n'
               '                                        gimple, gcov_type, int);\n')
        expected_code = ('\n'
               'struct cgraph_edge *cgraph_create_edge (struct cgraph_node *,\n'
               '                                        struct cgraph_node *,\n'
               '                                        gimple_stmt *, gcov_type, int);\n')
        expected_changelog = \
            ('\t* cgraph.h (cgraph_create_edge): Replace "gimple" typedef with\n'
             '\t"gimple_stmt *".\n')
        self.assertRefactoringEquals(src, 'cgraph.h',
                                     expected_code, expected_changelog)

    def test_function_decl_2(self):
        src = ('\n'
               'static inline void\n'
               'gimple_set_block (gimple g, tree block)\n'
               '{\n')
        expected_code = ('\n'
               'static inline void\n'
               'gimple_set_block (gimple_stmt *g, tree block)\n'
               '{\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_set_block): Replace "gimple" typedef with\n'
             '\t"gimple_stmt *".\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_bb_union(self):
        # Don't touch the "gimple" in "il.gimple.seq":
        src = (
            '\n'
            'static inline gimple_seq\n'
            'bb_seq (const_basic_block bb)\n'
            '{\n'
            '  return (!(bb->flags & BB_RTL)) ? bb->il.gimple.seq : NULL;\n'
            '}\n')
        self.assertUnchanged(src, 'gimple.h')



if __name__ == '__main__':
    unittest.main()
