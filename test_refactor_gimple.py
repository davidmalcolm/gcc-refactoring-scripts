import unittest

from refactor import wrap, Source
from refactor_gimple import convert_to_inheritance, GimpleTypes

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

        # Verify the C++ inheritance hierarchy:
        self.assertEqual(gt.parentclasses['gimple_statement_base'], None)
        self.assertEqual(gt.parentclasses['gimple_statement_transaction'],
                         'gimple_statement_with_memory_ops_base')

        self.assertEqual(gt.get_parent_classes('gimple_statement_omp_task'),
                         ['gimple_statement_base',
                          'gimple_statement_omp',
                          'gimple_statement_omp_parallel',
                          'gimple_statement_omp_task'])

        self.assertEqual(gt.get_codes_for_struct('gimple_statement_eh_else'),
                         ['GIMPLE_EH_ELSE'])

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
            '#undef DEFGSSTRUCT\n'
            '\n'
            'static inline void\n'
            'gimple_eh_else_set_e_body (gimple gs, gimple_seq seq)\n'
            '{\n'
            '  GIMPLE_CHECK (gs, GIMPLE_EH_ELSE);\n'
            '  gs->gimple_eh_else.e_body = seq;\n'
            '}\n')
        expected_code = (
            '#undef DEFGSSTRUCT\n'
            '\n'
            'template <>\n'
            'template <>\n'
            'inline bool\n'
            'is_a_helper <gimple_statement_eh_else>::test (gimple gs)\n'
            '{\n'
            '  return gs->code == GIMPLE_EH_ELSE;\n'
            '}\n'
            '\n'
            'static inline void\n'
            'gimple_eh_else_set_e_body (gimple gs, gimple_seq seq)\n'
            '{\n'
            '  gimple_statement_eh_else *eh_else_stmt =\n'
            '    as_a <gimple_statement_eh_else> (gs);\n'
            '  eh_else_stmt->e_body = seq;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (is_a_helper <gimple_statement_eh_else> (gimple)): New.\n'
             '\t(gimple_eh_else_set_e_body): Update for conversion of gimple types to\n'
             '\ta true class hierarchy.\n')
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
            '  gimple_statement_omp_for *omp_for_stmt =\n'
            '    as_a <gimple_statement_omp_for> (gs);\n'
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
            '  gimple_statement_omp_atomic_load *omp_atomic_load_stmt =\n'
            '    as_a <gimple_statement_omp_atomic_load> (g);\n'
            '  omp_atomic_load_stmt->lhs = lhs;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_omp_atomic_load_set_lhs): Update for conversion of\n'
             '\tgimple types to a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_gimple_omp_task_clauses(self):
        # This one checks for GIMPLE_OMP_TASK (which is GSS_OMP_TASK and thus
        # struct gimple_statement_omp_task), but then uses the union field
        # gimple_omp_parallel, which is GSS_OMP_PARALLEL (which is struct
        # gimple_statement_omp_parallel).
        # omp_task is indeed a subclass of omp_parallel; we need to walk the
        # base classes when considering union fields.
        src = (
            'static inline tree\n'
            'gimple_omp_task_clauses (const_gimple gs)\n'
            '{\n'
            '  GIMPLE_CHECK (gs, GIMPLE_OMP_TASK);\n'
            '  return gs->gimple_omp_parallel.clauses;\n'
            '}\n')
        expected_code = (
            'static inline tree\n'
            'gimple_omp_task_clauses (const_gimple gs)\n'
            '{\n'
            '  const gimple_statement_omp_task *omp_task_stmt =\n'
            '    as_a <const gimple_statement_omp_task> (gs);\n'
            '  return omp_task_stmt->clauses;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_omp_task_clauses): Update for conversion of gimple\n'
             '\ttypes to a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_gimple_omp_taskreg_child_fn_ptr(self):
        # This one has a more involved check:
        #    if (gimple_code (gs) != GIMPLE_OMP_PARALLEL)
        #        GIMPLE_CHECK (gs, GIMPLE_OMP_TASK);
        # which effectively means
        #   "either GIMPLE_OMP_TASK or GIMPLE_OMP_PARALLEL"
        # Given that gimple_statement_omp_task is a subclass of
        # gimple_statement_omp_parallel we can simply check against
        # the base class:
        # FIXME: what should  as_a <gimple_statement_omp_parallel>  look like?
        src = (
            'static inline tree *\n'
            'gimple_omp_taskreg_child_fn_ptr (gimple gs)\n'
            '{\n'
            '  if (gimple_code (gs) != GIMPLE_OMP_PARALLEL)\n'
            '    GIMPLE_CHECK (gs, GIMPLE_OMP_TASK);\n'
            '  return &gs->gimple_omp_parallel.child_fn;\n'
            '}\n')
        expected_code = (
            'static inline tree *\n'
            'gimple_omp_taskreg_child_fn_ptr (gimple gs)\n'
            '{\n'
            '  gimple_statement_omp_parallel *omp_parallel_stmt =\n'
            '    as_a <gimple_statement_omp_parallel> (gs);\n'
            '  return &omp_parallel_stmt->child_fn;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_omp_taskreg_child_fn_ptr): Update for conversion of\n'
             '\tgimple types to a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_const(self):
        src = (
            'static inline tree\n'
            'gimple_bind_vars (const_gimple gs)\n'
            '{\n'
            '  GIMPLE_CHECK (gs, GIMPLE_BIND);\n'
            '  return gs->gimple_bind.vars;\n'
            '}\n')
        expected_code = (
            'static inline tree\n'
            'gimple_bind_vars (const_gimple gs)\n'
            '{\n'
            '  const gimple_statement_bind *bind_stmt =\n'
            '    as_a <const gimple_statement_bind> (gs);\n'
            '  return bind_stmt->vars;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_bind_vars): Update for conversion of gimple types\n'
             '\tto a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_const_2(self):
        src = (
            'static inline tree\n'
            'gimple_omp_critical_name (const_gimple gs)\n'
            '{\n'
            '  GIMPLE_CHECK (gs, GIMPLE_OMP_CRITICAL);\n'
            '  return gs->gimple_omp_critical.name;\n'
            '}\n')
        expected_code = (
            'static inline tree\n'
            'gimple_omp_critical_name (const_gimple gs)\n'
            '{\n'
            '  const gimple_statement_omp_critical *omp_critical_stmt =\n'
            '    as_a <const gimple_statement_omp_critical> (gs);\n'
            '  return omp_critical_stmt->name;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_omp_critical_name): Update for conversion of gimple\n'
             '\ttypes to a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_const_3(self):
        # The preceding function was messing up the regex
        src = (
            'static inline gimple_seq\n'
            'gimple_transaction_body (gimple gs)\n'
            '{\n'
            '  return *gimple_transaction_body_ptr (gs);\n'
            '}\n'
            '\n'
            '/* Return the label associated with a GIMPLE_TRANSACTION.  */\n'
            '\n'
            'static inline tree\n'
            'gimple_transaction_label (const_gimple gs)\n'
            '{\n'
            '  GIMPLE_CHECK (gs, GIMPLE_TRANSACTION);\n'
            '  return gs->gimple_transaction.label;\n'
            '}\n')
        expected_code = (
            'static inline gimple_seq\n'
            'gimple_transaction_body (gimple gs)\n'
            '{\n'
            '  return *gimple_transaction_body_ptr (gs);\n'
            '}\n'
            '\n'
            '/* Return the label associated with a GIMPLE_TRANSACTION.  */\n'
            '\n'
            'static inline tree\n'
            'gimple_transaction_label (const_gimple gs)\n'
            '{\n'
            '  const gimple_statement_transaction *transaction_stmt =\n'
            '    as_a <const gimple_statement_transaction> (gs);\n'
            '  return transaction_stmt->label;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_transaction_label): Update for conversion of gimple\n'
             '\ttypes to a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_gimple_call_clobber_set(self):
        # This one has a param that isn't named "gs" or "g"
        src = (
            'static inline struct pt_solution *\n'
            'gimple_call_clobber_set (gimple call)\n'
            '{\n'
            '  GIMPLE_CHECK (call, GIMPLE_CALL);\n'
            '  return &call->gimple_call.call_clobbered;\n'
            '}\n')
        expected_code = (
            'static inline struct pt_solution *\n'
            'gimple_call_clobber_set (gimple call)\n'
            '{\n'
            '  gimple_statement_call *call_stmt = as_a <gimple_statement_call> (call);\n'
            '  return &call_stmt->call_clobbered;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_call_clobber_set): Update for conversion of gimple\n'
             '\ttypes to a true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)

    def test_has_mem_ops(self):
        src = (
            'static inline void\n'
            'gimple_set_use_ops (gimple g, struct use_optype_d *use)\n'
            '{\n'
            '  gimple_statement_with_ops *ops_stmt =\n'
            '    as_a <gimple_statement_with_ops> (g);\n'
            '  ops_stmt->use_ops = use;\n'
            '}\n'
            '\n'
            '\n'
            '/* Return the set of VUSE operand for statement G.  */\n'
            '\n'
            'static inline use_operand_p\n'
            'gimple_vuse_op (const_gimple g)\n'
            '{\n'
            '  struct use_optype_d *ops;\n'
            '  if (!gimple_has_mem_ops (g))\n'
            '    return NULL_USE_OPERAND_P;\n'
            '  ops = g->gsops.opbase.use_ops;\n'
            '  if (ops\n'
            '      && USE_OP_PTR (ops)->use == &g->gsmembase.vuse)\n'
            '    return USE_OP_PTR (ops);\n'
            '  return NULL_USE_OPERAND_P;\n'
            '}\n')
        expected_code = (
            'static inline void\n'
            'gimple_set_use_ops (gimple g, struct use_optype_d *use)\n'
            '{\n'
            '  gimple_statement_with_ops *ops_stmt =\n'
            '    as_a <gimple_statement_with_ops> (g);\n'
            '  ops_stmt->use_ops = use;\n'
            '}\n'
            '\n'
            '\n'
            '/* Return the set of VUSE operand for statement G.  */\n'
            '\n'
            'static inline use_operand_p\n'
            'gimple_vuse_op (const_gimple g)\n'
            '{\n'
            '  struct use_optype_d *ops;\n'
            '  const gimple_statement_with_memory_ops *mem_ops_stmt =\n'
            '     dyn_cast <const gimple_statement_with_memory_ops> (g);\n'
            '  if (!mem_ops_stmt)\n'
            '    return NULL_USE_OPERAND_P;\n'
            '  ops = mem_ops_stmt->use_ops;\n'
            '  if (ops\n'
            '      && USE_OP_PTR (ops)->use == &mem_ops_stmt->vuse)\n'
            '    return USE_OP_PTR (ops);\n'
            '  return NULL_USE_OPERAND_P;\n'
            '}\n')
        expected_changelog = \
            ('\t* gimple.h (gimple_vuse_op): Update for conversion of gimple types to\n'
             '\ta true class hierarchy.\n')
        self.assertRefactoringEquals(src, 'gimple.h',
                                     expected_code, expected_changelog)


if __name__ == '__main__':
    unittest.main()
