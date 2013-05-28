import unittest

from refactor import wrap
from refactor_cfun import expand_cfun_macros

def make_expected_changelog(filename, scope, text):
    return wrap('\t* %s (%s): %s' % (filename, scope, text))

class MacroTests(unittest.TestCase):
    def assertRefactoredCodeEquals(self,
                                   src, filename,
                                   expected_code):
        actual_code, actual_changelog = expand_cfun_macros(filename, src)
        self.maxDiff = 32768
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
    def assertRefactoringEquals(self,
                                src, filename,
                                expected_code, expected_changelog):
        actual_code, actual_changelog = expand_cfun_macros(filename, src)
        self.maxDiff = 8192
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
        self.assertMultiLineEqual(expected_changelog, actual_changelog) # 2.7+
    def assertUnchanged(self, src, filename):
        self.assertRefactoringEquals(src, filename, src, '')

    def test_ENTRY_BLOCK_PTR(self):
        src = (
            '    FOR_EACH_EDGE (e, ei, ENTRY_BLOCK_PTR->succs)')
        expected_code = (
            '    FOR_EACH_EDGE (e, ei, cfun->cfg->entry_block_ptr->succs)')
        expected_changelog = \
            '\t* bb-reorder.c (None): Remove usage of ENTRY_BLOCK_PTR macro.\n'
        self.assertRefactoringEquals(src, 'bb-reorder.c',
                                     expected_code, expected_changelog)

    def test_n_basic_blocks(self):
        src = (
            'rpo = XNEWVEC (int, n_basic_blocks);')
        expected_code = (
            'rpo = XNEWVEC (int, cfun->cfg->n_basic_blocks);')
        expected_changelog = make_expected_changelog('alias.c', 'None',
                                                     'Remove usage of n_basic_blocks macro.')
        self.assertRefactoredCodeEquals(src, 'alias.c',
                                        expected_code)

    def test_FOR_EACH_BB(self):
        src = (
            'static void\n'
            'transform_statements (void)\n'
            '{\n'
            '  basic_block bb, last_bb = NULL;\n'
            '  gimple_stmt_iterator i;\n'
            '  int saved_last_basic_block = last_basic_block;\n'
            '\n'
            '  FOR_EACH_BB (bb)\n'
            '     {\n'
            '       basic_block prev_bb = bb;\n')
        expected_code = (
            'static void\n'
            'transform_statements (void)\n'
            '{\n'
            '  basic_block bb, last_bb = NULL;\n'
            '  gimple_stmt_iterator i;\n'
            '  int saved_last_basic_block = cfun->cfg->last_basic_block;\n'
            '\n'
            '  FOR_EACH_BB (bb, cfun->cfg)\n'
            '     {\n'
            '       basic_block prev_bb = bb;\n')
        expected_changelog = (
            '\t* asan.c (transform_statements): Remove uses of macros: FOR_EACH_BB,\n'
            '\tlast_basic_block.\n')
        self.assertRefactoringEquals(src, 'asan.c',
                                     expected_code, expected_changelog)

    def test_FOR_ALL_BB(self):
        src = (
            '  /* Put all blocks that have no successor into the initial work list.  */\n'
            '  FOR_ALL_BB (bb)\n'
            '    if (EDGE_COUNT (bb->succs) == 0)\n')
        expected_code = (
            '  /* Put all blocks that have no successor into the initial work list.  */\n'
            '  FOR_ALL_BB (bb, cfun->cfg)\n'
            '    if (EDGE_COUNT (bb->succs) == 0)\n')
        self.assertRefactoredCodeEquals(src, 'cfganal.c',
                                        expected_code)

    def test_FOR_ALL_BB_nospace(self):
        src = (
            '		      FOR_ALL_BB(bb)\n')
        expected_code = (
            '		      FOR_ALL_BB (bb, cfun->cfg)\n')
        expected_changelog = ''
        self.assertRefactoredCodeEquals(src, 'df-core.c',
                                        expected_code)

    def test_BASIC_BLOCK(self):
        src = (
            'void\n'
            'init_alias_analysis (void)\n'
            '{\n'
            '...\n'
            'basic_block bb = BASIC_BLOCK (rpo[i]);')
        expected_code = (
            'void\n'
            'init_alias_analysis (void)\n'
            '{\n'
            '...\n'
            'basic_block bb = cfun->cfg->get_bb (rpo[i]);')
        expected_changelog = (
            '\t* alias.c (init_alias_analysis): Remove usage of BASIC_BLOCK macro.\n')
        self.assertRefactoringEquals(src, 'alias.c',
                                     expected_code, expected_changelog)

    def test_NOTE_BASIC_BLOCK(self):
        self.assertUnchanged('NOTE_BASIC_BLOCK (note) = bb;', 'cfgexpand.c')

    def test_profile_status(self):
        src = (
            '  if (profile_status != PROFILE_ABSENT)\n')
        expected_code = (
            '  if (cfun->cfg->profile_status != PROFILE_ABSENT)\n')
        expected_changelog = ''
        self.assertRefactoredCodeEquals(src, 'cfgbuild.c',
                                        expected_code)

    def test_set_profile_state(self):
        src = (
            '  profile_status = PROFILE_ABSENT;\n')
        expected_code = (
            '  cfun->cfg->profile_status = PROFILE_ABSENT;\n')
        expected_changelog = ''
        self.assertRefactoredCodeEquals(src, 'graphite.c',
                                        expected_code)

    def test_profile_status_for_function(self):
        self.assertUnchanged(
            '  if (profile_status_for_function (fun) == PROFILE_ABSENT)',
            'predict.c')

    def test_REG_FREQ_FROM_BB(self):
        src = (
            '  && !ENTRY_BLOCK_PTR->count)\t\t\\')
        expected_code = (
            '  && !cfun->cfg->entry_block_ptr->count)\t\t\\')
        expected_changelog = ''
        self.assertRefactoredCodeEquals(src, 'regs.h',
                                        expected_code)

    def test_FOR_EACH_BB_REVERSE(self):
        src = (
            '  FOR_EACH_BB_REVERSE (bb)\n')
        expected_code = (
            '  FOR_EACH_BB_REVERSE (bb, cfun->cfg)\n')
        expected_changelog = ''
        self.assertRefactoredCodeEquals(src, 'cfghooks.c',
                                        expected_code)

    def test_multiline_params(self):
        src = (
            'static void\n'
            'compute_antinout_edge (sbitmap *antloc, sbitmap *transp, sbitmap *antin,\n'
            '\t\t       sbitmap *antout)\n'
            '{\n'
            '  basic_block *worklist, *qin, *qout, *qend;\n'
            '\n'
            '  qin = qout = worklist = XNEWVEC (basic_block, n_basic_blocks);\n')
        expected_code = (
            'static void\n'
            'compute_antinout_edge (sbitmap *antloc, sbitmap *transp, sbitmap *antin,\n'
            '\t\t       sbitmap *antout)\n'
            '{\n'
            '  basic_block *worklist, *qin, *qout, *qend;\n'
            '\n'
            '  qin = qout = worklist = XNEWVEC (basic_block, cfun->cfg->n_basic_blocks);\n')
        expected_changelog = (
            '\t* lcm.c (compute_antinout_edge): Remove usage of n_basic_blocks macro.\n')
        self.assertRefactoringEquals(src, 'lcm.c',
                                     expected_code, expected_changelog)

    def test_comment(self):
        # The "last_basic_block" embedded in this comment shouldn't be
        # changed:
        self.assertUnchanged(
            ('/* The encoding for a function consists of the following sections:\n'
             '\n'
             '   [...]\n'
             '\n'
             '     THE FUNCTION\n'
             '\n'
             '\n'
             '     last_basic_block - in uleb128 form.\n'
             '\n'
             '     basic blocks     - This is the set of basic blocks.\n'
             '   [...]\n'),
            'lto-streamer.h')

    def test_match_after_comment(self):
        src = (
            '  /* ENTRY_BLOCK_PTR/EXIT_BLOCK_PTR depend on cfun.\n'
            '     Compare against ENTRY_BLOCK/EXIT_BLOCK to avoid that dependency.  */\n'
            '       FOR_BB_BETWEEN (bb, ENTRY_BLOCK_PTR, EXIT_BLOCK_PTR, next_bb)\n')
        expected_code = (
            '  /* ENTRY_BLOCK_PTR/EXIT_BLOCK_PTR depend on cfun.\n'
            '     Compare against ENTRY_BLOCK/EXIT_BLOCK to avoid that dependency.  */\n'
            '       FOR_BB_BETWEEN (bb, cfun->cfg->entry_block_ptr, cfun->cfg->exit_block_ptr, next_bb)\n')
        self.assertRefactoredCodeEquals(src, 'cfg.c',
                                        expected_code)

if __name__ == '__main__':
    unittest.main()
