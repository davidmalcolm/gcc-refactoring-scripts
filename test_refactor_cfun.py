from refactor_cfun import expand_cfun_macros
import unittest

class MacroTests(unittest.TestCase):
    def assertRefactoringEquals(self,
                                src, filename,
                                expected_code, expected_changelog):
        actual_code, actual_changelog = expand_cfun_macros(filename, src)
        self.maxDiff = 8192
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+
        self.assertMultiLineEqual(expected_changelog, actual_changelog) # 2.7+
    def assertUnchanged(self, src, filename):
        self.assertRefactoringEquals(src, filename, src, '')

    def test_n_basic_blocks(self):
        src = (
            'rpo = XNEWVEC (int, n_basic_blocks);')
        expected_code = (
            'rpo = XNEWVEC (int, cfun->cfg->get_n_basic_blocks ());')
        expected_changelog = ''
        self.assertRefactoringEquals(src, 'alias.c',
                                     expected_code, expected_changelog)

    def test_FOR_EACH_BB(self):
        src = (
            '  int saved_last_basic_block = last_basic_block;\n'
            '\n'
            '  FOR_EACH_BB (bb)\n'
            '     {\n'
            '       basic_block prev_bb = bb;\n')
        expected_code = (
            '  int saved_last_basic_block = cfun->cfg->get_last_basic_block ();\n'
            '\n'
            '  FOR_EACH_BB_CFG (bb, cfun->cfg)\n'
            '     {\n'
            '       basic_block prev_bb = bb;\n')
        expected_changelog = ''
        self.assertRefactoringEquals(src, 'asan.c',
                                     expected_code, expected_changelog)

    def test_BASIC_BLOCK(self):
        src = (
            'basic_block bb = BASIC_BLOCK (rpo[i]);')
        expected_code = (
            'basic_block bb = cfun->cfg->get_basic_block_by_idx (rpo[i]);')
        expected_changelog = ''
        self.assertRefactoringEquals(src, 'alias.c',
                                     expected_code, expected_changelog)

    def test_NOTE_BASIC_BLOCK(self):
        self.assertUnchanged('NOTE_BASIC_BLOCK (note) = bb;', 'cfgexpand.c')

    def test_profile_status(self):
        src = (
            '  if (profile_status != PROFILE_ABSENT)\n')
        expected_code = (
            '  if (cfun->cfg->get_profile_status () != PROFILE_ABSENT)\n')
        expected_changelog = ''
        self.assertRefactoringEquals(src, 'cfgbuild.c',
                                     expected_code, expected_changelog)


    def test_profile_status_for_function(self):
        self.assertUnchanged(
            '  if (profile_status_for_function (fun) == PROFILE_ABSENT)',
            'predict.c')

if __name__ == '__main__':
    unittest.main()
