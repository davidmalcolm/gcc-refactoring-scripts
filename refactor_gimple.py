from collections import OrderedDict
import re
import sys

from refactor import main, Changelog, ws, identifier_group, \
    named_identifier_group

PATTERN = r'->(gsbase\.)(\S)'
pattern = re.compile(PATTERN, re.MULTILINE | re.DOTALL)

PATTERN2 = ('\n'
            + identifier_group + r' \((?P<const>const_)?gimple ' + named_identifier_group('param') + '(?P<extra_args>[^)]*?)\)\n'
            + r'{\n'
            + '(?P<header>[^}]*?)'
            + r'(?P<cond>  if \(!gimple_has_mem_ops \(g\)\)\n'
            + '    return ).+?\n'
            + '(?P<code>.+?)\n'
            + '}\n')
pattern2 = re.compile(PATTERN2, re.MULTILINE | re.DOTALL)

DOWNCAST_PATTERN = (
    '\n'
    + identifier_group + r' \((?P<const>const_)?gimple ' + named_identifier_group('param') + '(?P<extra_args>[^)]*?)\)\n'
    + r'{\n'
    + '  (?P<check_stmt>GIMPLE_CHECK \((?P=param), (?P<gimple_code>[A-Z_]+?)\));\n'
    + '  (?P<body>[^}]+?)\n'
    + '}\n')
downcast_pattern = re.compile(DOWNCAST_PATTERN, re.MULTILINE | re.DOTALL)

DOWNCAST_PATTERN2 = (
    '\n'
    + identifier_group + r' \((?P<const>const_)?gimple ' + named_identifier_group('param') + '(?P<extra_args>[^)]*?)\)\n'
    + '{\n'
    + '  (?P<check_stmt>if \(gimple_code \((?P=param)\) != (?P<gimple_code>[A-Z_]+?)\)' + '\n'
    + '    GIMPLE_CHECK \((?P=param), [A-Z_]+?\));' + '\n'
    + '  (?P<body>[^}]+?)\n'
    + '}\n')
downcast_pattern2 = re.compile(DOWNCAST_PATTERN2, re.MULTILINE | re.DOTALL)

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

        self.parse_gimple_h()

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

    def get_union_field(self, struct):
        """
        Get the name of the field for this struct within
        union gimple_statement_d
        """
        assert struct.startswith('gimple_statement_')
        specialcases = {'gimple_statement_base': 'gsbase',
                        'gimple_statement_with_ops': 'gsops',
                        'gimple_statement_with_memory_ops_base': 'gsmembase',
                        'gimple_statement_with_memory_ops': 'gsmem',
                        'gimple_statement_omp': 'omp'}
        if struct in specialcases:
            return specialcases[struct]
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
        return struct[len('gimple_statement_'):] + '_stmt'

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
            txt = f.read()
            for m in re.finditer('^DEFGSCODE\((.+?),\s+"(.+?)",\s+(.+?)\)$',
                                 txt,
                                 re.MULTILINE | re.DOTALL):
                gimple_defs.append(m.groups())
        return gimple_defs

    def parse_gimple_h(self):
        """
        Scrape out the inheritance hierarchy from gimple.h
        """
        self.parentclasses = {'gimple_statement_base' : None}
        with open('../src/gcc/gimple.h') as f:
            txt = f.read()
            pattern = (r'struct' + ws + 'GTY\(\(user\)\)' + ws
                       + identifier_group + ws + ':' + ws + 'public' + ws
                       + identifier_group + ws)
            for m in re.finditer(pattern, txt,
                                 re.MULTILINE | re.DOTALL):
                self.parentclasses[m.group(1)] = m.group(2)

    def get_parent_classes(self, struct):
        result = [struct]
        # Build in reverse order:
        while 1:
            struct = self.parentclasses[struct]
            if struct:
                result.append(struct)
            else:
                # We have the list; reverse it:
                return result[::-1]

    def get_derived_classes(self, struct):
        result = [struct]
        for cand in self.parentclasses:
            if struct == self.parentclasses[cand]:
                result.append(self.get_derived_classes(cand))
        return result

    def iter_gimple_codes(self):
        for item in self.gimple_defs:
            yield item[0]

    def get_codes_for_struct(self, struct):
        """
        Get the enum gimple_code values for which a gimple can be cast to
        the given subclass
        """
        result = []
        subclasses = self.get_derived_classes(struct)
        for gimple_code in self.iter_gimple_codes():
            struct = self.get_struct_for_gimple_code(gimple_code)
            if struct in subclasses:
                result.append(gimple_code)
        return result

def eliminate_union_access(code_, gt, subclass, param, instance_name):
    # Replace uses of  "gs->some_union" with just "some_stmt->",
    # for those unions that are within the inheritance chain of the
    # subclass being checked for.
    subclass_uses = 0

    # Some existing code unnecessarily goes through
    # gimple_statement_with_ops:
    #   "g->gsops.opbase."
    # which confuses the rewriter below.
    # It can simply be rewritten as:
    #   "g->gsbase."
    # Rewrite such uses:
    while '->gsops.opbase' in code_:
        code_ = code_.replace('->gsops.opbase.', '->gsbase.')
        subclass_uses += 1

    for parent in gt.get_parent_classes(subclass):
        #print('parent: %r' % parent)
        union_field = gt.get_union_field(parent)
        #print('union_field: %r' % union_field)
        for m2 in list(re.finditer('(%s->%s.)' % (param, union_field),
                                   code_))[::-1]:
            code_ = (code_[:m2.start()]
                     + ('%s->' % instance_name)
                     +  code_[m2.end():])
            subclass_uses += 1
    return code_, subclass_uses

