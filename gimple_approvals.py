# Build APPROVALS, a dictionary mapping Subject lines from my April 2014
# posting of the 89-patch kit to 2-tuples: URL of Jeff's approval, and
# the pertinent text by him.

APPROVALS_16_to_18 = ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00626.html',
                      """OK when prerequisites have gone in.

                      Actually that's true for #17 & #18 as well.""")

APPROVALS_21_to_30 = ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00628.html',
                      """OK after fixing up the naming/const stuff as discussed for prior patches.

                      That applies to 22-30. Make sure to take care of the pretty printers per Trevor's comments as well. He indicated those were missing in a couple of those patches.""")

APPROVALS = dict([
    ('[PATCH 02/89] Introduce gimple_switch and use it in various places',
     ('https://gcc.gnu.org/ml/gcc-patches/2014-04/msg01475.html',
      """So it sounds like Richi really prefers the explicit casting rather than member functions. It seems like a minor issue to me, so let's go with explicit casting.

      OK for the trunk with that change. Per Richi's request, please hold off until 4.9.1 goes out the door (~2 months?)""")),

    ('[PATCH 03/89] Introduce gimple_bind and use it for accessors.',
     ('https://gcc.gnu.org/ml/gcc-patches/2014-04/msg01485.html',
      "This is fine, with the same requested changes as #2; specifically using an explicit cast\n"
      "rather than hiding the conversion in a method. Once those changes are in place, it's good for 4.9.1.")),

    ('[PATCH 04/89] Introduce gimple_cond and use it in various places',
     ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00595.html',
      """This is generally fine. It needs minor tweaks due to the change in how we're handling const stuff, but otherwise it looks ready to go.

      So, once you've flushed the queue of dependencies and reworked this to fit into the new world order, it's OK for the trunk. Please post the final version for archival purposes.""")),

    ('[PATCH 05/89] Introduce gimple_assign and use it in various places',
     ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00596.html',
      "Similar to the gimple_cond patch. Update for the changes in the prerequisites and it's good to go. Please post final version for archival purposes.")),

    ('[PATCH 06/89] Introduce gimple_label and use it in a few places',
     ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00597.html',
      'Same as prior patches for gimple_cond and gimple_assign.')),

    ('[PATCH 07/89] Introduce gimple_debug and use it in a few places',
     ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00598.html',
      'Same as prior patches.')),

    ('[PATCH 08/89] Introduce gimple_phi and use it in various places',
     ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00618.html',
      "Same as prior patches in this set. Just get the const/renaming stuff addressed and it's good to go.")),

    ('[PATCH 09/89] Introduce gimple_phi_iterator',
     ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00630.html',
      'OK once prerequisites have gone in.')),

    ('[PATCH 10/89] Update ssa_prop_visit_phi_fn callbacks to take a gimple_phi',
     ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00619.html',
      'OK when prerequisites have gone in.')),

    ('[PATCH 11/89] tree-parloops.c: use gimple_phi in various places',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00620.html',
       'OK when prerequisites have gone in.')),

    ('[PATCH 12/89] tree-predcom.c: use gimple_phi in various places',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00621.html',
       'OK when prerequisites have gone in.')),

    ('[PATCH 13/89] tree-ssa-phiprop.c: use gimple_phi',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00622.html',
       'OK when prerequisites have gone in.')),

    ('[PATCH 14/89] tree-ssa-loop-niter.c: use gimple_phi in a few places',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00623.html',
       'OK when prerequisites have gone in.')),

    ('[PATCH 15/89] tree-ssa-loop-manip.c: use gimple_phi in three places',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00625.html',
       'OK when prerequisites have gone in.')),

    ('[PATCH 16/89] tree-ssa-loop-ivopts.c: use gimple_phi in a few places',
     APPROVALS_16_to_18),
    ('[PATCH 17/89] Update various expressions within tree-scalar-evolution.c to be gimple_phi',
     APPROVALS_16_to_18),
    ('[PATCH 18/89] Concretize get_loop_exit_condition et al to working on gimple_cond',
     APPROVALS_16_to_18),

    # FIXME: patch 19/89?
    # approval was: https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00558.html
    # Re: [PATCH 19/89] Const-correctness of gimple_call_builtin_p
    # """This is fine per my prior pre-approval of const-correctness changes of this nature."""

    ('[PATCH 20/89] Introduce gimple_call',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00633.html',
       'OK once the const/renaming changes are done.')),

    ('[PATCH 21/89] Introduce gimple_return',
     APPROVALS_21_to_30),
    ('[PATCH 22/89] Introduce gimple_goto',
     APPROVALS_21_to_30),
    ('[PATCH 23/89] Introduce gimple_asm',
     APPROVALS_21_to_30),
    ('[PATCH 24/89] Introduce gimple_transaction',
     APPROVALS_21_to_30),
    ('[PATCH 25/89] Introduce gimple_catch',
     APPROVALS_21_to_30),
    ('[PATCH 26/89] Introduce gimple_eh_filter',
     APPROVALS_21_to_30),
    ('[PATCH 27/89] Introduce gimple_eh_must_not_throw',
     APPROVALS_21_to_30),
    ('[PATCH 28/89] Introduce gimple_eh_else',
     APPROVALS_21_to_30),
    ('[PATCH 29/89] Introduce gimple_resx',
     APPROVALS_21_to_30),
    ('[PATCH 30/89] Introduce gimple_eh_dispatch',
     APPROVALS_21_to_30),

    ('[PATCH 31/89] Use subclasses of gimple in various places',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00634.html',
       'OK once any prerequisites are in and any renaming done.')),

    ('[PATCH 32/89] Introduce gimple_try',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00636.html',
       'OK once const and associated renaming stuff is fixed.')),

    ('[PATCH 33/89] Use more concrete types for various gimple statements',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00801.html',
       'OK after prerequisites have gone in.')),

    ('[PATCH 34/89] Introduce gimple_omp_atomic_load',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00802.html',
       """OK with expected changes due to renaming/updates to const handling.

       Please repost the final patch for archival purposes.""")),

    ('[PATCH 35/89] Introduce gimple_omp_atomic_store',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00804.html',
       """OK with expected changes due to renaming/updates to const handling.

       Please repost the final patch for archival purposes.""")),

    ('[PATCH 36/89] Introduce gimple_omp_continue',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00826.html',
       """OK with expected changes due to renaming/updates to const handling.

       Please repost the final patch for archival purposes.""")),

    ('[PATCH 37/89] Introduce gimple_omp_critical',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00809.html',
       """OK with expected changes due to renaming/updates to const handling.

       Please repost the final patch for archival purposes.""")),

    ('[PATCH 38/89] Introduce gimple_omp_for',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00825.html',
       """OK with expected changes due to renaming/updates to const handling.

       Please repost the final patch for archival purposes.""")),

    ('[PATCH 39/89] Introduce gimple_omp_parallel',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00827.html',
       """OK with expected changes due to renaming/updates to const handling.

       Please repost the final patch for archival purposes.""")),

    ('[PATCH 40/89] tree-cfg.c: Make verify_gimple_call require a gimple_call',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00805.html',
       'OK when prerequisites have gone in.')),

    ('[PATCH 41/89] Introduce gimple_omp_task',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00806.html',
       """OK with expected changes due to renaming/updates to const handling.

       Please repost the final patch for archival purposes.""")),

    ('[PATCH 42/89] Introduce gimple_omp_single',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00807.html',
       """OK with expected changes due to renaming/updates to const handling.

       Please repost the final patch for archival purposes.""")),

    ('[PATCH 43/89] Introduce gimple_omp_target',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00823.html',
       """OK with expected changes due to renaming/updates to const handling.

       Please repost the final patch for archival purposes.""")),

    ('[PATCH 44/89] Introduce gimple_omp_teams',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00808.html',
       """OK with expected changes due to renaming/updates to const handling.

       Please repost the final patch for archival purposes.""")),

    ('[PATCH 45/89] Introduce gimple_omp_sections',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00821.html',
       """OK with expected changes due to renaming/updates to const handling.

       Please repost the final patch for archival purposes.""")),

    ('[PATCH 46/89] tree-parloops.c: Use gimple_phi in various places',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00819.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 47/89] omp-low.c: Use more concrete types of gimple statement for various locals',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00810.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 48/89] Make gimple_phi_arg_def_ptr and gimple_phi_arg_has_location require a gimple_phi',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00828.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 49/89] Make add_phi_arg require a gimple_phi',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00876.html',
       'Fine once prereqs go in.')),

    ('[PATCH 50/89] Make gimple_phi_arg_set_location require a gimple_phi',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00811.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 51/89] Update GRAPHITE to use more concrete gimple statement classes',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00868.html',
       'OK once prereqs go in.')),

    ('[PATCH 52/89] Make gimple_phi_arg_edge require a gimple_phi',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00877.html',
       'Fine once prereqs go in.')),

    ('[PATCH 53/89] More gimple_phi',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00812.html',
       'Ok once prerequisites have gone in.')),

    ('[PATCH 54/89] Make gimple_call_return_slot_opt_p require a gimple_call.',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00829.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 55/89] Use gimple_call for callgraph edges',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00867.html',
       'OK once prereqs go in.')),

    ('[PATCH 56/89] Various gimple to gimple_call conversions in IPA',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00857.html',
       'OK once prereqs go in.')),

    ('[PATCH 57/89] Concretize parameter to gimple_call_copy_skip_args',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00813.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 58/89] Make gimple_label_set_label require a gimple_label',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00814.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 59/89] Make gimple_goto_set_dest require a gimple_goto',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00815.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 60/89] Concretize gimple_catch_types',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00816.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 61/89] Concretize gimple_call_use_set and gimple_call_clobber_set',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00817.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 62/89] Concretize gimple_label_label',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00878.html',
       'OK once prereqs go in.')),

    ('[PATCH 63/89] Concretize gimple_eh_filter_set_types and gimple_eh_filter_set_failure',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00830.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 64/89] Concretize gimple_try_set_catch_is_cleanup',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00818.html',
       'OK after prerequisites have gone in.')),

    ('[PATCH 65/89] Concretize three gimple_try_set_ accessors',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00831.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 66/89] Make gimple_phi_arg_location_from_edge require a gimple_phi',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00833.html',
       'OK once prerequisites have gone in')),

    ('[PATCH 67/89] Make gimple_phi_arg_location require a gimple_phi.',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00848.html',
       'OK once prerequisites go in.')),

    ('[PATCH 68/89] Concretize three gimple_return_ accessors',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00865.html',
       'Fine once prereqs go in.')),

    ('[PATCH 69/89] Make gimple_cond_set_{true|false}_label require gimple_cond.',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00835.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 70/89] Concretize locals within expand_omp_for_init_counts',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00836.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 71/89] Concretize gimple_cond_make_{false|true}',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00863.html',
       'OK once prerequisites go in.')),
    # though see discussion in:
    #   https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00872.html
    #     https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00886.html

    ('[PATCH 72/89] Concretize gimple_switch_index and gimple_switch_index_ptr',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00860.html',
       'OK once prereqs go in and will obviously need updating for const changes as well.')),

    ('[PATCH 73/89] Concretize gimple_cond_{true|false}_label',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00845.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 74/89] Concretize gimple_cond_set_code',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00849.html',
       'Fine once prerequisites go in.')),

    ('[PATCH 75/89] Concretize gimple_cond_set_{lhs|rhs}',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00850.html',
       'OK once prereqs go in.')),

    ('[PATCH 76/89] Concretize gimple_cond_{lhs|rhs}_ptr',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00851.html',
       'OK when prereqs go in.')),

    ('[PATCH 77/89] Concretize various expressions from gimple to gimple_cond',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00858.html',
       'OK once prereqs go in.')),

    ('[PATCH 78/89] Concretize gimple_call_set_nothrow',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00837.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 79/89] Concretize gimple_call_nothrow_p',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00844.html',
       'OK once prerequisites have gone in.')),

    ('[PATCH 80/89] Tweak to gimplify_modify_expr',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00842.html',
       'OK once prerequisites have gone in.')),

    # why two 82/89?
    # what happened to 81/89?

    ('[PATCH 82/89] Concretize gimple_call_set_fntype',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00840.html',
       'This is fine once prerequisites have gone in.')),

    ('[PATCH 83/89] Concretize gimple_call_set_tail and gimple_call_tail_p',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00859.html',
       'OK once prereqs go in.')),

    ('[PATCH 84/89] Concretize gimple_call_arg_flags',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00838.html',
       'This is fine, but will need tweaking once the const changes go in. The final form is approved given its triviality, but please post for archival purposes.')),

    ('[PATCH 85/89] Concretize gimple_assign_nontemporal_move_p',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00853.html',
       'OK when prereqs have gone in.')),

    ('[PATCH 86/89] Concretize gimple_call_copy_flags and ipa_modify_call_arguments',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00855.html',
       'OK when prereqs go in.')),

    ('[PATCH 87/89] Use gimple_call in some places within tree-ssa-dom.c',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00856.html',
       'OK when prereqs go in.')),

    ('[PATCH 88/89] Use gimple_phi in many more places.',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00879.html',
       'Fine once prereqs go in.')),

    ('[PATCH 89/89] Convert various gimple to gimple_phi within ssa-iterators.h',
      ('https://gcc.gnu.org/ml/gcc-patches/2014-05/msg00861.html',
       'OK once prereq go in.')),
])


