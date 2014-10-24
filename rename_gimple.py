from collections import OrderedDict
import re
import sys

from refactor import main, Changelog, not_identifier, opt_ws

EXCLUDED_LINES = set([
    # coretypes.h:
    'class gimple;',
    'typedef gimple *gimple_seq;',

    # gimple-pretty-print.c:
    'debug (gimple &ref)',
    'debug (gimple *ptr)',

    # gimple-pretty-print.h:
    'extern void debug (gimple &ref);',
    'extern void debug (gimple *ptr);',

    # system.h:
    '#define CONST_CAST_GIMPLE(X) CONST_CAST (gimple *, (X))',

    # tree-ssa-ccp.c:
    'typedef hash_table <pointer_hash <gimple> > gimple_htab;',
])

def rename_types(clog_filename, src):
    """
    Rename types:
      "gimple" -> "gimple_stmt *"
      "const_gimple" -> "const gimple_stmt *"
    """
    changelog = Changelog(clog_filename)
    scopes = OrderedDict()

    for old, new in (("gimple", "gimple *"),
                     ("const_gimple", "const gimple *")):
        # this works backwards through the file
        for m in src.finditer(not_identifier + ('(%s)' % old) + not_identifier):
            if 0:
                print(m.start(1))
                print(m.end(1))
                print(src._str[m.start(1):m.end(1)])

            # Don't change things within comments.
            if src.within_comment_at(m.start(1)):
                continue

            # Don't change things within string literals (or within
            #   #include ""
            if src.within_string_literal_at(m.start(1)):
                continue
            # The above doesn't reject a string in gengtype.c for some
            # reason; manually do so:
            if clog_filename.endswith('gengtype.c'):
                continue

            # Specialcase: don't touch basic-block.h due to union name:
            #   union basic_block_il_dependent {
            #      struct gimple_bb_info GTY ((tag ("0"))) gimple;
            #                                              ^^^^^^
            if clog_filename.endswith('basic-block.h'):
                continue

            # Don't touch the bb union e.g. "bb->il.gimple.seq":
            if src._str[m.start(1) - 1] == '.':
                continue

            # Skip some specific lines:
            line = src.get_line_at(m.start(1))
            if line.strip() in EXCLUDED_LINES:
                continue

            # Don't touch inheritance from "gimple":
            if line.endswith(': public gimple'):
                continue

            # Don't touch the name of the base class in its declaration:
            if line == '  gimple':
                continue

            scope = src.get_change_scope_at(m.start(1),
                                            raise_exception=True)
            if 0:
                print('scope: %r' % scope)
            replacement = new
            start, end = m.start(1), m.end(1)

            src = _add_stars_in_decls(src, old, new, start, end)

            # Avoid turning:
            #   gimple stmt
            # into
            #   gimple_stmt * stmt
            # converting into
            #   gimple_stmt *stmt
            # instead.
            if new.endswith(' *') and src._str[end] == ' ':
                end += 1
            src = src.replace(start, end, replacement)
            if scope not in scopes:
                scopes[scope] = scope

    # Put the scopes back into forward order in the ChangeLog:
    for scope in list(scopes)[::-1]:
        changelog.append(scope,
                         'Replace "gimple" typedef with "gimple *".')

    return src.str(), changelog

def _add_stars_in_decls(src, old, new, start, end, within_patch=0):
    # Handle variable declarations, where more than one decl could be
    # present.
    # Assume that such repeated declarations are the first thing on
    # their line.
    if 0:
        print('_add_stars_in_decls(src=%r, old=%r, new=%r, start=%r, end=%r, within_patch=%r)'
              % (src.str(), old, new, start, end, within_patch))
        print(src._str.replace('\n', ' '))
        print((' ' * start) + '^')
        print((' ' * end) + '^')
        print('start: %r' % start)

    line = src.get_line_at(start)
    if within_patch:
        # skip leading "-", "+", " " character:
        line = line[1:]
    if not line[0].isspace():
        return src
    if not line.lstrip().startswith(old):
        return src
    if line.endswith(')') or line.endswith(','):
        return src


    # Are we within a function declaration:
    last_idx_of_open_paren = src._str.rfind('(', 0, start)
    last_idx_of_semicolon = src._str.rfind(';', 0, start)
    last_idx_of_open_brace = src._str.rfind('{', 0, start)
    if 0:
        print('last_idx_of_open_paren: %r' % last_idx_of_open_paren)
        print('last_idx_of_semicolon: %r' % last_idx_of_semicolon)
        print('last_idx_of_open_brace: %r' % last_idx_of_open_brace)

    if last_idx_of_open_brace < last_idx_of_open_paren:
        if last_idx_of_open_paren > last_idx_of_semicolon:
            # If so, don't add extra *:
            return src

    if 0:
        print('line: %r' % line)

    # Handle such declarations the dirty way by replacing
    # ", " with ", *":
    assert new.endswith(' *')

    DECL_PATTERN = opt_ws + '([^;]+);'
    start_of_decls = start + len(old)
    m = re.match(DECL_PATTERN,
                 src._str[start_of_decls:],
                 re.MULTILINE | re.DOTALL)
    if not m:
        return src

    if 0:
        print(m.groups())
    end_of_decls = start_of_decls + m.end(1)
    decls = src._str[start_of_decls:end_of_decls]

    # Don't do this to function parameters:
    if decls.startswith(','):
        return src

    # Replace ", " with ", *", but not within function calls:
    new_decls = ''
    paren_nesting = 0
    for ch in decls:
        if ch == '(':
            paren_nesting += 1
        elif ch == ')':
            paren_nesting -= 1
        elif ch == ' ':
            if new_decls and new_decls[-1] == ',' and paren_nesting == 0:
                ch = ' *'
        new_decls += ch
    if 0:
        print('new_decls: %r' % new_decls)
    src = src.replace(start_of_decls, end_of_decls, new_decls)
    return src

if __name__ == '__main__':
    main('rename_gimple.py', rename_types, sys.argv,
         skip_testsuite=True)
