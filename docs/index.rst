Welcome to dasbus's documentation!
==================================

Dasbus is a DBus library written in Python 3, based on GLib and inspired by pydbus.
The code used to be part of the `Anaconda Installer <https://github.com/rhinstaller/anaconda>`_
project. It was based on the `pydbus <https://github.com/LEW21/pydbus>`_ library, but we replaced
it with our own solution because its upstream development stalled. The dasbus library is a result
of this effort.

Requirements
____________

* Python 3.6+
* PyGObject 3

You can install `PyGObject <https://pygobject.readthedocs.io>`_ provided by your system or use
PyPI. The system package is usually called ``python3-gi``, ``python3-gobject`` or ``pygobject3``.
See the `instructions <https://pygobject.readthedocs.io/en/latest/getting_started.html>`_ for
your platform (only for PyGObject, you don't need cairo or GTK).

The library is known to work with Python 3.8, PyGObject 3.34 and GLib 2.63, but these are not the
required minimal versions.

Installation
------------

Install the package from `PyPI <https://pypi.org/project/dasbus/>`_. Follow the instructions above
to install the required dependencies.

::

    pip3 install dasbus


Or install the RPM package on Fedora 31+.

::

    sudo dnf install python3-dasbus


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   Development and testing <development>
   Dasbus vs pydbus <pydbus>
   Public API <api/dasbus>
   Examples <examples>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
