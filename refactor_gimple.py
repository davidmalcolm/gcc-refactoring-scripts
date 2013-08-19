from collections import OrderedDict
import re
import sys

from refactor import main, Changelog

PATTERN = r'->(gsbase\.)(\S)'
pattern = re.compile(PATTERN, re.MULTILINE | re.DOTALL)

PATTERN2 = (r'{\n'
            + '  (?P<check_stmt>GIMPLE_CHECK \(gs, (?P<gimple_code>[A-Z_]+?)\));\n'
            + '  (?P<body>.+?)\n'
            + '}\n')
pattern2 = re.compile(PATTERN2, re.MULTILINE | re.DOTALL)

#FIXME: gstruct.def vs gimple.h

#code_to_struct = dict((key, value) for value, key, _ in subclasses)
#code_to_subname = dict((key, value) for _, key, value in subclasses)

class GimpleTypes:
    def __init__(self):
        from pprint import pprint
        self.gsdefs = GimpleTypes.parse_gsstruct_def()
        #pprint(self.gsdefs)

        self.gimple_defs = GimpleTypes.parse_gimple_def()
        #pprint(self.gimple_defs)

        # Mapping from GSS_foo to (struct_name, has_tree_operands) pair:
        self.gsscodes = {}
        for gss_enum, struct_name, has_tree_operands in self.gsdefs:
            self.gsscodes [gss_enum] = (struct_name, has_tree_operands)

        #pprint(self.gsscodes)

        # Mapping from gimple_code to (printable_name, GSS_foo):
        self.gimplecodes = {}
        for gimplecode, printable_name, gss_enum in self.gimple_defs:
            self.gimplecodes[gimplecode] = (printable_name, gss_enum)
        #pprint(self.gimplecodes)

    def get_struct_for_gimple_code(self, gimple_code):
        printable_name, gss_enum = self.gimplecodes[gimple_code]
        struct_name, has_tree_operands = self.gsscodes[gss_enum]
        return struct_name

    def get_union_field(self, gimple_code):
        """
        Get the name of the field for this gss value within
        union gimple_statement_d
        """
        struct = self.get_struct_for_gimple_code(gimple_code)
        assert struct.startswith('gimple_statement_')
        if struct == 'gimple_statement_omp':
            return 'omp'
        else:
            # Convert 'gimple_statement_' prefix to 'gimple_':
            return 'gimple_' + struct[len('gimple_statement_'):]

    def get_instance_name(self, gimple_code):
        """
        Suggest an instance name for a subclass for this gimple code
        """
        struct = self.get_struct_for_gimple_code(gimple_code)
        assert struct.startswith('gimple_statement_')
        # Remove 'gimple_statement_' prefix:
        return struct[len('gimple_statement_'):]

    @staticmethod
    def parse_gsstruct_def():
        """
        gsstruct.def defines "enum gimple_statement_structure_enum"
        """
        gss_defs = []
        with open('../src/gcc/gsstruct.def') as f:
            for line in f:
                m = re.match('^DEFGSSTRUCT\((.+?), (.+?), (.+?)\)$', line)
                if m:
                    gss_defs.append(m.groups())
        return gss_defs

    @staticmethod
    def parse_gimple_def():
        """
        gimple.def defines "enum gimple_code"
        """
        gimple_defs = []
        with open('../src/gcc/gimple.def') as f:
            for line in f:
                m = re.match('^DEFGSCODE\((.+?), "(.+?)", (.+?)\)$', line)
                if m:
                    gimple_defs.append(m.groups())
        return gimple_defs


def convert_to_inheritance(clog_filename, src):
    """
    Look for code of the form:
        "->gsbase."
    followed by non-whitespace, and replace it with:
        "->"
    """
    gt = GimpleTypes()

    changelog = Changelog(clog_filename)
    scopes = OrderedDict()
    while 1:
        m = src.search(pattern)
        if m:
            scope = src.get_change_scope_at(m.start())
            replacement = '->' + m.group(2)
            src = src.replace(m.start(), m.end(), replacement)
            if scope not in scopes:
                scopes[scope] = scope
            continue

        m = src.search(pattern2)
        if m:
            scope = src.get_change_scope_at(m.start('body'))
            #print(scope)
            if scope not in scopes:
                scopes[scope] = scope
            gd = m.groupdict()
            #from pprint import pprint
            #pprint(gd)
            gimple_code = gd['gimple_code']
            subclass = gt.get_struct_for_gimple_code(gimple_code)
            union_field = gt.get_union_field(gimple_code)
            #print(union_field)
            instance_name = gt.get_instance_name(gimple_code)
            #print(instance_name)
            replacement = ('%s *%s = as_a <%s> (gs)'
                           % (subclass, instance_name, subclass))
            src = src.replace(m.start('check_stmt'), m.end('check_stmt'), replacement)

            for m in src.finditer('(gs->%s.)' % union_field):
                #print m.groups()
                src = src.replace(m.start(), m.end(), '%s->' % instance_name)
            continue

        # no matches:
        break

    for scope in scopes:
        changelog.append(scope,
                         'Update for conversion of gimple types to a true class hierarchy.')

    return src.str(), changelog

if __name__ == '__main__':
    main('refactor_symtab.py', convert_to_inheritance, sys.argv,
         skip_testsuite=True)
