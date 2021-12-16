from distutils.core import setup
setup(
    name = 'orbitit',
    packages = ['orbitit'],
    version = '0.4',
    license='GNU Public License version 2',
    description = 'Program for modelling polyhedra',
    author = 'Marcel "Teun" Tunnissen',
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
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
    ],
)
