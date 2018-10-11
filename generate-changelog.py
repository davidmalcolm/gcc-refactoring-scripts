#!/usr/bin/env python
"""
Parse a diff from git (e.g. from "git show") and generate barebones
ChangeLog entry/entries, to save some of the typing.

The script does the gruntwork of laying out files and function
scopes, indicating which ChangeLog file each is to go in.

It assumes that a fully-automated approach is going to
get some things wrong, so it leaves the hunks in place, but
indented to distinguish them from the surrounding metadata, so
that you can e.g. fix up scopes.
"""

import argparse
import fileinput
import re
import sys
import unittest

from refactor import ChangeLogLayout

class Parser:
    def __init__(self, omit_hunks, show_linenums):
        self.cll = ChangeLogLayout('.')
        self.within_preamble = True
        self.initial_hunk = False
        self.current_dir = ''
        self.omit_hunks = omit_hunks
        self.show_linenums = show_linenums
        self.previous_scope = None
        self.new_file = False

    def write(self, msg):
        sys.stdout.write(msg)

    def parse_linespans(self, linespans):
        numgrp = '([0-9]+)'
        pat = ('-' + numgrp +',' + numgrp + ' '
               r'\+' + numgrp +',' + numgrp)
        m = re.match(pat, linespans)
        return m.groups()

    def on_line(self, line):
        if self.within_preamble:
            if line.startswith('diff --git'):
                self.within_preamble = False
                self.write('\n')
            if line.startswith(' '):
                # Echo any commit message
                self.write('%s\n' % line.strip())
            # Strip away preamble metadata
            return

        if line.startswith('diff --git'):
            self.new_file = False
            return

        if line.startswith('index '):
            return

        if line.startswith('--- a/'):
            return

        if line.startswith('new file mode'):
            return

        if line == '--- /dev/null\n':
            self.new_file = True
            return

        # '+++ b/gcc/asan.c\n'
        m = re.match(r'\+\+\+ b/(.+)', line)
        if m:
            # Start of per-file changes
            git_path = m.group(1) # e.g. "gcc/gimple.h"
            cll_path = './%s' % git_path # e.g. "./gcc/gimple.h"
            dir_ = self.cll.locate_dir(cll_path) # e.g "./gcc"

            # Strip off leading "./":
            assert dir_.startswith('./')
            dir_ = dir_[2:]

            # Emit e.g. "gcc/ChangeLog:" whenever the enclosing ChangeLog
            # changes.
            if dir_ != self.current_dir:
                self.current_dir = dir_
                self.write('%s/ChangeLog:\n' % dir_)

            # Get path relative to the ChangeLog file
            # e.g. "gimple.h"
            rel_path = self.cll.get_path_relative_to_changelog(cll_path)
            self.write('\t* %s' % rel_path)
            if self.new_file:
                text = 'New file.'
                if 'testsuite' in cll_path:
                    text = 'New test.'
                self.write(': %s\n' % text)
            else:
                self.write(' ')
                self.initial_hunk = True
                self.previous_scope = None
            return

        # '@@ -1936,7 +1936,7 @@ transform_statements (void)\n'
        if line.startswith('@') and not self.new_file:
            # This is a hunk.  Print the funcname, and "Likewise."
            # since we'll probably want that in most places.
            m = re.match('@@ (.+) @@ (.+)\n', line)
            if self.show_linenums:
                linespans = m.group(1)
                startline = self.parse_linespans(linespans)[2]
                self.write(startline)
            if m:
                scope = m.group(2).split(' ')
            else:
                scope = ['UNKNOWN']
            if scope[0] == 'struct':
                # e.g. "struct foo"
                scope = ' '.join(scope)
            else:
                # Assume a function decl with args; use just the name:
                scope = scope[0]
            if self.initial_hunk:
                indent = ''
                self.initial_hunk = False
            else:
                indent = '\t'
            if not self.omit_hunks or scope != self.previous_scope:
                self.write('%s(%s): Likewise.\n' % (indent, scope))
                self.previous_scope = scope
            return

        # Print the remaining lines, massively indented (to easily
        # distinguish them from the metadata).
        # We can then use this to identify and describe the underlying
        # changes (and perhaps fix erroneous scope metadata)
        if not self.omit_hunks:
            self.write('%s%s\n' % (' ' * 16, line.rstrip()))

