#!python

import os
import shutil
import glob

dest_dir = '4Orbitit'
if not os.path.exists(dest_dir):
    os.mkdir(dest_dir)
elif not os.path.isdir(dest_dir):
    print 'error: target directory exists as file'
    exit(-1)
shutil.copy2
files = glob.glob('frh-roots*')
for fn in files:
    fd = open(fn, 'r')
    ed = {'__name__': 'readPyFile'}
    exec fd in ed
    fd.close()
    if ed['results'] != []:
	shutil.copy2(fn, dest_dir)
