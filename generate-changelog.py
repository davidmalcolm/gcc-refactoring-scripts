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

import fileinput
import re
import sys
import argparse

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
                sys.stdout.write('\n')
            if line.startswith(' '):
                # Echo any commit message
                print(line.strip())
            # Strip away preamble metadata
            return

        if line.startswith('diff --git'):
            return

        if line.startswith('index '):
            return

        if line.startswith('--- a/'):
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
                print('%s/ChangeLog:' % dir_)

            # Get path relative to the ChangeLog file
            # e.g. "gimple.h"
            rel_path = self.cll.get_path_relative_to_changelog(cll_path)
            sys.stdout.write('\t* %s ' % rel_path)
            self.initial_hunk = True
            self.previous_scope = None
            return

        # '@@ -1936,7 +1936,7 @@ transform_statements (void)\n'
        if line.startswith('@'):
            # This is a hunk.  Print the funcname, and "Likewise."
            # since we'll probably want that in most places.
            m = re.match('@@ (.+) @@ (.+)\n', line)
            if self.show_linenums:
                linespans = m.group(1)
                startline = self.parse_linespans(linespans)[2]
                sys.stdout.write(startline)
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
                print('%s(%s): Likewise.' % (indent, scope))
                self.previous_scope = scope
            return

        # Print the remaining lines, massively indented (to easily
        # distinguish them from the metadata).
        # We can then use this to identify and describe the underlying
        # changes (and perhaps fix erroneous scope metadata)
        if not self.omit_hunks:
            print('%s%s' % (' ' * 16, line.rstrip()))


def main():
    argp = argparse.ArgumentParser(description='Auto-generate ChangeLog entries')
    argp.add_argument('--no-hunks', help='omit hunk from output',
                      action='store_true', default=False, dest='omit_hunks')
    # The following option may be useful when merging ChangeLog entries, for
    # keeping the entries sorted relative to the underlying file.
    argp.add_argument('--show-linenums', help='prepend line numbers',
                      action='store_true', default=False, dest='show_linenums')
    argp.add_argument('files', action='append', nargs='*')

    parsed_args = argp.parse_args()
    sys.argv = parsed_args.files

    p = Parser(parsed_args.omit_hunks,
               parsed_args.show_linenums)
    for line in fileinput.input():
        p.on_line(line)

if __name__ == "__main__":
    main()
