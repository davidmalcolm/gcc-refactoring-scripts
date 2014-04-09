from collections import namedtuple
import os.path
import re

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
                words = paramdecl.split()
                paramtypes.append(words[0])
        return GimpleAccessor(line, returntype, symbol, paramtypes)

    def is_builder(self):
        return self.symbol.startswith('gimple_build_')

    def is_accessor(self):
        return (self.symbol.startswith('gimple_')
                and not (self.symbol.startswith('gimple_seq')
                         or self.symbol.startswith('gimple_build_')))

    def __hash__(self):
        return hash(self.symbol)

    def __eq__(self, other):
        return self.symbol == other.symbol

    def __ne__(self, other):
        return self.symbol != other.symbol

def print_title(text):
    print(text)
    print('-' * len(text))

def report(gas, title, pred):
    subset = filter(pred, gas)
    print_title('%s: %s' % (title, len(subset)))
    for ga in subset:
        print('  %s' % ga.line)
    print

gas = sorted(set(list(GimpleAccessor.get_all())),
             lambda ga1, ga2: cmp(ga1.symbol, ga2.symbol))
#for ga in gas:
#    print(ga)

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
