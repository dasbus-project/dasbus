#
# Support for DBus errors
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
from dasbus.namespace import get_dbus_name

__all__ = [
    "dbus_error",
    "DBusError",
    "register",
    "ErrorRegister"
]


def dbus_error(error_name, namespace=()):
    """Define decorated class as a DBus error.

    The decorated exception class will be mapped to a DBus error.

    :param error_name: a DBus name of the error
    :param namespace: a sequence of strings
    :return: a decorator
    """
    error_name = get_dbus_name(*namespace, error_name)

    def decorated(cls):
        register.map_exception_to_name(cls, error_name)
        return cls

    return decorated


class DBusError(Exception):
    """A default DBus error."""
    pass


class ErrorRegister(object):
    """Class for mapping exceptions to DBus errors."""

    def __init__(self, default_namespace="not.known.Error",
                 default_class=DBusError):
        self._default_class = default_class
        self._default_namespace = default_namespace
        self._map = dict()
        self._reversed_map = dict()

    def map_exception_to_name(self, exception_cls, name):
        """Map the exception class to a DBus name."""
        self._map[name] = exception_cls
        self._reversed_map[exception_cls] = name

    def get_error_name(self, exception_cls):
        """Get the DBus name of the exception."""
        if exception_cls in self._reversed_map:
            return self._reversed_map.get(exception_cls)

        return "{}.{}".format(
            self._default_namespace,
            exception_cls.__name__
        )

    def get_exception_class(self, name):
        """Get the exception class mapped to the DBus name."""
        return self._map.get(name, self._default_class)


# A default register of DBus errors.
register = ErrorRegister()
