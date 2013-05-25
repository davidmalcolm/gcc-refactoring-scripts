import re

from refactor import main

def expand_cfun_macros(filename, src):
    if filename == 'basic-block.h':
        return src, ''

    prev_not_ident = '(?<=[^_0-9a-zA-Z])'
    succ_not_ident = '(?=[^_0-9a-zA-Z])'
    rules = [('ENTRY_BLOCK_PTR' + succ_not_ident,
              'cfun->cfg->get_entry_block ()'),
             ('EXIT_BLOCK_PTR' + succ_not_ident,
              'cfun->cfg->get_exit_block ()'),
             (prev_not_ident + 'basic_block_info' + succ_not_ident,
              'cfun->cfg->get_basic_block_info ()'),
             (prev_not_ident + 'n_basic_blocks' + succ_not_ident,
              'cfun->cfg->get_n_basic_blocks ()'),
             (prev_not_ident + 'n_edges' + succ_not_ident,
              'cfun->cfg->get_n_edges ()'),
             (prev_not_ident + 'last_basic_block' + succ_not_ident,
              'cfun->cfg->get_last_basic_block ()'),
             (prev_not_ident + 'label_to_block_map' + succ_not_ident,
              'cfun->cfg->get_label_to_block_map ()'),
             (prev_not_ident + 'profile_status' + succ_not_ident,
              'cfun->cfg->get_profile_status ()'),
             (prev_not_ident + 'BASIC_BLOCK \((?P<N>.+)\)',
              'cfun->cfg->get_basic_block_by_idx (%(N)s)'),
             (prev_not_ident + 'SET_BASIC_BLOCK \((?P<N>.+), (?P<BB>.+)\)',
              'cfun->cfg->set_basic_block_by_idx (%(N)s, %(BB)s)'),
             ('FOR_EACH_BB \((?P<BB>.+)\)',
              'FOR_EACH_BB_CFG (%(BB)s, cfun->cfg)'),
             ]
    while 1:
        match = 0
        for pat_in, pat_out in rules:
            m = re.search(pat_in, src)
            if m:
                replacement = pat_out % m.groupdict()
                # print(replacement)
                src = (src[:m.start()] + replacement + src[m.end():])
                match = 1
        if not match:
            break

    #print(src)
    return src, '' # FIXME: changelog entry

if __name__ == '__main__':
    main('refactor_cfun.py', expand_cfun_macros)
