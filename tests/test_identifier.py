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
import unittest
from unittest.mock import Mock

from dasbus.identifier import DBusInterfaceIdentifier, DBusObjectIdentifier, \
    DBusServiceIdentifier, DBusBaseIdentifier


class DBusIdentifierTestCase(unittest.TestCase):
    """Test DBus identifiers."""

    def assert_namespace(self, obj, namespace):
        """Check the DBus namespace object."""
        self.assertEqual(obj.namespace, namespace)

    def assert_interface(self, obj, interface_name):
        """Check the DBus interface object."""
        self.assertEqual(obj.interface_name, interface_name)

    def test_identifier(self):
        """Test the DBus identifier object."""
        identifier = DBusBaseIdentifier(
            namespace=("a", "b", "c")
        )
        self.assert_namespace(identifier, ("a", "b", "c"))

        identifier = DBusBaseIdentifier(
            basename="d",
            namespace=("a", "b", "c")
        )
        self.assert_namespace(identifier, ("a", "b", "c", "d"))

    def test_interface(self):
        """Test the DBus interface object."""
        interface = DBusInterfaceIdentifier(
            namespace=("a", "b", "c")
        )
        self.assert_namespace(interface, ("a", "b", "c"))
        self.assert_interface(interface, "a.b.c")

        interface = DBusInterfaceIdentifier(
            namespace=("a", "b", "c"),
            interface_version=1
        )
        self.assert_namespace(interface, ("a", "b", "c"))
        self.assert_interface(interface, "a.b.c1")

        interface = DBusInterfaceIdentifier(
            basename="d",
            namespace=("a", "b", "c"),
            interface_version=1
        )
        self.assert_namespace(interface, ("a", "b", "c", "d"))
        self.assert_interface(interface, "a.b.c.d1")

    def assert_object(self, obj, object_path):
        """Check the DBus object."""
        self.assertEqual(obj.object_path, object_path)

    def test_object(self):
        """Test the DBus object."""
        obj = DBusObjectIdentifier(
            namespace=("a", "b", "c")
        )
        self.assert_namespace(obj, ("a", "b", "c"))
        self.assert_interface(obj, "a.b.c")
        self.assert_object(obj, "/a/b/c")

        obj = DBusObjectIdentifier(
            namespace=("a", "b", "c"),
            object_version=2,
            interface_version=4
        )
        self.assert_namespace(obj, ("a", "b", "c"))
        self.assert_interface(obj, "a.b.c4")
        self.assert_object(obj, "/a/b/c2")

        obj = DBusObjectIdentifier(
            basename="d",
            namespace=("a", "b", "c"),
            object_version=2,
            interface_version=4
        )
        self.assert_namespace(obj, ("a", "b", "c", "d"))
        self.assert_interface(obj, "a.b.c.d4")
        self.assert_object(obj, "/a/b/c/d2")

    def assert_bus(self, obj, message_bus):
        """Check the DBus service object."""
        self.assertEqual(obj.message_bus, message_bus)

    def assert_service(self, obj, service_name):
        """Check the DBus service object."""
        self.assertEqual(obj.service_name, service_name)

    def test_service(self):
        """Test the DBus service object."""
        bus = Mock()
        service = DBusServiceIdentifier(
            namespace=("a", "b", "c"),
            message_bus=bus
        )
        self.assert_namespace(service, ("a", "b", "c"))
        self.assert_interface(service, "a.b.c")
        self.assert_object(service, "/a/b/c")
        self.assert_service(service, "a.b.c")
        self.assert_bus(service, bus)

        service = DBusServiceIdentifier(
            namespace=("a", "b", "c"),
            service_version=3,
            interface_version=5,
            object_version=7,
            message_bus=bus
        )
        self.assert_namespace(service, ("a", "b", "c"))
        self.assert_interface(service, "a.b.c5")
        self.assert_object(service, "/a/b/c7")
        self.assert_service(service, "a.b.c3")
        self.assert_bus(service, bus)

        service = DBusServiceIdentifier(
            basename="d",
            namespace=("a", "b", "c"),
            service_version=3,
            interface_version=5,
            object_version=7,
            message_bus=bus
        )
        self.assert_namespace(service, ("a", "b", "c", "d"))
        self.assert_interface(service, "a.b.c.d5")
        self.assert_object(service, "/a/b/c/d7")
        self.assert_service(service, "a.b.c.d3")
        self.assert_bus(service, bus)


class DBusServiceIdentifierTestCase(unittest.TestCase):
    """Test DBus service identifiers."""

    def test_get_proxy(self):
        """Test getting a proxy."""
        bus = Mock()
        namespace = ("a", "b", "c")

        service = DBusServiceIdentifier(
            namespace=namespace,
            message_bus=bus
        )

        obj = DBusObjectIdentifier(
            basename="object",
            namespace=namespace
        )

        service.get_proxy()
        bus.get_proxy.assert_called_with(
            "a.b.c",
            "/a/b/c",
            None
        )
        bus.reset_mock()

        service.get_proxy("/a/b/c/object")
        bus.get_proxy.assert_called_with(
            "a.b.c",
            "/a/b/c/object",
            None
        )
        bus.reset_mock()

        service.get_proxy(obj)
        bus.get_proxy.assert_called_with(
            "a.b.c",
            "/a/b/c/object",
            None
        )
        bus.reset_mock()

    def test_get_proxy_for_interface(self):
        """Test getting a proxy for an interface."""
        bus = Mock()
        namespace = ("a", "b", "c")

        service = DBusServiceIdentifier(
            namespace=namespace,
            message_bus=bus
        )

        interface = DBusInterfaceIdentifier(
            basename="interface",
            namespace=namespace
        )

        service.get_proxy(
            interface_name="a.b.c.interface"
        )
        bus.get_proxy.assert_called_with(
            "a.b.c",
            "/a/b/c",
            "a.b.c.interface"
        )
        bus.reset_mock()

        service.get_proxy(
            interface_name=interface
        )
        bus.get_proxy.assert_called_with(
            "a.b.c",
            "/a/b/c",
            "a.b.c.interface"
        )
        bus.reset_mock()

    def test_get_proxy_with_bus_arguments(self):
        """Test getting a proxy with an additional arguments."""
        bus = Mock()
        error_mapper = Mock()
        namespace = ("a", "b", "c")

        service = DBusServiceIdentifier(
            namespace=namespace,
            message_bus=bus
        )

        service.get_proxy(
            error_mapper=error_mapper
        )
        bus.get_proxy.assert_called_with(
            "a.b.c",
            "/a/b/c",
            None,
            error_mapper=error_mapper
        )
        bus.reset_mock()

        service.get_proxy(
            interface_name=service,
            error_mapper=error_mapper
        )
        bus.get_proxy.assert_called_with(
            "a.b.c",
            "/a/b/c",
            "a.b.c",
            error_mapper=error_mapper
        )
        bus.reset_mock()
