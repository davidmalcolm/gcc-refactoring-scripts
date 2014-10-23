import unittest

from refactor_gimple_patches import rename_types

class RefactoringTests(unittest.TestCase):
    def test_subject(self):
        self.assertEqual(rename_types('[PATCH 01/88] Introduce gimple_switch and use it in various places',
                                      'subject'),
                         '[PATCH 01/88] Introduce gswitch * and use it in various places')
        self.assertEqual(rename_types('[PATCH 09/88] Update ssa_prop_visit_phi_fn callbacks to take a\n gimple_phi',
                                      'subject'),
                         '[PATCH 09/88] Update ssa_prop_visit_phi_fn callbacks to take a\n gphi *')

if __name__ == '__main__':
    unittest.main()
