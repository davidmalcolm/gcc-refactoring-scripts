from collections import namedtuple, Counter
import os.path
from pprint import pprint
import re
import sys

from refactor_gimple import GimpleTypes

SRCDIR = '../src/gcc'
def get_gimple_h():
    with open(os.path.join(SRCDIR, 'gimple.h')) as f:
        srctext = f.read()
    return srctext

GA_FIELDS = (
    'line',
    'returntype',
    'symbol',
    'paramtypes')

class GimpleAccessor(namedtuple('GimpleAccessor',
                                tuple(GA_FIELDS))):
    @classmethod
    def get_all(cls):
        """
        Parse gimple.h and yield a sequence of GimpleAccessor instances
        """
        for line, returntype, symbol, params in cls._find_lines():
            ga = cls._parse_re_result(line, returntype, symbol, params)
            yield ga

    @classmethod
    def _find_lines(cls):
        """
        Yield a sequence of (return-type, symbol, partial-params) tuples
        """
        for line in get_gimple_h().splitlines():
            # Locate decls where the return type precedes it on its line:
            m = re.match(r'^([_A-Za-z0-9]+) (gimple_[_A-Za-z0-9]+) \((.*)$', line)
            if m:
                yield tuple([line] + list(m.groups()))

            # and those where the return type is not present:
            m = re.match(r'^(gimple_[_A-Za-z0-9]+) \((.*)$', line)
            if m:
                yield tuple([line, None] + list(m.groups()))

    @classmethod
    def _parse_re_result(cls, line, returntype, symbol, params):
        if params.endswith(');'):
            params = params[:-2]
        if params.endswith(','):
            params = params[:-1]
        paramtypes = []
        for paramdecl in params.strip().split(','):
            if paramdecl == 'const char *':
                paramtypes.append(paramdecl)
            else:
                m = re.match(r'(.+\*)(\S+)', paramdecl)
                if m:
                    if 0:
                        print('%r : %r' % (paramdecl, m.groups()))
                    paramtypes.append(m.group(1).strip())
                else:
                    words = paramdecl.split()
                    paramtypes.append(' '.join(words[:-1]))
        return GimpleAccessor(line, returntype, symbol, paramtypes)

    def is_builder(self):
        return self.symbol.startswith('gimple_build_')

    def is_accessor(self):
        return (self.symbol.startswith('gimple_')
                and not (self.symbol.startswith('gimple_seq')
                         or self.symbol.startswith('gimple_build_')
                         or self.symbol.startswith('gimple_alloc_')))

    def get_prefix(self, accessor_prefixes):
        for prefix in accessor_prefixes:
            if ga.symbol.startswith(prefix):
                return prefix
        if ga.symbol.startswith('gimple_omp_'):
            return 'gimple_omp_'
        raise ValueError(self)

    def get_constless_first_param(self):
        paramtype = self.paramtypes[0]
        if paramtype.startswith('const_'):
            paramtype = paramtype[len('const_'):]
        if paramtype.startswith('const '):
            paramtype = paramtype[len('const '):]
        return paramtype

    def __hash__(self):
        return hash(self.symbol)

    def __eq__(self, other):
        return self.symbol == other.symbol

    def __ne__(self, other):
        return self.symbol != other.symbol

def print_title(text):
    print(text)
    print('-' * len(text))

def println():
    sys.stdout.write('\n')

SHOW_FULL = 0

def report(gas, title, pred):
    subset = filter(pred, gas)
    if SHOW_FULL:
        print_title('%s: %s' % (title, len(subset)))
        for ga in subset:
            print('  %s' % ga.line)
        print
    else:
        # just a summary
        print('%s: %s' % (title, len(subset)))
    return subset

gas = sorted(set(list(GimpleAccessor.get_all())),
             lambda ga1, ga2: cmp(ga1.symbol, ga2.symbol))
if 0:
    for ga in gas:
        print(ga)
        print('  is_builder: %r' % ga.is_builder())
        print('  is_accessor: %r' % ga.is_accessor())
        #print('  get_prefix: %r' % ga.get_prefix())
        print('  get_constless_first_param: %r' % ga.get_constless_first_param())

