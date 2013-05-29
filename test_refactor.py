import unittest

from refactor import tabify, \
    ChangeLogLayout, ChangeLogAdditions, \
    AUTHOR, Source

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
        self.assertEqual(
            Source('void\n'
                   'foo ()\n'
                   '{\n'
                   '  int i;\n').get_change_scope_at(50),
            'foo')
        self.assertEqual(Source(
            'static void\n'
            'compute_antinout_edge (sbitmap *antloc, sbitmap *transp, sbitmap *antin,\n'
            '\t\t       sbitmap *antout)\n'
            '{\n'
            '  basic_block *worklist, *qin, *qout, *qend;\n'
            ).get_change_scope_at(4096),
                         'compute_antinout_edge')

        self.assertEqual(Source(
                '#define REG_FREQ_FROM_EDGE_FREQ(freq)	\t\t\t	   \\\n'
                '  (optimize_size || (flag_branch_probabilities && !ENTRY_BLOCK_PTR->count) \\\n'
                '   ? REG_FREQ_MAX : (freq * REG_FREQ_MAX / BB_FREQ_MAX)\t\t\t   \\\n'
                '   ? (freq * REG_FREQ_MAX / BB_FREQ_MAX) : 1)\n')
                         .get_change_scope_at(4096),
                         'REG_FREQ_FROM_EDGE_FREQ')

    def test_within_comment(self):
        self.assertTrue(Source('/* foo').within_comment_at(1024))
        self.assertFalse(Source('/* foo */').within_comment_at(1024))
        self.assertFalse(Source('foo').within_comment_at(1024))
        self.assertFalse(Source('/* foo */ /').within_comment_at(1024))

