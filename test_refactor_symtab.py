import unittest

from refactor import wrap, Source
from refactor_symtab import convert_to_inheritance

def make_expected_changelog(filename, scope, text):
    return wrap('\t* %s (%s): %s' % (filename, scope, text))

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

    def test_simple(self):
        src = (
            'static inline bool\n'
            'cgraph_function_with_gimple_body_p (struct cgraph_node *node)\n'
            '{\n'
            ' return node->symbol.definition && !node->thunk.thunk_p && !node->symbol.alias;\n'
            '}\n')
        expected_code = (
            'static inline bool\n'
            'cgraph_function_with_gimple_body_p (struct cgraph_node *node)\n'
            '{\n'
            ' return node->definition && !node->thunk.thunk_p && !node->alias;\n'
            '}\n')
        expected_changelog = \
            ('\t* cgraph.h (cgraph_function_with_gimple_body_p): Update for conversion\n'
             '\tof symtab types to a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'cgraph.h',
                                     expected_code, expected_changelog)

    def test_unchanged(self):
        src = (
            '/* qsort comparison function for argument pairs, with the following\n'
            '   order:\n'
            '    - p->a->expr == NULL\n'
            '    - p->a->expr->expr_type != EXPR_VARIABLE\n'
            '    - growing p->a->expr->symbol.  */\n'
            )
        # Ensure we don't touch the "expr->symbol. " in the above comment
        self.assertUnchanged(src, 'gcc/fortran/interface.c')

    def test_whitespace(self):
        # Ensure that we don't touch whitespace
        src = (
            'void\n'
            'cgraph_turn_edge_to_speculative (struct cgraph_edge *e, /* etc */)\n'
            '{\n'
            '  if (dump_file)\n'
            '    {\n'
            '      fprintf (dump_file, "Indirect call -> direct call from"\n'
            '\t       " other module %s/%i => %s/%i\n",\n'
            '\t       xstrdup (cgraph_node_name (n)), n->symbol.order,\n'
            '\t       xstrdup (cgraph_node_name (n2)), n2->symbol.order);\n'
            '    }\n'
            '\n')
        expected_code = (
            'void\n'
            'cgraph_turn_edge_to_speculative (struct cgraph_edge *e, /* etc */)\n'
            '{\n'
            '  if (dump_file)\n'
            '    {\n'
            '      fprintf (dump_file, "Indirect call -> direct call from"\n'
            '\t       " other module %s/%i => %s/%i\n",\n'
            '\t       xstrdup (cgraph_node_name (n)), n->order,\n'
            '\t       xstrdup (cgraph_node_name (n2)), n2->order);\n'
            '    }\n'
            '\n')
        expected_changelog = \
            ('\t* cgraph.c (cgraph_turn_edge_to_speculative): Update for conversion of\n'
             '\tsymtab types to a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'cgraph.c',
                                     expected_code, expected_changelog)

    def test_removing_upcast(self):
        src = (
            'void\n'
            'dump_cgraph_node (FILE *f, struct cgraph_node *node)\n'
            '{\n'
            '  struct cgraph_edge *edge;\n'
            '  int indirect_calls_count = 0;\n'
            '\n'
            '  dump_symtab_base (f, (symtab_node) node);\n'
            '  /* snip */\n'
            '}\n')
        expected_code = (
            'void\n'
            'dump_cgraph_node (FILE *f, struct cgraph_node *node)\n'
            '{\n'
            '  struct cgraph_edge *edge;\n'
            '  int indirect_calls_count = 0;\n'
            '\n'
            '  dump_symtab_base (f, node);\n'
            '  /* snip */\n'
            '}\n')
        expected_changelog = \
            ('\t* cgraph.c (dump_cgraph_node): Update for conversion of symtab types\n'
             '\tto a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'cgraph.c',
                                     expected_code, expected_changelog)

    def test_prototypes_are_not_casts(self):
        src = (
            'void symtab_register_node (symtab_node);\n'
            'void symtab_unregister_node (symtab_node);\n'
            'void symtab_remove_node (symtab_node);\n')
        self.assertUnchanged(src, 'cgraph.h')

    def test_leave_interesting_casts(self):
        src = (
            'bool\n'
            'symtab_remove_unreachable_nodes (bool before_inlining_p, FILE *file)\n'
            '{\n'
            '  symtab_node first = (symtab_node) (void *) 1;\n')
        self.assertUnchanged(src, 'cgraph.h')

if __name__ == '__main__':
    unittest.main()