NOT_TO_BE_CONVERTED = set(['gimple_assign_cast_p',
                           'gimple_assign_copy_p',
                           'gimple_assign_load_p',
                           'gimple_assign_single_p',
                           'gimple_assign_ssa_name_copy_p',
                           'gimple_assign_unary_nop_p',
                           'gimple_bb',
                           'gimple_block',
                           'gimple_clobber_p',
                           'gimple_code',
                           'gimple_copy',
                           'gimple_could_trap_p_1',
                           'gimple_could_trap_p',
                           'gimple_debug_bind_p',
                           'gimple_debug_source_bind_p',
                           'gimple_do_not_emit_location_p',
                           'gimple_expr_code',
                           'gimple_expr_type',
                           'gimple_filename',
                           'gimple_get_lhs',
                           'gimple_has_lhs',
                           'gimple_has_location',
                           'gimple_has_mem_ops',
                           'gimple_has_ops',
                           'gimple_has_side_effects',
                           'gimple_has_substatements',
                           'gimple_has_volatile_ops',
                           'gimple_in_transaction',
                           'gimple_init_singleton',
                           'gimple_lineno',
                           'gimple_location',
                           'gimple_location_ptr',
                           'gimple_location_safe',
                           'gimple_modified_p',
                           'gimple_no_warning_p',
                           'gimple_nop_p',
                           'gimple_num_ops',
                           'gimple_op',
                           'gimple_op_ptr',
                           'gimple_ops',
                           'gimple_plf',
                           'gimple_references_memory_p',
                           'gimple_set_bb',
                           'gimple_set_block',
                           'gimple_set_do_not_emit_location',
                           'gimple_set_has_volatile_ops',
                           'gimple_set_lhs',
                           'gimple_set_location',
                           'gimple_set_modified',
                           'gimple_set_no_warning',
                           'gimple_set_num_ops',
                           'gimple_set_op',
                           'gimple_set_plf',
                           'gimple_set_uid',
                           'gimple_set_use_ops',
                           'gimple_set_vdef',
                           'gimple_set_visited',
                           'gimple_set_vuse',
                           'gimple_statement_structure',
                           'gimple_stmt_max_uid',
                           'gimple_store_p',
                           'gimple_uid',
                           'gimple_use_ops',
                           'gimple_vdef',
                           'gimple_vdef_ptr',
                           'gimple_visited_p',
                           'gimple_vuse',
                           'gimple_vuse_ptr',
                       ])
report(gas,
       'TODO: Builder calls still returning a plain gimple',
       lambda ga: ga.is_builder() and ga.returntype == 'gimple')

report(gas,
       'TODO: Accessors not yet converted to taking a gimple',
       lambda ga: (ga.paramtypes[0] in ('gimple', 'const_gimple')
                   and ga.is_accessor()
                   and ga.symbol not in NOT_TO_BE_CONVERTED))

report(gas,
       'DONE: Builder calls converted to returning a gimple subclass',
       lambda ga: ga.is_builder() and ga.returntype != 'gimple')

report(gas,
       'DONE: Accessors converted to taking a gimple subclass',
       lambda ga: ((ga.paramtypes[0].startswith('gimple_')
                    or ga.paramtypes[0].startswith('const_gimple_'))
                   and ga.is_accessor()))

report(gas,
       'NOTE: Accessors known not to need to be converted',
       lambda ga: ga.symbol in NOT_TO_BE_CONVERTED)

println()

gt = GimpleTypes()
gimple_type_names = gt.get_gimple_type_names()
#pprint(sorted(gimple_type_names))

accessor_prefixes = gt.get_accessor_prefixes()

accessors = {}
for ga in gas:
    if ga.is_accessor() and ga.symbol not in NOT_TO_BE_CONVERTED:
        prefixtype = ga.get_prefix(accessor_prefixes)
        if prefixtype in accessors:
            accessors[prefixtype].add(ga)
        else:
            accessors[prefixtype] = set([ga])
#pprint(accessors)

stats = Counter()
for prefixtype in sorted(accessors.keys()):
    if prefixtype is None:
        prefixtype = 'gimple_omp_'
    prefix_accessors = sorted(accessors[prefixtype])
    done = len([ga for ga in prefix_accessors
                if ga.get_constless_first_param() != 'gimple'])
    todo = len([ga for ga in prefix_accessors
                if ga.get_constless_first_param() == 'gimple'])
    percentage = (done * 100) / (done + todo)
    stats[prefixtype] = (percentage, prefixtype, done, todo)

def print_table(stats):
    print_title('Accessors "concretized" by prefix')
    def print_row(percentage, prefixtype, done, todo):
        print('%3s %30s %5s %5s' % (percentage, prefixtype, done, todo))
    print_row('%', 'Prefix', 'DONE', 'TODO')
    for key, value in stats.most_common():
        percentage, prefixtype, done, todo = value
        print_row(percentage, prefixtype, done, todo)

print_title('Statement subclasses where all accessors are fully-concrete')
for key in sorted(stats.keys()):
    percentage, prefixtype, done, todo = stats[key]
    if todo == 0:
        print('%s (%i accessors)' % (prefixtype, done))
println()

print_table(stats)
println()
