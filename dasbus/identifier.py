#
# Identification of DBus objects, interfaces and services
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
from dasbus.namespace import get_dbus_path, get_dbus_name

__all__ = [
    'DBusInterfaceIdentifier',
    'DBusObjectIdentifier',
    'DBusServiceIdentifier'
]


class DBusBaseIdentifier(object):
    """A base identifier."""

    def __init__(self, namespace, basename=None):
        """Create an identifier.

        :param namespace: a sequence of strings
        :param basename: a string with the base name or None
        """
        if basename:
            namespace = (*namespace, basename)

        self._namespace = namespace
        self._name = get_dbus_name(*namespace)
        self._path = get_dbus_path(*namespace)

    @property
    def namespace(self):
        """DBus namespace of this object."""
        return self._namespace

    def __str__(self):
        """Return the string representation."""
        return self._name


class DBusInterfaceIdentifier(DBusBaseIdentifier):
    """Identifier of a DBus interface."""

    def __init__(self, namespace, basename=None, interface_version=None):
        """Describe a DBus interface.

        :param namespace: a sequence of strings
        :param basename: a string with the base name or None
        :param interface_version: a version of the interface
        """
        super().__init__(namespace, basename=basename)
        self._interface_version = interface_version

    def _version_to_string(self, version):
        """Convert version to a string.

        :param version: a number or None
        :return: a string
        """
        if version is None:
            return ""

        return str(version)

    @property
    def interface_name(self):
        """Full name of the DBus interface."""
        return self._name + self._version_to_string(self._interface_version)

    def __str__(self):
        """Return the string representation."""
        return self.interface_name


class DBusObjectIdentifier(DBusInterfaceIdentifier):
    """Identifier of a DBus object."""

    def __init__(self, namespace, basename=None, interface_version=None,
                 object_version=None):
        """Describe a DBus object.

        :param namespace: a sequence of strings
        :param basename: a string with the base name or None
        :param interface_version: a version of the DBus interface
        :param object_version: a version of the DBus object
        """
        super().__init__(namespace, basename=basename,
                         interface_version=interface_version)
        self._object_version = object_version

    @property
    def object_path(self):
        """Full path of the DBus object."""
        return self._path + self._version_to_string(self._object_version)

    def __str__(self):
        """Return the string representation."""
        return self.object_path


class DBusServiceIdentifier(DBusObjectIdentifier):
    """Identifier of a DBus service."""

    def __init__(self, message_bus, namespace, basename=None,
                 interface_version=None, object_version=None,
                 service_version=None):
        """Describe a DBus service.

        :param message_bus: a message bus
        :param namespace: a sequence of strings
        :param basename: a string with the base name or None
        :param interface_version: a version of the DBus interface
        :param object_version: a version of the DBus object
        :param service_version: a version of the DBus service
        """
        super().__init__(namespace, basename=basename,
                         interface_version=interface_version,
                         object_version=object_version)

        self._service_version = service_version
        self._message_bus = message_bus

    @property
    def message_bus(self):
        """Message bus of the DBus service.

        :return: a message bus
        :rtype: an instance of the MessageBus class
        """
        return self._message_bus

    @property
    def service_name(self):
        """Full name of a DBus service."""
        return self._name + self._version_to_string(self._service_version)

    def __str__(self):
        """Return the string representation."""
        return self.service_name

    def _choose_object_path(self, object_id):
        """Choose an object path."""
        if object_id is None:
            return self.object_path

        if isinstance(object_id, DBusObjectIdentifier):
            return object_id.object_path

        return object_id

    def _choose_interface_name(self, interface_id):
        """Choose an interface name."""
        if interface_id is None:
            return None

        if isinstance(interface_id, DBusInterfaceIdentifier):
            return interface_id.interface_name

        return interface_id

    def get_proxy(self, object_path=None, interface_name=None,
                  **bus_arguments):
        """Returns a proxy of the DBus object.

        If no object path is specified, we will use the object path
        of this DBus service.

        If no interface name is specified, we will use none and create
        a proxy from all interfaces of the DBus object.

        :param object_path: an object identifier or a DBus path or None
        :param interface_name: an interface identifier or a DBus name or None
        :param bus_arguments: additional arguments for the message bus
        :return: a proxy object
        """
        object_path = self._choose_object_path(object_path)
        interface_name = self._choose_interface_name(interface_name)

        return self._message_bus.get_proxy(
            self.service_name,
            object_path,
            interface_name,
            **bus_arguments
        )
