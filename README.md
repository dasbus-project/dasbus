# dasbus
This DBus library is written in Python 3, based on GLib and inspired by pydbus.

The code used to be part of the [Anaconda Installer](https://github.com/rhinstaller/anaconda)
project. It was based on the [pydbus](https://github.com/LEW21/pydbus) library, but we replaced
it with our own solution because of its inactivity. The dasbus library is a result of this effort.

## Requirements

* Python 3.6+
* PyGObject 3

You can install [PyGObject](https://pygobject.readthedocs.io) provided by your system or use PyPI.
The system package is usually called `python3-gi`, `python3-gobject` or `pygobject3`. See the
[instructions](https://pygobject.readthedocs.io/en/latest/getting_started.html) for your platform
(only for PyGObject, you don't need cairo or GTK).

The library is known to work with Python 3.8, PyGObject 3.34 and GLib 2.63, but these are not the
required minimal versions.
