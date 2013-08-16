from collections import namedtuple, OrderedDict
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
        properties = lines[1].split()
        for prop in properties:
            if prop in ('Common', 'Target'):
                if availability != None:
                    raise ValueError(lines)
                availability = prop
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
            elif prop.startswith('Init('):
                init = Option.parse_prop_arg(prop)
            else:
                pass
                #print(prop)
        return Option(name=lines[0],
                      availability=availability,
                      kind=kind,
                      driver=driver,
                      report=report,
                      var=var,
                      init=init,
                      helptext='\n'.join(lines[2:]))

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
    elif lines == ['###', 'Driver']:
        # not sure what's up with this one
        return None
    else:
        return Option.from_lines(lines)

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

def make_macros_visible(clog_filename, src):
    records = parse_opt_file('../src/gcc/common.opt')
    optvarnames = [opt.var
                   for opt in records
                   if isinstance(opt, Option)]
    # Construct regular expressions for matching the varnames.
    # Must not be preceded by "( ", so that we don't repeatedly
    # apply the transformation
    # Must not be followed by a valid identifier character, so
    # that we don't match other variables which have a matching
    # initial suffix.
    patterns = [re.compile(r'[^\(] (%s)[^_a-zA-Z0-9]' % varname, re.MULTILINE | re.DOTALL)
                for varname in optvarnames]
    changelog = Changelog(clog_filename)
    scopes = OrderedDict()
    while 1:
        match = 0
        for pattern in patterns:
            m = src.search(pattern)
            if m:
                scope = src.get_change_scope_at(m.start())
                replacement = 'GCC_OPTION (%s)' % m.group(1)
                src = src.replace(m.start(1), m.end(1), replacement)
                if scope not in scopes:
                    scopes[scope] = scope
                match = 1

        # no matches:
        if not match:
            break

    for scope in scopes:
        changelog.append(scope,
                         'Wrap option usage in GCC_OPTION macro.')

    return src.str(), changelog

if __name__ == '__main__':
    main('refactor_options.py', make_macros_visible, sys.argv,
         skip_testsuite=True)
