from distutils.core import setup

with open("README", "r", encoding="utf-8") as fd:
    long_description = fd.read()

setup(
    name = 'orbitit',
    version = '0.5.4',
    license='GNU Public License version 2',
    description = 'Utility for modelling polyhedra',
    long_description=long_description,
    author = 'marcelteun',
    author_email = 'marcelteun@gmail.com',
    url = 'https://github.com/marcelteun/Orbitit',
    download_url = 'https://github.com/marcelteun/Orbitit/archive/refs/tags/0.4.0.zip',
    keywords = ['orbitit', 'polyhedra', 'heptagons'],
    install_requires=[
        'python-config',
        'wxPython>=4.0.0',
        'pyopengl',
    ],
    classifiers=[
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 3',
    ],
    packages=["orbitit"],
    python_requires=">=3.6",
)
