import unittest

from refactor import tabify, \
    ChangeLogLayout, ChangeLogAdditions, \
    AUTHOR, get_change_scope

class GeneralTests(unittest.TestCase):
    def assertTabifyEquals(self, input_code, expected_result):
        actual_result = tabify(input_code)
        self.maxDiff = 8192
        self.assertMultiLineEqual(expected_result, actual_result) # 2.7+

    def test_tabify(self):
        self.assertTabifyEquals(
            input_code=('public:\n'
                        '  pass_jump2(context &ctxt)\n'
                        '    : rtl_opt_pass(ctxt,\n'
                        '                   "jump2",\n'
                        '                   OPTGROUP_NONE,\n'),
            expected_result=('public:\n'
                             '  pass_jump2(context &ctxt)\n'
                             '    : rtl_opt_pass(ctxt,\n'
                             '\t\t   "jump2",\n'
                             '\t\t   OPTGROUP_NONE,\n'))

    def test_get_funcname(self):
        self.assertEqual(get_change_scope('void\n'
                                      'foo ()\n'
                                      '{\n'
                                      '  int i;\n',
                                      50),
                         'foo')
        self.assertEqual(get_change_scope('static void\n'
            'compute_antinout_edge (sbitmap *antloc, sbitmap *transp, sbitmap *antin,\n'
            '\t\t       sbitmap *antout)\n'
            '{\n'
            '  basic_block *worklist, *qin, *qout, *qend;\n',
                                      4096),
                         'compute_antinout_edge')

        self.assertEqual(get_change_scope(
                '#define REG_FREQ_FROM_EDGE_FREQ(freq)	\t\t\t	   \\\n'
                '  (optimize_size || (flag_branch_probabilities && !ENTRY_BLOCK_PTR->count) \\\n'
                '   ? REG_FREQ_MAX : (freq * REG_FREQ_MAX / BB_FREQ_MAX)\t\t\t   \\\n'
                '   ? (freq * REG_FREQ_MAX / BB_FREQ_MAX) : 1)\n',
                4096),
                         'REG_FREQ_FROM_EDGE_FREQ')


class ChangeLogTests(unittest.TestCase):
    def test_changelog_layout(self):
        cll = ChangeLogLayout('../src')
        self.assertIn('../src/gcc', cll.dirs)
        self.assertIn('../src/gcc/testsuite', cll.dirs)

        self.assertEqual(cll.locate_dir('../src/gcc/foo.c'),
                         '../src/gcc')
        self.assertEqual(cll.locate_dir('../src/gcc/c-family/foo.c'),
                         '../src/gcc/c-family')
        self.assertEqual(cll.locate_dir('../src/gcc/testsuite/gcc.target/arm/pr46631.cgcc/testsuite/foo.c'),
                         '../src/gcc/testsuite')

    def test_additions(self):
        TEST_ISODATE = '1066-10-14'
        cll = ChangeLogLayout('../src')
        cla = ChangeLogAdditions(cll, TEST_ISODATE, AUTHOR,
                                 'This is some header text')
        cla.add_text('../src/gcc/foo.c',
                     '* foo.c (bar): Do something.')
        cla.add_text('../src/gcc/bar.c',
                     '* bar.c (some_fn): Likewise.')
        cla.add_text('../src/gcc/testsuite/baz.c',
                     '* baz.c (quux): Do something.')
        cla.add_text('../src/gcc/testsuite/some-other-file.c',
                     '') # should have no effect
        self.maxDiff = 8192
        self.assertMultiLineEqual(
            cla.text_per_dir['../src/gcc'],
            ('1066-10-14  David Malcolm  <dmalcolm@redhat.com>\n'
             '\n'
             'This is some header text\n'
             '* foo.c (bar): Do something.\n'
             '* bar.c (some_fn): Likewise.\n'))
        self.assertMultiLineEqual(
            cla.text_per_dir['../src/gcc/testsuite'],
            ('1066-10-14  David Malcolm  <dmalcolm@redhat.com>\n'
             '\n'
             'This is some header text\n'
             '* baz.c (quux): Do something.\n'))


if __name__ == '__main__':
    unittest.main()
