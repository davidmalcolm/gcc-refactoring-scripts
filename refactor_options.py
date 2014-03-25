from collections import namedtuple, OrderedDict
import os
import re
import sys

from refactor import main, Changelog

class Variable(namedtuple('Variable', ('type_', 'name'))):
    pass

def __parse_variable(line):
    # Strip away any initializer
    if '=' in line:
        line = line.split('=')[0]

    # Strip away any array
    if '[' in line:
        line = line.split('[')[0]

    fields = line.split()
    if len(fields) >= 2:
        # Move * indicating pointer into the type:
        if fields[-1].startswith('*'):
            fields[-2] = fields[-2] + ' *'
            fields[-1] = fields[-1][1:]
        var = Variable(type_=' '.join(fields[0:-1]),
                       name=fields[-1])
        return var
    else:
        raise ValueError('unhandled line after "Variable": %s' % line)

class Option(
    namedtuple('Option',
               ('name',

                'availability',
                # one of 'Common', 'Target', or a list
                # of languages

                'kind',
                # one of 'Warning', 'Optimization', or None

                'driver',
                'report',
                'var',
                'init',
                'helptext'))):
    """
    This is what:
       http://gcc.gnu.org/onlinedocs/gccint/Option-file-format.html
    calls an "option definition record"
    """
    @staticmethod
    def from_lines(lines):
        availability = None
        kind = None
        driver = False
        report = False
        var = None
        init = None
        #print('lines: %r' % lines)
        if len(lines) > 1:
            properties = Option.split_into_properties(lines[1])
            for prop in properties:
                if prop in ('Common', 'Target'):
                    if not availability:
                        availability = prop
                    else:
                        # Duplicate availability; ignore
                        pass
                elif prop in ('Warning', 'Optimization'):
                    if kind != None:
                        raise ValueError(lines)
                    kind = prop
                elif prop == 'Driver':
                    driver = True
                elif prop == 'Report':
                    report = True
                elif prop.startswith('Alias('):
                    alias = Option.parse_prop_arg(prop)
                elif prop.startswith('Var('):
                    var = Option.parse_prop_arg(prop)
                    # Handle the 2-arg variant of Var() by taking
                    # the first arg:
                    if var and ',' in var:
                        var = var.split(',')[0].strip()
                elif prop.startswith('Init('):
                    init = Option.parse_prop_arg(prop)
                else:
                    pass
                    #print(prop)
        name = lines[0]
        if name.startswith('-'):
            name = name[1:]
        if name.endswith('='):
            # FIXME: many of these are duplicates, but not all
            name = name[:-1]
        return Option(name=name,
                      availability=availability,
                      kind=kind,
                      driver=driver,
                      report=report,
                      var=var,
                      init=init,
                      helptext='\n'.join(lines[2:]))

    @staticmethod
    def split_into_properties(line):
        # Naive parser: split by whitespace
        items = line.split()

        # Now recombine parenthesized regions, to handle spaces within
        # parentheses
        # Reverse  so that we can use "pop" to pop from the front:
        items = items[::-1]

        result = []
        while items:
            item = items.pop()
            if '(' in item and ')' not in item:
                while items:
                    nextitem = items.pop()
                    item += ' ' + nextitem
                    if ')' in item:
                        break
            result.append(item)

        return result

    @staticmethod
    def parse_prop_arg(prop):
        m = re.match('\S+\((.*)\)', prop)
        if not m:
            return None # for now
            raise ValueError(prop)
        return m.group(1)

def parse_record(lines):
    if lines[0] == 'Variable':
        assert len(lines) == 2
        return __parse_variable(lines[1])
    if lines[0] == 'TargetVariable':
        assert len(lines) == 2
        return __parse_variable(lines[1])
    elif lines == ['###', 'Driver']:
        # not sure what's up with this one
        return None
    else:
        return Option.from_lines(lines)

def find_opt_files(path):
    """
    Yield a sequence of paths to .opt files
    """
    result = []
    def visit(arg, dirname, names):
        # Skip testsuite:
        if 'testsuite' in names:
            names.remove('testsuite')
        for name in sorted(names):
            newpath = os.path.join(dirname, name)
            if os.path.isfile(newpath) and newpath.endswith('.opt'):
                result.append(newpath)
    os.path.walk(path, visit, None)
    return result

def parse_opt_file(path):
    """
    Parse a .opt file, returning a list of Record instances
    See http://gcc.gnu.org/onlinedocs/gccint/Option-file-format.html
    """
    with open(path) as f:
        records = [] # list of Record
        pending = [] # list of lines
        for line in f:
            line = line.rstrip()

            # skip comments
            if ';' in line:
                line = line.split(';')[0]
                if not line:
                    continue

            # empty lines break up records:
            if not line:
                if pending:
                    record = parse_record(pending)
                    if record:
                        records.append(record)
                    pending = []
                continue

            pending.append(line)
    return records

