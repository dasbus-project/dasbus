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
from collections import defaultdict
from unittest.mock import Mock, patch

from dasbus.connection import MessageBus, SystemMessageBus, SessionMessageBus, \
    AddressedMessageBus
from dasbus.constants import DBUS_REQUEST_NAME_REPLY_PRIMARY_OWNER, \
    DBUS_NAME_FLAG_ALLOW_REPLACEMENT, DBUS_REQUEST_NAME_REPLY_ALREADY_OWNER

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio


class TestMessageBus(MessageBus):
    """Message bus for testing."""

    def __init__(self):
        super().__init__()
        self._proxy_factory = Mock()
        self._server_factory = Mock()

    def _get_connection(self):
        return Mock()

    def publish_object(self, *args, **kwargs):  # pylint: disable=arguments-differ
        return super().publish_object(*args, **kwargs, server_factory=self._server_factory)

    def get_proxy(self, *args, **kwargs):  # pylint: disable=arguments-differ
        return super().get_proxy(*args, **kwargs, proxy_factory=self._proxy_factory)


class DBusConnectionTestCase(unittest.TestCase):
    """Test DBus connection."""

    def setUp(self):
        self.message_bus = TestMessageBus()
        self.proxy_factory = self.message_bus._proxy_factory
        self.server_factory = self.message_bus._server_factory

    def connection_test(self):
        """Test the bus connection."""
        self.assertIsNotNone(self.message_bus.connection)
        self.assertEqual(self.message_bus.connection, self.message_bus.connection)
        self.assertTrue(self.message_bus.check_connection())

    def failing_connection_test(self):
        """Test the failing connection."""
        self.message_bus._get_connection = Mock(side_effect=IOError())
        self.assertFalse(self.message_bus.check_connection())

        self.message_bus._get_connection = Mock(return_value=None)
        self.assertFalse(self.message_bus.check_connection())

    def proxy_test(self):
        """Test the object proxy."""
        proxy = self.message_bus.get_proxy(
            "service.name",
            "/object/path"
        )

        self.proxy_factory.assert_called_once_with(
            self.message_bus,
            "service.name",
            "/object/path"
        )

        self.assertEqual(proxy, self.proxy_factory.return_value)

    def bus_proxy_test(self):
        """Test the bus proxy."""
        proxy = self.message_bus.proxy

        self.proxy_factory.assert_called_once_with(
            self.message_bus,
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus"
        )

        self.assertIsNotNone(proxy)
        self.assertEqual(proxy, self.proxy_factory.return_value)
        self.assertEqual(self.message_bus.proxy, self.message_bus.proxy)

    def register_service_test(self):
        """Test the service registration."""
        self.message_bus.proxy.RequestName.return_value = DBUS_REQUEST_NAME_REPLY_PRIMARY_OWNER
        self.message_bus.register_service(
            "my.service",
            DBUS_NAME_FLAG_ALLOW_REPLACEMENT
        )

        self.message_bus.proxy.RequestName.assert_called_once_with(
            "my.service",
            DBUS_NAME_FLAG_ALLOW_REPLACEMENT
        )

        self.assertIn("my.service", self.message_bus._requested_names)
        callback = self.message_bus._registrations[-1]
        self.assertTrue(callable(callback))

        self.message_bus.disconnect()
        self.message_bus.proxy.ReleaseName.assert_called_once_with(
            "my.service"
        )

    def failed_register_service_test(self):
        """Test the failing service registration."""
        self.message_bus.proxy.RequestName.return_value = DBUS_REQUEST_NAME_REPLY_ALREADY_OWNER

        with self.assertRaises(ConnectionError):
            self.message_bus.register_service("my.service")

        self.message_bus.proxy.RequestName.assert_called_once_with(
            "my.service",
            DBUS_NAME_FLAG_ALLOW_REPLACEMENT
        )

        self.assertNotIn("my.service", self.message_bus._requested_names)

    def check_service_access_test(self):
        """Check the service access."""
        # The service can be accessed.
        self.message_bus.get_proxy("my.service", "/my/object")

        # The service cannot be accessed.
        self.message_bus.proxy.RequestName.return_value = DBUS_REQUEST_NAME_REPLY_PRIMARY_OWNER
        self.message_bus.register_service("my.service")

        with self.assertRaises(RuntimeError):
            self.message_bus.get_proxy("my.service", "/my/object")

    def publish_object_test(self):
        """Test the object publishing."""
        obj = Mock()
        self.message_bus.publish_object("/my/object", obj)

        self.server_factory.assert_called_once_with(
            self.message_bus,
            "/my/object",
            obj
        )

        callback = self.message_bus._registrations[-1]
        self.assertTrue(callable(callback))

        self.message_bus.disconnect()
        callback.assert_called_once_with()

    def disconnect_test(self):
        """Test the disconnection."""
        # Set up the connection.
        self.assertIsNotNone(self.message_bus.connection)

        # Create registrations.
        callbacks = defaultdict(Mock)

        self.message_bus._registrations = [
            callbacks["my.service.1"],
            callbacks["my.service.2"],
            callbacks["/my/object/1"],
            callbacks["/my/object/2"],
        ]

        self.message_bus._requested_names = {
            "my.service.1",
            "my.service.2"
        }

        # Disconnect.
        self.message_bus.disconnect()
        self.assertEqual(self.message_bus._connection, None)
        self.assertEqual(self.message_bus._registrations, [])
        self.assertEqual(self.message_bus._requested_names, set())

        for callback in callbacks.values():
            callback.assert_called_once_with()

        # Do nothing by default.
        self.message_bus.disconnect()

    @patch("dasbus.connection.Gio.bus_get_sync")
    def system_bus_test(self, getter):
        """Test the system bus."""
        message_bus = SystemMessageBus()
        self.assertIsNotNone(message_bus.connection)
        getter.assert_called_once_with(
            Gio.BusType.SYSTEM,
            None
        )

    @patch("dasbus.connection.Gio.bus_get_sync")
    def session_bus_test(self, getter):
        """Test the session bus."""
        message_bus = SessionMessageBus()
        self.assertIsNotNone(message_bus.connection)
        getter.assert_called_once_with(
            Gio.BusType.SESSION,
            None
        )

    def _check_addressed_connection(self, message_bus, getter, address):
        self.assertIsNotNone(message_bus.connection)
        self.assertEqual(message_bus.address, address)
        getter.assert_called_once_with(
            address,
            (
                Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT |
                Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION
            ),
            None,
            None
        )

    @patch("dasbus.connection.Gio.DBusConnection.new_for_address_sync")
    def addressed_bus_test(self, getter):
        """Test the addressed bus."""
        message_bus = AddressedMessageBus("ADDRESS")
        self._check_addressed_connection(message_bus, getter, "ADDRESS")
