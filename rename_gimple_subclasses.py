#!/usr/bin/python
from collections import OrderedDict
import os
import sys

from refactor import main, Changelog
from refactor_gimple_patches import rename_types_in_src

def path_filter(path):
    return (os.path.isfile(path)
            and (path.endswith('.c') or
                 path.endswith('.h') or
                 path.endswith('gsstruct.def')))

def rename_types(clog_filename, src):
    changelog = Changelog(clog_filename)
    scopes = OrderedDict()
    src = rename_types_in_src(src, 'file-on-disk', changelog)
    return src.str(), changelog

if __name__ == '__main__':
    main('rename_gimple_subclasses.py', rename_types, sys.argv,
         skip_testsuite=True,
         path_filter=path_filter,
         clogname='ChangeLog.gimple-classes')
