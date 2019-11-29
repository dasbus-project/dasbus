#
# Representation of a signal
#
# Copyright (C) 2019  Red Hat, Inc.  All rights reserved.
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

__all__ = ["Signal"]


class Signal(object):
    """Default representation of a signal."""

    __slots__ = [
        "_callbacks",
        "__weakref__"
    ]

    def __init__(self):
        """Create a new signal."""
        self._callbacks = []

    def connect(self, callback):
        """Connect to a signal.

        :param callback: a function to register
        """
        self._callbacks.append(callback)

    def __call__(self, *args, **kwargs):
        """Emit a signal with the given arguments."""
        self.emit(*args, **kwargs)

    def emit(self, *args, **kwargs):
        """Emit a signal with the given arguments."""
        # The list of callbacks can be changed, so
        # use a copy of the list for the iteration.
        for callback in self._callbacks.copy():
            callback(*args, **kwargs)

    def disconnect(self, callback=None):
        """Disconnect from a signal.

        If no callback is specified, then all functions will
        be unregistered from the signal.

        If the specified callback isn't registered, do nothing.

        :param callback: a function to unregister or None
        """
        if callback is None:
            self._callbacks.clear()
            return

        try:
            self._callbacks.remove(callback)
        except ValueError:
            pass
