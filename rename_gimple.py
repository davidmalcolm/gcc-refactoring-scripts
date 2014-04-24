from collections import OrderedDict
import re
import sys

from refactor import main, Changelog

PATTERN = r'->(symbol\.)(\S)'
pattern = re.compile(PATTERN, re.MULTILINE | re.DOTALL)

def rename_types(clog_filename, src):
    """
    Rename types:
      "gimple" -> "gimple_stmt *"
      "const_gimple" -> "const gimple_stmt *"
    """
    changelog = Changelog(clog_filename)
    scopes = OrderedDict()

    for old, new in (("gimple", "gimple_stmt *"),
                     ("const_gimple", "const gimple_stmt *")):
        # this works backwards through the file
        for m in src.finditer('[^_a-zA-Z0-9](%s)[^_a-zA-Z0-9]' % old):

            # Don't change things within comments.
            if src.within_comment_at(m.start(1)):
                continue

            # Don't change things within string literals (or within
            #   #include ""
            if src.within_string_literal_at(m.start(1)):
                continue

            #line = src.get_line_at(m.start(1))
            scope = src.get_change_scope_at(m.start(1),
                                            raise_exception=True)
            replacement = new
            start, end = m.start(1), m.end(1)

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
                         'Replace "gimple" typedef with "gimple_stmt *".')

    return src.str(), changelog

if __name__ == '__main__':
    main('rename_gimple.py', rename_types, sys.argv,
         skip_testsuite=True)