def parse_all_opt_files(path):
    records = []
    for optpath in find_opt_files(path):
        records += parse_opt_file(optpath)
    return records

class Options:
    def __init__(self):
        # There are currently 111 option files:
        #   find . -name "*.opt"|wc -l
        #   111
        self.records = parse_all_opt_files('../src/gcc')
        #from pprint import pprint
        #pprint(self.records)

        # Get names of Option and Variable instances
        self.opt_varnames = set([opt.var
                                 for opt in self.records
                                 if isinstance(opt, Option)])
        self.var_names = set([var.name
                              for var in self.records
                              if isinstance(var, Variable)])
        if 0:
            pprint(self.opt_varnames)
            pprint(self.var_names)

        # ...and combine them:
        # e.g. optimize is a Variable (within common.opt)
        self.varnames = self.opt_varnames.union(self.var_names)

        # Construct regular expressions for matching the varnames.
        # Must not be preceded or followed by valid identifier characters, so
        # that we don't match other variables which have a matching
        # prefix or suffix.
        self.patterns = [(varname,
                          re.compile((r'[^_a-zA-Z0-9](%s)[^_a-zA-Z0-9]'
                                      % varname),
                                     re.MULTILINE | re.DOTALL))
                         for varname in self.varnames]
        #print(len(self.patterns))

    def make_macros_visible(self,clog_filename, src):
        changelog = Changelog(clog_filename)
        scopes = OrderedDict()
        count = 0
        changes = 0
        for varname, pattern in self.patterns:
            match = 0
            count += 1
            if count % 100 == 0:
                print('count: %i' % count)

            if varname == 'TARGET_ACCUMULATE_OUTGOING_ARGS':
                # Nasty special-case: we're handling Vars from all .opt
                # files, and sh.opt has a
                #   Var(TARGET_ACCUMULATE_OUTGOING_ARGS)
                # and uses of this option in sh.c and sh.h, which must
                # become GCC_OPTION (TARGET_ACCUMULATE_OUTGOING_ARGS)
                # whereas i386.opt has a:
                #   Mask(ACCUMULATE_OUTGOING_ARGS)
                # leading to there being a TARGET_ACCUMULATE_OUTGOING_ARGS
                # macro within options.h on i386 builds defined in terms
                # of masking GCC_OPTION (target_flags).
                #
                # Hence only process this as a Var within the sh config
                # subdir:
                if 'config/sh/' not in clog_filename:
                    continue

            for m in src.finditer(pattern):
                # Don't handle code that's already been touched:
                MACRO = 'GCC_OPTION ('
                if src._str[m.start(1) - len(MACRO):m.start(1)] == MACRO:
                    continue

                # Avoid changing variable definitions in print-rtl.c that
                # are guarded by #ifdef GENERATOR_FILE:
                line = src.get_line_at(m.start(1))
                if line.startswith('int'):
                    continue

                # opt_for_fn(fndecl, opt) is its own macro, which potentially
                # looks up option "opt" in a function-specific location.
                # Don't touch such macros (currently all uses are the only
                # thing on their line):
                if 'opt_for_fn' in line:
                    continue

                # Don't change things within comments.  In particular, this
                # avoids lots of rewriting of the word "optimize" to
                # "GCC_OPTION (optimize)".
                if src.within_comment_at(m.start(1)):
                    continue

                # Don't change things within string literals e.g. within
                # spec strings in gcc.c.   It's OK within .md files, since
                # the C fragments in those files occur within strings.
                if src.within_string_literal_at(m.start(1)) \
                   and not clog_filename.endswith('.md'):
                    continue

                scope = src.get_change_scope_at(m.start())
                replacement = 'GCC_OPTION (%s)' % m.group(1)
                src = src.replace(m.start(1), m.end(1), replacement)
                if scope not in scopes:
                    scopes[scope] = scope
                match = 1
                changes += 1
                print('changes: %i' % changes)

        for scope in scopes.keys()[::-1]:
            changelog.append(scope,
                             'Wrap option usage in GCC_OPTION macro.')

        return src.str(), changelog

def path_filter(path):
    if not os.path.isfile(path):
        return False

    if not (path.endswith('.c') or
            path.endswith('.h') or
            path.endswith('.def') or
            path.endswith('.md')):
        return False

    # target.def has various words e.g. "optimize" in comments that
    # shouldn't be wrapped, along with some wrapped in @code{} that
    # probably should, but none that need wrapping.  Skip this file.
    if path.endswith('/target.def'):
        return False

    return True

if __name__ == '__main__':
    options = Options()
    main('refactor_options.py', options.make_macros_visible, sys.argv,
         skip_testsuite=True,
         path_filter=path_filter)
