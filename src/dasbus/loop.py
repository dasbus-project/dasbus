#
# Representation of an event loop
#
# Copyright (C) 2020  Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA
#
from abc import ABCMeta, abstractmethod

import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib

__all__ = [
    "AbstractEventLoop",
    "EventLoop"
]


class AbstractEventLoop(metaclass=ABCMeta):
    """The abstract representation of the event loop.

    It is necessary to run the event loop to handle emitted
    DBus signals or incoming DBus calls (in the DBus service).

    Example:

    .. code-block:: python

        # Create the event loop.
        loop = EventLoop()

        # Start the event loop.
        loop.run()

        # Run loop.quit() to stop.

    """

    @abstractmethod
    def run(self):
        """Start the event loop."""
        pass

    @abstractmethod
    def quit(self):
        """Stop the event loop."""
        pass


class EventLoop(AbstractEventLoop):
    """The representation of the event loop."""

    def __init__(self):
        """Create the event loop."""
        self._loop = GLib.MainLoop()

    def run(self):
        """Start the event loop."""
        self._loop.run()

    def quit(self):
        """Stop the event loop."""
        self._loop.quit()