class ChangeLogTests(unittest.TestCase):
    # Constructing a ChangeLogLayout is somewhat expensive, so only
    # do it once, shared by all the cases:
    cll = ChangeLogLayout('../src')

    def test_changelog_layout(self):
        self.assertIn('../src/gcc', self.cll.dirs)
        self.assertIn('../src/gcc/testsuite', self.cll.dirs)

        self.assertEqual(self.cll.locate_dir('../src/gcc/foo.c'),
                         '../src/gcc')
        self.assertEqual(self.cll.locate_dir('../src/gcc/c-family/foo.c'),
                         '../src/gcc/c-family')
        self.assertEqual(self.cll.locate_dir('../src/gcc/testsuite/gcc.target/arm/pr46631.cgcc/testsuite/foo.c'),
                         '../src/gcc/testsuite')

    def test_additions(self):
        TEST_ISODATE = '1066-10-14'
        cla = ChangeLogAdditions(self.cll, TEST_ISODATE, AUTHOR,
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

    def test_get_relative_path(self):
        self.assertEqual(
            self.cll.get_path_relative_to_changelog('../src/gcc/tree-cfg.c'),
            'tree-cfg.c')
        self.assertEqual(
            self.cll.get_path_relative_to_changelog('../src/gcc/testsuite/g++.dg/some-file.c'),
            'g++.dg/some-file.c')

class TestWrapping(unittest.TestCase):
    def assertWrappedCodeEquals(self, src, expected_code):
        as_tabs = ('\t' in src)
        actual_code = Source(src).wrap(just_changed=0).str(as_tabs=as_tabs)
        self.maxDiff = 32768
        self.assertMultiLineEqual(expected_code, actual_code) # 2.7+

    def assertUnchanged(self, src):
        self.assertWrappedCodeEquals(src, src)

    def test_unchanged(self):
        # The unchanged case, with lines < 80:
        src = (
            '  /* Remove BB from the original basic block array.  */\n'
            '  (*cfun->cfg->basic_block_info)[bb->index] = NULL;\n'
            '  cfun->cfg->n_basic_blocks--;\n')
        self.assertUnchanged(src)

    def test_linewrap(self):
        src = (
            '			  if (best_edge->dest != cfun->cfg->entry_block_ptr->next_bb)\n')
        expected_code = (
            '			  if (best_edge->dest\n'
            '			      != cfun->cfg->entry_block_ptr->next_bb)\n')
        self.assertWrappedCodeEquals(src, expected_code)

    def test_linewrap2(self):
        src = (
            '      if ((e->src != cfun->cfg->entry_block_ptr && bbd[e->src->index].end_of_trace >= 0)\n'
            '\t  || (e->flags & EDGE_DFS_BACK))\n')
        expected_code = (
            '      if ((e->src != cfun->cfg->entry_block_ptr\n'
            '\t   && bbd[e->src->index].end_of_trace >= 0)\n'
            '\t  || (e->flags & EDGE_DFS_BACK))\n')
        self.assertWrappedCodeEquals(src, expected_code)

    def test_overlong_(self):
        src = (
            '      superset_entry->children\n'
            '        = splay_tree_new_ggc (splay_tree_compare_ints,\n'
            '                              ggc_alloc_splay_tree_scalar_scalar_splay_tree_s,\n'
            '                              ggc_alloc_splay_tree_scalar_scalar_splay_tree_node_s);\n')
        # No good way of wrapping this
        self.assertUnchanged(src)

    def test_linewrap3(self):
        src = (
            '  if (e->src != cfun->cfg->entry_block_ptr && e->dest != cfun->cfg->exit_block_ptr\n'
            '      && any_condjump_p (BB_END (e->src))\n'
            '      && JUMP_LABEL (BB_END (e->src)) == BB_HEAD (e->dest))\n'
            '    {\n')
        expected_code = (
            '  if (e->src != cfun->cfg->entry_block_ptr\n'
            '      && e->dest != cfun->cfg->exit_block_ptr\n'
            '      && any_condjump_p (BB_END (e->src))\n'
            '      && JUMP_LABEL (BB_END (e->src)) == BB_HEAD (e->dest))\n'
            '    {\n')
        self.assertWrappedCodeEquals(src, expected_code)

    def test_linewrap_indent_multiline(self):
        # Ensure that we take into account more than just the preceding
        # line when choosing indent location of a wrapped line
        src = (
            '   for (attempt = get_immediate_dominator (CDI_DOMINATORS, def->bb);\n'
            '        !give_up && attempt && attempt != cfun->cfg->entry_block_ptr && def->cost >= min_cost;\n'
            '        attempt = get_immediate_dominator (CDI_DOMINATORS, attempt))\n')
        expected_code = (
            '   for (attempt = get_immediate_dominator (CDI_DOMINATORS, def->bb);\n'
            '        !give_up && attempt && attempt != cfun->cfg->entry_block_ptr\n'
            '        && def->cost >= min_cost;\n'
            '        attempt = get_immediate_dominator (CDI_DOMINATORS, attempt))\n')
        self.assertWrappedCodeEquals(src, expected_code)

    def test_linewrap_indent_nested_parens(self):
        # Ensure that we respect nested parens when choosing indent location
        # of a wrapped line
        src = (
            '  basic_block bb = create_basic_block (BB_HEAD (e->dest), NULL, cfun->cfg->entry_block_ptr);\n')
        expected_code = (
            '  basic_block bb = create_basic_block (BB_HEAD (e->dest), NULL,\n'
            '                                       cfun->cfg->entry_block_ptr);\n')
        self.assertWrappedCodeEquals(src, expected_code)

    def test_linewrap_ternary(self):
        src = (
            '  if (dump_file)\n'
            '    fprintf (dump_file,\n'
            '             "Deleting fallthru block %i.\\n",\n'
            '             b->index);\n'
            '\n'
            '          c = b->prev_bb == cfun->cfg->entry_block_ptr ? b->next_bb : b->prev_bb;\n')
        expected_code = (
            '  if (dump_file)\n'
            '    fprintf (dump_file,\n'
            '             "Deleting fallthru block %i.\\n",\n'
            '             b->index);\n'
            '\n'
            '          c = ((b->prev_bb == cfun->cfg->entry_block_ptr)\n'
            '               ? b->next_bb : b->prev_bb);\n')
        self.assertWrappedCodeEquals(src, expected_code)

    def test_linewrap_ternary_short(self):
        src = (
            '  basic_block begin = reverse ? cfun->cfg->exit_block_ptr : cfun->cfg->entry_block_ptr;\n')
        expected_code = (
            '  basic_block begin = (reverse\n'
            '                       ? cfun->cfg->exit_block_ptr : cfun->cfg->entry_block_ptr);\n')
        self.assertWrappedCodeEquals(src, expected_code)

    def test_linewrap_ternary_arg(self):
        src = (
            '       e = make_edge (call_bb, return_bb,\n'
            '                      return_bb == cfun->cfg->exit_block_ptr ? 0 : EDGE_FALLTHRU);\n')
        expected_code = (
            '       e = make_edge (call_bb, return_bb,\n'
            '                      return_bb == cfun->cfg->exit_block_ptr\n'
            '                      ? 0 : EDGE_FALLTHRU);\n')
        self.assertWrappedCodeEquals(src, expected_code)

    def test_linewrap_invocation(self):
        src = (
            '      int save_LR_around_toc_setup = (TARGET_ELF\n'
            '                                      && DEFAULT_ABI != ABI_AIX\n'
            '                                      && flag_pic\n'
            '                                      && ! info->lr_save_p\n'
            '                                      && EDGE_COUNT (cfun->cfg->exit_block_ptr->preds) > 0);\n')
        # We don't have a good way of wrapping this without breaking the
        # EDGE_COUNT () invocation:
        self.assertUnchanged(src)

if __name__ == '__main__':
    unittest.main()
