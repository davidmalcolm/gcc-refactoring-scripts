#!/usr/bin/python
from collections import namedtuple, OrderedDict
import os
import sys

from refactor import main, Changelog, Source, not_identifier
from rename_gimple import _add_stars_in_decls

class StmtClass(namedtuple('StmtClass',
                           ('orig_name', 'typedef', 'new_name'))):
    pass

stmt_classes = [
    StmtClass('gimple_statement_cond',
              'gimple_cond',
              'gcond'),
    StmtClass('gimple_statement_debug',
              'gimple_debug',
              'gdebug'),
    StmtClass('gimple_statement_goto',
              'gimple_goto',
              'ggoto'),
    StmtClass('gimple_statement_label',
              'gimple_label',
              'glabel'),
    StmtClass('gimple_statement_switch',
              'gimple_switch',
              'gswitch'),
    StmtClass('gimple_statement_assign',
              'gimple_assign',
              'gassign'),
    StmtClass('gimple_statement_asm',
              'gimple_asm',
              'gasm'),
    StmtClass('gimple_statement_call',
              'gimple_call',
              'gcall'),
    StmtClass('gimple_statement_transaction',
              'gimple_transaction',
              'gtransaction'),
    StmtClass('gimple_statement_return',
              'gimple_return',
              'greturn'),
    StmtClass('gimple_statement_bind',
              'gimple_bind',
              'gbind'),
    StmtClass('gimple_statement_catch',
              'gimple_catch',
              'gcatch'),
    StmtClass('gimple_statement_eh_filter',
              'gimple_eh_filter',
              'geh_filter'),
    StmtClass('gimple_statement_eh_mnt',
              'gimple_eh_must_not_throw',
              'geh_mnt'),
    StmtClass('gimple_statement_eh_else',
              'gimple_eh_else',
              'geh_else'),
    StmtClass('gimple_statement_resx',
              'gimple_resx',
              'gresx'),
    StmtClass('gimple_statement_eh_dispatch',
              'gimple_eh_dispatch',
              'geh_dispatch'),
    StmtClass('gimple_statement_phi',
              'gimple_phi',
              'gphi'),
    StmtClass('gimple_statement_try',
              'gimple_try',
              'gtry'),
    StmtClass('gimple_statement_omp_atomic_load',
              'gimple_omp_atomic_load',
              'gomp_atomic_load'),
    StmtClass('gimple_statement_omp_atomic_store',
              'gimple_omp_atomic_store',
              'gomp_atomic_store'),
    StmtClass('gimple_statement_omp_continue',
              'gimple_omp_continue',
              'gomp_continue'),
    StmtClass('gimple_statement_omp_critical',
              'gimple_omp_critical',
              'gomp_critical'),
    StmtClass('gimple_statement_omp_for',
              'gimple_omp_for',
              'gomp_for'),
    StmtClass('gimple_statement_omp_parallel',
              'gimple_omp_parallel',
              'gomp_parallel'),
    StmtClass('gimple_statement_omp_task',
              'gimple_omp_task',
              'gomp_task'),
    StmtClass('gimple_statement_omp_sections',
              'gimple_omp_sections',
              'gomp_sections'),
    StmtClass('gimple_statement_omp_single',
              'gimple_omp_single',
              'gomp_single'),
    StmtClass('gimple_statement_omp_target',
              'gimple_omp_target',
              'gomp_target'),
    StmtClass('gimple_statement_omp_teams',
              'gimple_omp_teams',
              'gomp_teams'),
]

