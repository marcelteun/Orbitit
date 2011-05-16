import glob
import shutil

files = glob.glob('frh-roots-*-fld_star*')
for fn in files:
    nfn = fn.replace('fld_star', 'fld_shell')
    shutil.move(fn, nfn)

files = glob.glob('frh-roots-*star-opp*')
for fn in files:
    nfn = fn.replace('star-opp', 'shell-opp')
    shutil.move(fn, nfn)

files = glob.glob('frh-roots-opp.*star.py')
for fn in files:
    nfn = fn.replace('star.py', 'shell.py')
    shutil.move(fn, nfn)

files = glob.glob('frh-roots-*.py')
for fn in files:
    nfn = fn.replace('star', 'shell', 3)
    shutil.move(fn, nfn)

