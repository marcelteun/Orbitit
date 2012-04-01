#!/usr/bin/python

import glob
import os
import shutil
import sys

if len(sys.argv) > 1:
    dstDir = sys.argv[1]
else:
    dstDir = "4Orbitit"

if len(sys.argv) > 2:
    srcDir = sys.argv[2]
else:
    srcDir = "."

try:
    os.mkdir(dstDir)
except OSError:
    if not os.path.isdir(dstDir):
        print 'error: target directory exists as file'
        exit(-1)

fl = glob.glob("%s/frh-roots-*.py" % srcDir)
nrFiles = len(fl)
nrSols = 0
nrEmptyFiles = 0
for fn in fl:
    fd = open(fn, 'r')
    ed = {'__name__': 'readPyFile'}
    exec fd in ed
    fd.close()
    if len(ed['results']) > 0:
        nrSols += len(ed['results'])
        if os.path.islink(fn):
            linkto = os.readlink(fn)
            lp = "%s/%s" % (dstDir, fn)
            try:
                os.symlink(linkto, lp)
            except OSError:
                os.remove(lp)
                os.symlink(linkto, lp)
        else:
            shutil.copy2(fn, dstDir)
    else:
        # TODO: make optional: to do something here..., e.g. rm
        nrEmptyFiles += 1

print '%d solutions found in %d files' % (nrSols, nrFiles - nrEmptyFiles)
print '  (excl. %d files without any solutions)' % nrEmptyFiles
