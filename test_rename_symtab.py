import unittest

from refactor import wrap, Source
from rename_symtab import rename_types

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

    def test_simple(self):
        src = (
            'struct GTY((user)) cgraph_node : public symtab_node_base {')
        expected_code = (
            'struct GTY((user)) cgraph_node : public symtab_node {')
        expected_changelog = \
            ('\t* cgraph.h (cgraph_node): Rename symtab_node_base to symtab_node.\n')
        self.assertRefactoringEquals(src, 'cgraph.h',
                                     expected_code, expected_changelog)

    def test_simple2(self):
        src = (
            'extern void gt_ggc_mx (symtab_node_base *p);\n'
            'extern void gt_pch_nx (symtab_node_base *p);\n'
            'extern void gt_pch_nx (symtab_node_base *p, gt_pointer_operator op, void *cookie);\n')
        expected_code = (
            'extern void gt_ggc_mx (symtab_node *p);\n'
            'extern void gt_pch_nx (symtab_node *p);\n'
            'extern void gt_pch_nx (symtab_node *p, gt_pointer_operator op, void *cookie);\n')
        expected_changelog = \
            ('\t* cgraph.h (gt_ggc_mx): Rename symtab_node_base to symtab_node.\n'
             '\t(gt_pch_nx): Likewise.\n')
        self.assertRefactoringEquals(src, 'cgraph.h',
                                     expected_code, expected_changelog)

    def test_pointer_tweak(self):
        src = (
            '\n'
            'symtab_node symtab_alias_ultimate_target (symtab_node,\n'
            '\t\t\t\t\t  enum availability *avail = NULL);\n')
        expected_code = (
            '\n'
            'symtab_node *symtab_alias_ultimate_target (symtab_node *,\n'
            '\t\t\t\t\t  enum availability *avail = NULL);\n')
        expected_changelog = \
            ('\t* cgraph.h (symtab_alias_ultimate_target): Rename symtab_node_base to\n'
             '\tsymtab_node.\n')
        self.assertRefactoringEquals(src, 'cgraph.h',
                                     expected_code, expected_changelog)

    def test_globals(self):
        src = (
            '/* Queue of cgraph nodes scheduled to be lowered.  */\n'
            'symtab_node x_cgraph_nodes_queue;\n')
        expected_code = (
            '/* Queue of cgraph nodes scheduled to be lowered.  */\n'
            'symtab_node *x_cgraph_nodes_queue;\n')
        expected_changelog = \
            ('\t* cgraph.c (x_cgraph_nodes_queue): Rename symtab_node_base to\n'
             '\tsymtab_node.\n')
        self.assertRefactoringEquals(src, 'cgraph.c',
                                     expected_code, expected_changelog)

    def test_is_a_helper(self):
        src = (
            'template <>\n'
            'template <>\n'
            'inline bool\n'
            'is_a_helper <cgraph_node>::test (symtab_node_base *p)\n'
            '{\n'
            '  return p->type == SYMTAB_FUNCTION;\n'
            '}\n')
        expected_code = (
            'template <>\n'
            'template <>\n'
            'inline bool\n'
            'is_a_helper <cgraph_node>::test (symtab_node *p)\n'
            '{\n'
            '  return p->type == SYMTAB_FUNCTION;\n'
            '}\n')
        expected_changelog = \
            ('\t* cgraph.h (is_a_helper <cgraph_node>::test): Rename symtab_node_base\n'
             '\tto symtab_node.\n')
        self.assertRefactoringEquals(src, 'cgraph.h',
                                     expected_code, expected_changelog)

    def test_multiline_params(self):
        src = (
            'struct ipa_ref *\n'
            'ipa_record_reference (symtab_node referring_node,\n'
            '\t\t      symtab_node referred_node,\n'
            '\t\t      enum ipa_ref_use use_type, gimple stmt)\n'
            '{\n')
        expected_code = (
            'struct ipa_ref *\n'
            'ipa_record_reference (symtab_node *referring_node,\n'
            '\t\t      symtab_node *referred_node,\n'
            '\t\t      enum ipa_ref_use use_type, gimple stmt)\n'
            '{\n')
        expected_changelog = \
            ('\t* ipa-ref.c (ipa_record_reference): Rename symtab_node_base to\n'
             '\tsymtab_node.\n')
        self.assertRefactoringEquals(src, 'ipa-ref.c',
                                     expected_code, expected_changelog)

if __name__ == '__main__':
    unittest.main()
