## License

With this program you can interactively investigate some polyhedra. I use this
program myself and I am willing to share it with other who are interested. I use
Ubuntu, as a consequence some problems might exist with windows.

Copyright (C) 2021 Marcel Tunnissen
http://www.tunnissen.eu

License: GPLv2, see LICENCSE.txt

## Run in a Virtual Environment

It is recommended to run in a virtual environment, e.g. by using
[uv](https://docs.astral.sh/uv/guides/)

As listed below, one of the requirements is wxPython. Installing this through
`pip` will try to compile the source code and this will require certain
packages to be installed. It is easier to just use a pre-compiled package, see
section [wxPython](#wxPython) below.

## If You Install through PyPI (pip install)

Also here it is important to have the correct packages for building wxPython
installed. See section [wxPython](wxPython)" below.

### Install
`pip install orbitit`

### Run
`python -m orbitit`

## If You Downloaded from Github Directly

### Requirements

You will need:
1. python 3.x:  http://www.python.org
2. wxPython: http://www.wxpython.org
3. pyOpenGL: http://pyopengl.sourceforge.net/

### Install

E.g. for Ubuntu or other Debian based Linux dist:
`sudo apt-get install python3 python3-pip`

Then use pip to install other packages, e.g:
`pip3 install python-config`
`pip3 install attrdict3`
`pip3 install pyopengl`

As mentioned `wxpython` is needed as well, again see section
[wxPython](#wxPython) for more about installing wxPython through pip.

## wxPython

I chose wxPython over Tk, for several reasons. The main one was that I ran into
quite some preformance problems with Tk. The disadvantage is that it can be a
pain to install wxPython especially through pip in a virtual environment. Some
might want to skip the virtual evironment and install and use wxPython from
inside the OS instead.

When wxPython is installed through pip the standard way it is compiled. This
can take quite some time (e.g. more than 15 minutes) and it can be quite
cumbersome. It is easier to check whether there is a pre-compiled version
available for your OS [here](https://extras.wxpython.org/wxPython4/extras)

For instance for Ubuntu 24 LTS one can install a pre-compiled version through:
`pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-24.04/ wxPython`

This is quicker and much easier. You do need to make sure you have certain
libraries installed on your OS. E.g. if you start the program on Ubuntu 24 LTS
and you get:
`File "/home/marceltn/self/fromGitHub/Orbitit/.venv/lib/python3.14/site-packages/wx/core.py", line 12, in <module>
  from ._core import *
ImportError: libSDL2-2.0.so.0: cannot open shared object file: No such file or directory`

Then you will need to install the package `libsdl2-2.0-0` through `apt-get install`.

### Install by Compiling

Below follows some tips if you decide to compile your own version by just
running `pip install wxpython`.
Make sure that you have the right packages installed. You will need a a
C-compiler at least.
For a Debian Linux you would need have installed (e.g.
through apt-get) the packages
 - build-essential
 - libgtk-3-dev and libwxgtk3.0-gtk3-dev (or whathever GTK version you are using)
 - python3-dev
 - libgl1-mesa-glx libglu1-mesa

For Ubuntu I also did:
`sudo apt-get install python3-dev`
I am not sure whether this was needed.

If the build fails during install the directory with the files is deleted
again. To investigate the problem it is better to download the
tar.gz file, e.g. by
`pip3 download --no-deps wxpython`
Then
`tar xzf wxPython-x.y.z.tar.gz`
`cd wxPython-x.y.z`
`python3 build.py build`

See, this (reference)[https://stackoverflow.com/questions/58712734/how-to-fix-testing-pyext-configuration-could-not-build-python-extensions]

Now the log file is saved (the standard-out tells where, usually in red) and you
can try to solve one issue, and then continue the build without loosing files
that were build already etc.

Once everything you fixed the problem you can create a wheel file in that
directory:
`pip wheel .`
Then you can install the resulting wheel files with:
`pip install wxPython-x.y.z.whl`

One problem can be that the python environment wasn't build with
--enable-shared. Another problem can be that Python.h isn't found.

When I tried compiling myself I was also using pyenv and I needed to install
the python version as follows:
`CONFIGURE_OPTS=--enable-shared pyenv install 3.10-dev`
which will try to fetch Python development files directly from github, compile
and install, see
(reference)[https://stackoverflow.com/questions/45680681/installing-python-dev-in-virtualenv]

Then I created and activated an environment with that:
`pyenv virtualenv 3.10-dev orbitit-py3.10`
`pyenv activate orbitit-py3.10`
Unfortunately Python.h still couldn't be found, because the include directory
for that pyenv was still empty:
`$ python-config --prefix`
`/my-home/.pyenv/versions/3.10-dev/envs/orbitit-3.10`
Then
`$ ls -l /my-home/.pyenv/versions/3.10-dev/envs/orbitit-3.10/include/`
Showed an empty directory

However
`$ ls /my-home/.pyenv/versions/3.10-dev/include/`
Did have
`python3.10`

Once I copied the contents:
`scp -r /my-home/.pyenv/versions/3.10-dev/include/python3.10 /my-home/.pyenv/versions/3.10-dev/envs/orbitit-3.10/include/`
Python.h could be found. I am not sure why this didn't work to begin with.

Some more references that might be helpful:
https://stackoverflow.com/questions/21530577/fatal-error-python-h-no-such-file-or-directory
https://stackoverflow.com/questions/74863665/pyenv-installed-python-creates-virtualenv-with-empty-include-dir-no-python-conf

Another problem I ran into was that wxPython couldn't find the share objects:
`ImportError: libwx_gtk3u_core-3.2.so.0: cannot open shared object file: No such file or directory`
As a workaround I set the `LD_LIBRARY_PATH` environment variable:
`export LD_LIBRARY_PATH=/my-home/.pyenv/versions/orbitit-3.10/lib/python3.10/site-packages/wx/`
I think there should be a better way, but I haven't found it yet.

All this was not needed when I used the pre-compiled version.

### Run
Make sure the `PYTHONPATH` points out this directory, e.g. in Linux
`export PYTHONPATH=$PWD`

Also make sure to have set the `PYOPENGL_PLATFORM` environment variable.
On my system I do
```
source ./init_env
python -m orbitit

Use "python -m orbitit -h" for more help on additional parameters. Note that you
can define an environment variable ORBITIT_LIB to point to a library with
models, e.g. the github repo orbitit-lib.
```

## Errors

### 1.
If you get problems with a context not being valid, e.g.
OpenGL.error.Error: Attempt to retrieve context when no valid context

Then this might be related to eht wrong `PYOPENGL_PLATFORM`
In my case this problem was solved by

`PYOPENGL_PLATFORM=egl python -m orbitit`

### 2.
If you get problems with NotImplementedError on GLCanvas you probably built
wxPython without the wxgtk support. See section [wxPython](#wxPython) above.
