# -*- coding: utf-8 -*-


from setuptools import setup
from iconlibrary.core import __author__, __license__

setup(
    name='icon-library',
    version='0.0.2',
    author=' '.join(__author__.split()[:-1]),
    author_email=__author__.split()[-1].strip('<>'),
    description='Inspect installed icon themes.',
    url='https://launchpad.net/icon-library',
    license=__license__,
    keywords=['freedesktop', 'icon', 'theme'],
    packages=['iconlibrary'],
    install_requires=['Cheetah'],
    data_files=[
        ('share/applications', ['share/applications/icon-library.desktop']),
        ('share/iconlibrary', ['share/iconlibrary/export_template.html'])],
    entry_points={
        'console_scripts': ['icon-library=iconlibrary.core:main'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: System',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
)
