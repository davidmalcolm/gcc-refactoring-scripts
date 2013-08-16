from collections import namedtuple
import re
import sys

from refactor import main, Changelog, tabify

############################################################################
# Parsing input
############################################################################
IPA_FIELDS = (
    'generate_summary',
    'write_summary',
    'read_summary',
    'write_optimization_summary',
    'read_optimization_summary',
    'stmt_fixup',
    'function_transform_todo_flags_start',
    'function_transform',
    'variable_transform')

class IpaFields(namedtuple('IpaFields',
                           tuple(IPA_FIELDS))):
    @staticmethod
    def from_ctor(ctor):
        fields = [clean_field(field)
                  for field in ''.join(ctor.splitlines()[2:]).split(',')]
        if fields[8] == '{}':
            fields[8] = 'NULL'
        return IpaFields(*fields)

ws = r'\s+'
optws = r'\s*'

PATTERN = (
    'namespace {' + ws
    + r'const pass_data (?P<passdata_name>\S+) =\n'
    + '{[^}]+};\n\n'
    + '(?P<start_of_class>class) (?P<pass_name>\S+) : public ipa_opt_pass_d\n'
    + '{\n'
    + 'public:\n'
    + '(?P<ctor>.*)'
    + '  /\* opt_pass methods: \*/\n'
    + '(?P<opt_pass_methods>.*)'
    + '(?P<end_of_class>}); // class (.*)\n'
    + '\n'
    + '} // anon namespace'
)

pattern = re.compile(PATTERN, re.MULTILINE | re.DOTALL)

def clean_field(field):
    # Strip out C comments:
    field = re.sub(r'(/\*.*\*/)', '', field)
    # Strip out leading/trailing whitespace:
    field = field.strip()
    field = field.replace('\n', ' ')
    if '|' in field:
        field = ' | '.join(to_flags(field))
    return field

def is_null(ptr):
    return ptr in ('NULL', '0')

def refactor_ipa_passes(filename, src):
    changelog = Changelog(filename)
    while 1:
        m = src.search(pattern)
        if m:
            from pprint import pprint
            gd = m.groupdict()
            #pprint(gd)

            # Parse the data
            ctor = gd['ctor']
            fields = IpaFields.from_ctor(ctor)

            # Build in reverse order, to avoid having to update offsets.

            # Insert the new virtual functions:
            vfuncs = '  /* ipa_opt_pass_d methods: */\n'
            for field, value in zip(IPA_FIELDS, fields):
                if field != 'function_transform_todo_flags_start':
                    if not is_null(value):
                        if field == 'stmt_fixup':
                            returntype = 'void'
                            params = 'struct cgraph_node *node, gimple *stmt'
                            args = 'node, stmt'
                        elif field == 'function_transform':
                            returntype = 'unsigned int'
                            params = 'struct cgraph_node *node'
                            args = 'node'
                        elif field == 'variable_transform':
                            returntype = 'void'
                            params = 'struct varpool_node *node'
                            args = 'node'
                        else:
                            returntype = 'void'
                            params = 'void'
                            args = ''
                        vfuncs += '  %s %s (%s)\n' % (returntype, field, params)
                        vfuncs += '  {\n'
                        vfuncs += '    %s%s (%s);\n' % ('return ' if returntype != 'void' else '', value, args)
                        vfuncs += '  }\n\n'

            idx_end_of_class = m.start('end_of_class')
            src = src.replace(idx_end_of_class, idx_end_of_class,
                              tabify(vfuncs))

            # Extract first two lines of existing ctor:
            ctor = '\n'.join(ctor.splitlines()[0:2])
            # ...and add ipa_pass_data:
            ctor += '\n'
            ctor += '                     ipa_%s)\n' % gd['passdata_name']
            ctor += '  {}\n\n'
            replacement = ctor
            src = src.replace(m.start('ctor'), m.end('ctor'), tabify(replacement))

            # Add the ipa_pass_data:
            idx_start_of_class = m.start('start_of_class')
            ipa_pass_data = 'const ipa_pass_data ipa_%s =\n' % gd['passdata_name']
            ipa_pass_data += '{\n'
            for field, value in zip(IPA_FIELDS, fields):
                if field == 'function_transform_todo_flags_start':
                    ipa_pass_data += ('  %s, /* %s */\n'
                                      % (value, field))
                else:
                    ipa_pass_data += ('  %s%s /* has_%s */\n'
                                      % ('false' if is_null(value) else 'true',
                                         ',' if field != 'variable_transform' else '',
                                         field))
            ipa_pass_data += '};\n\n'

            src = src.replace(idx_start_of_class, idx_start_of_class,
                              tabify(ipa_pass_data))
            changelog.append('%(pass_name)s' %gd,
                             'Convert to new API for IPA passes.')
            continue

        # no matches:
        break

    src = src.wrap(tabify_changes=1)
    return src.str(as_tabs=0), changelog

if __name__ == '__main__':
    main('refactor_passes_2.py', refactor_ipa_passes, sys.argv)
