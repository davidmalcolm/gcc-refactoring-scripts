from collections import namedtuple, OrderedDict
import re

from refactor import main, Changelog

class Macro(namedtuple("Macro", ("name", "pattern", "expansion"))):
    pass

prev_not_ident_or_deref = '(?<=[^_0-9a-zA-Z>])'
succ_not_ident = '(?=[^_0-9a-zA-Z])'
macros = \
    [# basic-block.h:
     Macro('ENTRY_BLOCK_PTR',
           'ENTRY_BLOCK_PTR' + succ_not_ident,
           'cfun->cfg->entry_block_ptr'),
     Macro('EXIT_BLOCK_PTR',
           'EXIT_BLOCK_PTR' + succ_not_ident,
           'cfun->cfg->exit_block_ptr'),
     Macro('basic_block_info',
           prev_not_ident_or_deref + 'basic_block_info' + succ_not_ident,
           'cfun->cfg->basic_block_info'),
     Macro('n_basic_blocks',
           prev_not_ident_or_deref + 'n_basic_blocks' + succ_not_ident,
           'cfun->cfg->n_basic_blocks'),
     Macro('n_edges',
           prev_not_ident_or_deref + 'n_edges' + succ_not_ident,
           'cfun->cfg->n_edges'),
     Macro('last_basic_block',
           prev_not_ident_or_deref + 'last_basic_block' + succ_not_ident,
           'cfun->cfg->last_basic_block'),
     Macro('label_to_block_map',
           prev_not_ident_or_deref + 'label_to_block_map' + succ_not_ident,
           'cfun->cfg->label_to_block_map'),
     Macro('profile_status',
           prev_not_ident_or_deref + 'profile_status' + succ_not_ident,
           'cfun->cfg->profile_status'),
     Macro('BASIC_BLOCK',
           prev_not_ident_or_deref + 'BASIC_BLOCK \((?P<N>.+)\)',
           'cfun->cfg->get_bb (%(N)s)'),
     Macro('SET_BASIC_BLOCK',
           prev_not_ident_or_deref + 'SET_BASIC_BLOCK \((?P<N>.+), (?P<BB>.+)\)',
           'cfun->cfg->set_bb (%(N)s, %(BB)s)'),
     Macro('FOR_EACH_BB',
           'FOR_EACH_BB \((?P<BB>[^,\n]+)\)',
           'FOR_EACH_BB (%(BB)s, cfun->cfg)'),
     Macro('FOR_ALL_BB',
           'FOR_ALL_BB ?\((?P<BB>[^,\n]+)\)',
           'FOR_ALL_BB (%(BB)s, cfun->cfg)'),
     Macro('FOR_EACH_BB_REVERSE',
           'FOR_EACH_BB_REVERSE \((?P<BB>[^,\n]+)\)',
           'FOR_EACH_BB_REVERSE (%(BB)s, cfun->cfg)'),
                            ]

def expand_cfun_macros(clog_filename, src):
    if clog_filename in ('basic-block.h',

                         # testsuite/
                         'gcc.dg/tree-ssa/20041122-1.c',

                         # This one has its own struct control_flow_graph
                         # with an x_entry_block_ptr field:
                         'gcc.target/ia64/pr49303.c',
                         ):
        return src.str(), ''

    changelog = Changelog(clog_filename)
    macros_removed_by_scope = OrderedDict()
    macros_changed_by_scope = OrderedDict()
    fields_replaced_by_scope = OrderedDict()
    while 1:
        match = 0
        for macro in macros:
            for m in src.finditer(macro.pattern):
                replacement = macro.expansion % m.groupdict()
                # print(replacement)
                if src.within_comment_at(m.start()):
                    continue
                src = src.replace(m.start(), m.end(), replacement)
                scope = src.get_change_scope_at(m.start())
                if macro.name.startswith('FOR_'):
                    dict_ = macros_changed_by_scope
                else:
                    dict_ = macros_removed_by_scope
                if scope in dict_:
                    dict_[scope].add(macro.name)
                else:
                    dict_[scope] = set([macro.name])

                # only process one match at most per re.finditer,
                # since the m.start/end will no longer correspond
                # to the string after the first subsitution
                match = 1
                break
        if not match:
            break
    field_replacements = \
        ( ('x_entry_block_ptr', 'entry_block_ptr'),
          ('x_exit_block_ptr', 'exit_block_ptr'),
          ('x_basic_block_info', 'basic_block_info'),
          ('x_n_basic_blocks', 'n_basic_blocks'),
          ('x_n_edges', 'n_edges'),
          ('x_last_basic_block', 'last_basic_block'),
          ('x_label_to_block_map', 'label_to_block_map'),
          ('x_profile_status', 'profile_status') )

    while 1:
        match = 0
        for old, new in field_replacements:
            for m in src.finditer('->%s' % old):
                replacement = '->%s' % new
                # print(replacement)
                if src.within_comment_at(m.start()):
                    continue
                src = src.replace(m.start(), m.end(), replacement)
                scope = src.get_change_scope_at(m.start())
                if scope in fields_replaced_by_scope:
                    fields_replaced_by_scope[scope].add(old)
                else:
                    fields_replaced_by_scope[scope] = set([old])

                # only process one match at most per re.finditer,
                # since the m.start/end will no longer correspond
                # to the string after the first subsitution
                match = 1
                break
        if not match:
            break
    for scope in macros_removed_by_scope:
        macro_names = sorted(macros_removed_by_scope[scope])
        if len(macro_names) == 1:
            changelog.append(scope,
                             'Remove usage of %s macro.' % macro_names[0])
        else:
            changelog.append(scope,
                             ('Remove uses of macros: %s.'
                              % ', '.join(macro_names)))
    for scope in macros_changed_by_scope:
        macro_names = sorted(macros_changed_by_scope[scope])
        if len(macro_names) == 1:
            changelog.append(scope,
                             ('Added cfun->cfg argument to usage of %s macro.'
                              % macro_names[0]))
        else:
            changelog.append(scope,
                             ('Added cfun->cfg argument to uses of macros: %s.'
                              % ', '.join(macro_names)))
    for scope in fields_replaced_by_scope:
        field_names = sorted(fields_replaced_by_scope[scope])
        if len(field_names) == 1:
            changelog.append(scope,
                             ('Drop leading x_ from usage of %s field.'
                              % field_names[0]))
        else:
            changelog.append(scope,
                             ('Drop leading x_ from uses of macros: %s.'
                              % ', '.join(field_names)))

    #print(src)
    src = src.wrap()
    return src.str(), changelog.content

if __name__ == '__main__':
    main('refactor_cfun.py', expand_cfun_macros)