def add_downcast(gt, scopes, src, pattern, is_a_helpers):
    # Potentially introduce an "as_a<>" downcast to access
    # fields of a subclass:
    changes = 0
    for m in src.finditer(pattern):
        scope = src.get_change_scope_at(m.start('body'))
        #print(scope)
        gd = m.groupdict()
        gimple_code = gd['gimple_code']
        instance_name = gt.get_instance_name(gimple_code)
        #print(instance_name)

        body = gd['body']
        param = gd['param']

        subclass = gt.get_struct_for_gimple_code(gimple_code)

        # Consider downcasting "gimple gs" to "someclass some_stmt"
        body, subclass_uses = \
            eliminate_union_access(body, gt, subclass,
                                   param, instance_name)

        # If we would need to replace any union references, convert
        # the check into a checked downcast, and perform the
        # replacement:
        if subclass_uses > 0:
            src = src.replace(m.start('body'), m.end('body'), body)
            const = 'const ' if (gd['const'] == 'const_') else ''
            replacement = ('%s%s *%s = as_a <%s%s> (%s)'
                           % (const, subclass, instance_name,
                              const, subclass, param))
            if len(replacement) > 76:
                replacement = ('%s%s *%s =\n'
                               '    as_a <%s%s> (%s)'
                               % (const, subclass, instance_name,
                                  const, subclass, param))
            src = src.replace(m.start('check_stmt'), m.end('check_stmt'),
                              replacement)
            is_a_helpers.add( (gd['const'], subclass) )
            if scope not in scopes:
                scopes[scope] = scope
            changes += 1
    return src, changes

def add_is_a_helpers(changelog, src, is_a_helpers, gt):
    m = src.search('(#undef DEFGSSTRUCT\n)')
    if m:
        helpers = ''
        for const, type_ in sorted(is_a_helpers):
            codes = gt.get_codes_for_struct(type_)
            assert codes
            if const:
                type_ = 'const ' + type_
                basetype = 'const_gimple'
            else:
                basetype = 'gimple'
            test = '|| '.join('gs->code == %s' % code_
                              for code_ in codes)
            helpers += (
                '\n'
                'template <>\n'
                'template <>\n'
                'inline bool\n'
                'is_a_helper <%s>::test (%s gs)\n'
                '{\n'
                '  return %s;\n'
                '}\n') % (type_, basetype, test)
            changelog.append('is_a_helper <%s> (%s)' % (type_, basetype),
                             'New.')
        src = src.replace(m.end(1), m.end(1),
                          helpers)
    return src

def convert_to_inheritance(clog_filename, src):
    """
    Look for code of the form:
        "->gsbase."
    followed by non-whitespace, and replace it with:
        "->"
    """
    gt = GimpleTypes()

    is_a_helpers = set()

    changelog = Changelog(clog_filename)
    scopes = OrderedDict()
    while 1:
        # Convert "gs->gsbase.somefield" to just "gs->somefield":
        m = src.search(pattern)
        if m:
            scope = src.get_change_scope_at(m.start())
            replacement = '->' + m.group(2)
            src = src.replace(m.start(), m.end(), replacement)
            if scope not in scopes:
                scopes[scope] = scope
            continue

        src, changes = add_downcast(gt, scopes, src, downcast_pattern,
                                    is_a_helpers)
        if changes:
            continue
        src, changes = add_downcast(gt, scopes, src, downcast_pattern2,
                                    is_a_helpers)
        if changes:
            continue

        m = src.search(pattern2)
        if m:
            gd = m.groupdict()
            code_ = gd['code']
            #print(code_)
            scope = src.get_change_scope_at(m.start('code'))
            if scope not in scopes:
                scopes[scope] = scope
            code_, subclass_uses = \
                eliminate_union_access(code_, gt,
                                       'gimple_statement_with_memory_ops',
                                       'g', 'mem_ops_stmt')
            #print(code_)
            if subclass_uses > 0:
                src = src.replace(m.start('code'), m.end('code'), code_)
            const = 'const ' if (gd['const'] == 'const_') else ''
            replacement = (
                '  %sgimple_statement_with_memory_ops *mem_ops_stmt =\n'
                '     dyn_cast <%sgimple_statement_with_memory_ops> (g);\n'
                '  if (!mem_ops_stmt)\n'
                '    return ' % (const, const))
            src = src.replace(m.start('cond'), m.end('cond'), replacement)
            continue

        # no matches:
        break

    src = add_is_a_helpers(changelog, src, is_a_helpers, gt)

    for scope in scopes:
        changelog.append(scope,
                         'Update for conversion of gimple types to a true class hierarchy.')

    return src.str(), changelog

if __name__ == '__main__':
    main('refactor_gimple.py', convert_to_inheritance, sys.argv,
         skip_testsuite=True)
