About
-----

**Icon Library** is a *Python 2* GTK application that makes it easy to:

* view complete icon sets
* search icon sets
* export icon sets to HTML
* check which icon names comply with the freedesktop.org Standard Icon Naming Specification
* compare icons against a range of background colours

Easy Install
------------

**Icon Library** is available for installation via Python's package manager ``pip``:

::

    pip2 install --user icon-library

Manual Install
--------------

To manually build and install the Python package, perform the following:

* clone the repository (or download the tarball at https://github.com/brbsix/icon-library/archive/master.zip)

::

    git clone 'https://github.com/brbsix/icon-library.git'

* from the repo's root directory, build the package

::

    python2 setup.py sdist clean

* install the package

::

    pip2 install --user dist/icon-library-0.0.1.tar.gz

Usage
-----

To run the application, execute ``icon-library`` or click the *Icon Library* shortcut in your desktop's application menu.

Note: The **Export HTML** button exports to *icons.html* in your home folder.

License
-------

This application was originally released by Matthew McGowan (matthew.joseph.mcgowan@gmail.com) under a LGPLv3 license. I have made a few changes and prepared it for packaging. For the original homepage, see https://launchpad.net/icon-library.
