from collections import OrderedDict
import re
import sys

from refactor import main, Changelog

PATTERN = r'->(symbol\.)(\S)'
pattern = re.compile(PATTERN, re.MULTILINE | re.DOTALL)

UPCAST_PATTERN = r'(\(symtab_node\))[^;]'
upcast_pattern = re.compile(UPCAST_PATTERN, re.MULTILINE | re.DOTALL)

def convert_to_inheritance(clog_filename, src):
    """
    Look for code of the form:
        "->symbol."
    followed by non-whitespace, and replace it with:
        "->"

    Eliminate redundant upcasts to "(symtab_node)"
    """

    changelog = Changelog(clog_filename)
    scopes = OrderedDict()
    for m in src.finditer(pattern):
        scope = src.get_change_scope_at(m.start())
        replacement = '->' + m.group(2)
        src = src.replace(m.start(), m.end(), replacement)
        if scope not in scopes:
            scopes[scope] = scope

    for m in src.finditer(upcast_pattern):
        scope = src.get_change_scope_at(m.start())
        replacement = ''
        start, end = m.start(1), m.end(1)
        if src._str[end] == ' ':
            end += 1

        # Various specialcases to avoid removing necessary casts
        # from (void *) to (symtab_node):
        line = src.get_line_at(start)
        line = line.strip()
        if 0:
            print(repr(line))
        if line in ('ipa_record_reference ((symtab_node)data,',
                    'first = (symtab_node)first->aux;',
                    'node = (symtab_node) *slot;',
                    'node->next_sharing_asm_name = (symtab_node)*aslot;',
                    '((symtab_node)*aslot)->previous_sharing_asm_name = node;',
                    '? (symtab_node)varpool_node_for_decl (node->alias_target)',
                    ': (symtab_node)cgraph_get_create_node (node->alias_target));'):
            continue
        if '(intptr_t)' in line:
            continue
        if src._str[end:].startswith('(void *)'):
            continue

        src = src.replace(start, end, replacement)
        if scope not in scopes:
            scopes[scope] = scope

    for scope in scopes:
        changelog.append(scope,
                         'Update for conversion of symtab types to a true class hierarchy.')

    return src.str(), changelog

if __name__ == '__main__':
    main('refactor_symtab.py', convert_to_inheritance, sys.argv,
         skip_testsuite=True)
