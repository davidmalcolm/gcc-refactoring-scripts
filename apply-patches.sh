#!/bin/bash
cd ../src-with-patches
for p in ../src/generated-patches/*.patch ;
do
  git am $p || exit 1
  python ../refactor-scripts/build_changelog_entry.py $p ChangeLog.gimple-classes || exit 2
  git add $(find -name ChangeLog.gimple-classes) || exit 3
  git commit --amend --no-edit || exit 4
done
