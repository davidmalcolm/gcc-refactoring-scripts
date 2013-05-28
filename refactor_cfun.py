from collections import namedtuple, OrderedDict
import re

from refactor import main, Changelog, get_change_scope, within_comment

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

def expand_cfun_macros(filename, src):
    if filename in ('basic-block.h',
                    'testsuite/gcc.dg/tree-ssa/20041122-1.c',
                    ):
        return src, ''

    changelog = Changelog(filename)
    macros_removed_by_scope = OrderedDict()
    while 1:
        match = 0
        for macro in macros:
            for m in re.finditer(macro.pattern, src):
                replacement = macro.expansion % m.groupdict()
                # print(replacement)
                if within_comment(src, m.start()):
                    continue
                src = (src[:m.start()] + replacement + src[m.end():])
                scope = get_change_scope(src, m.start())
                if scope in macros_removed_by_scope:
                    macros_removed_by_scope[scope].add(macro.name)
                else:
                    macros_removed_by_scope[scope] = set([macro.name])

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
            changelog.append('(%s): Remove usage of %s macro.\n'
                             % (scope, macro_names[0]))
        else:
            changelog.append('(%s): Remove uses of macros: %s.\n'
                             % (scope, ', '.join(macro_names)))


    #print(src)
    return src, changelog.content

if __name__ == '__main__':
    main('refactor_cfun.py', expand_cfun_macros)
