#
# Client support for DBus properties
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

__all__ = ["PropertyProxy"]


class PropertyProxy(object):
    """Proxy of a remote DBus property.

    It can be used to define instance attributes.
    """

    __slots__ = [
        "_getter",
        "_setter"
    ]

    def __init__(self, getter, setter):
        """Create a new proxy of the DBus property."""
        self._getter = getter
        self._setter = setter

    def get(self):
        """Get the value of the DBus property."""
        return self.__get__(None, None)

    def __get__(self, instance, owner):
        if instance is None and owner:
            return self

        if not self._getter:
            raise AttributeError(
                "Can't read DBus property."
            )

        return self._getter()

    def set(self, value):
        """Set the value of the DBus property."""
        return self.__set__(None, value)

    def __set__(self, instance, value):
        if not self._setter:
            raise AttributeError(
                "Can't set DBus property."
            )

        return self._setter(value)