def rename_types_in_src(src, where, changelog):
    """
    Update patches to follow the naming convention from
      https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00346.html

    Rename new types:
      "ORIG_NAME" -> "NEW_NAME"
      "TYPEDEF" -> "NEW_NAME *"
      "const_TYPEDEF" -> "const NEW_NAME *"
    e.g.
      "gimple_statement_switch" -> "gswitch"
      "gimple_switch" -> "gswitch *"
      "const_gimple_switch" -> "const gswitch *"
    """
    assert where in ('subject', 'patch', 'file-on-disk')
    patterns = []
    scopes = OrderedDict()
    for subclass in stmt_classes:
        for old, new in ((subclass.orig_name,
                          subclass.new_name),
                         (subclass.typedef,
                          '%s *' % subclass.new_name),
                         ('const_%s' % subclass.typedef,
                          'const %s *' % subclass.new_name)):
            patterns.append((old, new, not_identifier + ('(%s)' % old) + not_identifier))
            # Also match at the very end:
            patterns.append((old, new, not_identifier + ('(%s)$' % old)))

    patterns.append( ('gimple_phi_iterator', 'gphi_iterator',
                      not_identifier + '(gimple_phi_iterator)' + not_identifier) )
    patterns.append( ('gimple_phi_iterator', 'gphi_iterator',
                      not_identifier + '(gimple_phi_iterator)$') )

    for old, new, pattern in patterns:
            # this works backwards through the file
            for m in src.finditer_multiline(pattern):
                if 0:
                    print(m.start(1))
                    print(m.end(1))
                    print(src._str[m.start(1):m.end(1)])

                if changelog:
                    scope = src.get_change_scope_at(m.start(1),
                                                    raise_exception=True)
                    # Some manual fixups:
                    if scope == 'equal' and src.filename == 'gimplify.c':
                        scope = 'struct gimplify_ctx'
                    if scope == 'Copyright' and src.filename == 'coretypes.h':
                        scope = None
                    if scope == 'Copyright' and src.filename == 'gimple-builder.h':
                        scope = 'build_assign'
                    if scope in ('phi', 'Copyright') and src.filename == 'gimple-iterator.h':
                        scope = 'gimple_phi_iterator::phi'
                    if scope == 'typedefs' and src.filename == 'gimple.h':
                        scope = 'is_a_helper <gimple_statement_cond *>'
                    if scope == 'GTY' and src.filename == 'gimple.h':
                        scope = 'gimple_statement_cond'
                    if scope == 'Copyright' and src.filename == 'omp-low.c':
                        scope = 'struct omp_for_data'
                    if scope == 'hierarchy' and src.filename == 'gimple-low.c':
                        scope = 'struct return_statements_t'
                    if scope == 'information' and src.filename == 'gimple.h':
                        scope = 'gimple_statement_call'
                    if scope == 'Copyright' and src.filename == 'gimple-streamer-in.c':
                        scope = 'input_phi'
                    if scope == 'Copyright' and src.filename == 'tree-ssa-dom.c':
                        scope = 'struct hashable_expr'
                    if scope == 'land' and src.filename == 'gimple.h':
                        scope = 'gimple_statement_catch'

                    if scope in ('Copyright', 'phi', 'hierarchy', 'information',
                                 'GTY', 'typedefs', 'equal', 'land'):
                        raise ValueError('scope: %r in %r within line %r '
                                         % (scope,
                                            src.filename,
                                            src.get_line_at(m.start(1))))
                    if 0:
                        print('scope: %r' % scope)
                    if scope not in scopes:
                        scopes[scope] = scope

                replacement = new
                start, end = m.start(1), m.end(1)

                if new.endswith(' *'):
                    src = _add_stars_in_decls(src, old, new, start, end,
                                              within_patch=1 if where == 'patch' else 0)

                # Avoid turning:
                #   gimple_switch stmt
                # into
                #   gswitch * stmt
                # converting into
                #   gswitch *stmt
                # instead.
                if where != 'subject':
                    if new.endswith(' *') and src._str[end] == ' ':
                        end += 1

                src = src.replace(start, end, replacement)

    # Put the scopes back into forward order in the ChangeLog:
    if changelog:
        for scope in list(scopes)[::-1]:
            changelog.append(scope,
                             'Rename gimple subclass types.')

    return src

def rename_types_in_str(text, where):
    src = Source(text)
    src = rename_types_in_src(src, where, None)
    return src.str()

def path_filter(path):
    return (os.path.isfile(path)
            and (path.endswith('.c') or
                 path.endswith('.h') or
                 path.endswith('gsstruct.def')))

def rename_types(clog_filename, src):
    changelog = Changelog(clog_filename)
    scopes = OrderedDict()
    src = rename_types_in_src(src, 'file-on-disk', changelog)
    return src.str(), changelog

if __name__ == '__main__':
    main('rename_gimple_subclasses.py', rename_types, sys.argv,
         skip_testsuite=True,
         path_filter=path_filter,
         clogname='ChangeLog.gimple-classes')
