from collections import OrderedDict
import re
import sys

from refactor import main, Changelog, not_identifier

PATTERN = r'->(symbol\.)(\S)'
pattern = re.compile(PATTERN, re.MULTILINE | re.DOTALL)

def rename_types(clog_filename, src):
    """
    Rename types:
      "symtab_node_base" -> "symtab_node"
      "symtab_node" -> "symtab_node *"
    """
    changelog = Changelog(clog_filename)
    scopes = OrderedDict()

    for old, new in (("symtab_node", "symtab_node *"),
                     ("symtab_node_base", "symtab_node"),
                     ('const_symtab_node', 'const symtab_node *')):
        # this works backwards through the file
        for m in src.finditer(not_identifier + ('(%s)' % old) + not_identifier):
            line = src.get_line_at(m.start(1))
            if line in ('   The symtab_node is inherited by cgraph and varpol nodes.  */',):
                continue
            scope = src.get_change_scope_at(m.start(1),
                                            raise_exception=True)
            replacement = new
            start, end = m.start(1), m.end(1)

            # Avoid turning:
            #   symtab_node foo
            # into
            #   symtab_node * foo
            # converting into
            #   symtab_node *foo
            # instead.
            if new.endswith(' *') and src._str[end] == ' ':
                end += 1
            src = src.replace(start, end, replacement)
            if scope not in scopes:
                scopes[scope] = scope

    # Put the scopes back into forward order in the ChangeLog:
    for scope in list(scopes)[::-1]:
        changelog.append(scope,
                         'Rename symtab_node_base to symtab_node.')

    return src.str(), changelog

if __name__ == '__main__':
    main('rename_symtab.py', rename_types, sys.argv,
         skip_testsuite=True)