class TestParser(Parser):
    def __init__(self, omit_hunks, show_linenums):
        Parser.__init__(self, omit_hunks, show_linenums)
        self.text = ''

    def write(self, msg):
        self.text += msg

class TestGenerateChangeLog(unittest.TestCase):
    def get_clog(self, diff):
        p = TestParser(False, False)
        p.cll.dirs = ['./libcpp', './gcc/testsuite']
        for line in diff.splitlines():
            # TODO: after py3k we can use keepends=True
            line += '\n'
            p.on_line(line)
        return p.text

    def test_simple(self):
        diff = """
diff --git a/libcpp/macro.c b/libcpp/macro.c
index 073816d..aacaf8c 100644
--- a/libcpp/macro.c
+++ b/libcpp/macro.c
@@ -964,6 +964,10 @@ _cpp_arguments_ok (cpp_reader *pfile, cpp_macro *macro, const cpp_hashnode *node
               "macro \"%s\" passed %u arguments, but takes just %u",
               NODE_NAME (node), argc, macro->paramc);
 
+  if (macro->line > RESERVED_LOCATION_COUNT)
+    cpp_error_at (pfile, CPP_DL_NOTE, macro->line, "macro \"%s\" defined here",
+                 NODE_NAME (node));
+
   return false;
 }
"""
        clog = self.get_clog(diff)
        self.assertMultiLineEqual(clog,
                                  """
libcpp/ChangeLog:
	* macro.c (_cpp_arguments_ok): Likewise.
                               "macro "%s" passed %u arguments, but takes just %u",
                               NODE_NAME (node), argc, macro->paramc);
                
                +  if (macro->line > RESERVED_LOCATION_COUNT)
                +    cpp_error_at (pfile, CPP_DL_NOTE, macro->line, "macro "%s" defined here",
                +                 NODE_NAME (node));
                +
                   return false;
                 }
""")

    def test_added_file(self):
        diff = """
diff --git a/gcc/testsuite/c-c++-common/cpp/macro-arg-count-1.c b/gcc/testsuite/c-c++-common/cpp/macro-arg-count-1.c
new file mode 100644
index 0000000..7773c47
--- /dev/null
+++ b/gcc/testsuite/c-c++-common/cpp/macro-arg-count-1.c
@@ -0,0 +1,3 @@
+/* { dg-options "-fdiagnostics-show-caret" } */
+
+#define MACRO_1(X,Y) /* { dg-line "def_of_MACRO_1" } */
"""
        clog = self.get_clog(diff)
        self.assertMultiLineEqual(clog,
                                  """
gcc/testsuite/ChangeLog:
	* c-c++-common/cpp/macro-arg-count-1.c: New test.
                @@ -0,0 +1,3 @@
                +/* { dg-options "-fdiagnostics-show-caret" } */
                +
                +#define MACRO_1(X,Y) /* { dg-line "def_of_MACRO_1" } */
""")

def main():
    argp = argparse.ArgumentParser(description='Auto-generate ChangeLog entries')
    argp.add_argument('--no-hunks', help='omit hunk from output',
                      action='store_true', default=False, dest='omit_hunks')
    # The following option may be useful when merging ChangeLog entries, for
    # keeping the entries sorted relative to the underlying file.
    argp.add_argument('--show-linenums', help='prepend line numbers',
                      action='store_true', default=False, dest='show_linenums')
    argp.add_argument('--test', help='run test suite',
                      action='store_true', default=False, dest='test')
    argp.add_argument('files', nargs='*')

    parsed_args = argp.parse_args()
    sys.argv = [sys.argv[0]] + parsed_args.files

    if parsed_args.test:
        unittest.main()

    p = Parser(parsed_args.omit_hunks,
               parsed_args.show_linenums)
    for line in fileinput.input():
        p.on_line(line)

if __name__ == "__main__":
    main()
