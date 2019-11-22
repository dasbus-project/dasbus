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
from unittest.mock import patch, Mock

from dasbus.constants import DBUS_FLAG_NONE
from dasbus.client.observer import DBusObserver


class DBusObserverTestCase(unittest.TestCase):
    """Test DBus observers."""

    def _setup_observer(self, observer):
        """Set up the observer."""
        observer._service_available = Mock()
        observer._service_unavailable = Mock()
        self.assertFalse(observer.is_service_available)

    def _make_service_available(self, observer):
        """Make the service available."""
        observer._service_name_appeared_callback()
        self._test_if_service_available(observer)

    def _test_if_service_available(self, observer):
        """Test if service is available."""
        self.assertTrue(observer.is_service_available)

        observer._service_available.emit.assert_called_once_with(observer)
        observer._service_available.reset_mock()

        observer._service_unavailable.emit.assert_not_called()
        observer._service_unavailable.reset_mock()

    def _make_service_unavailable(self, observer):
        """Make the service unavailable."""
        observer._service_name_vanished_callback()
        self._test_if_service_unavailable(observer)

    def _test_if_service_unavailable(self, observer):
        """Test if service is unavailable."""
        self.assertFalse(observer.is_service_available)

        observer._service_unavailable.emit.assert_called_once_with(observer)
        observer._service_unavailable.reset_mock()

        observer._service_available.emit.assert_not_called()
        observer._service_available.reset_mock()

    def test_observer(self):
        """Test the observer."""
        observer = DBusObserver(Mock(), "SERVICE")
        self._setup_observer(observer)
        self._make_service_available(observer)
        self._make_service_unavailable(observer)

    @patch("dasbus.client.observer.Gio")
    def test_connect(self, gio):
        """Test Gio support for watching names."""
        dbus = Mock()
        observer = DBusObserver(dbus, "my.service")
        self._setup_observer(observer)

        # Connect the observer.
        observer.connect_once_available()

        # Check the call.
        gio.bus_watch_name_on_connection.assert_called_once()
        args, kwargs = gio.bus_watch_name_on_connection.call_args

        self.assertEqual(len(args), 5)
        self.assertEqual(len(kwargs), 0)
        self.assertEqual(args[0], dbus.connection)
        self.assertEqual(args[1], "my.service")
        self.assertEqual(args[2], DBUS_FLAG_NONE)

        name_appeared_closure = args[3]
        self.assertTrue(callable(name_appeared_closure))

        name_vanished_closure = args[4]
        self.assertTrue(callable(name_vanished_closure))

        # Check the subscription.
        subscription_id = gio.bus_watch_name_on_connection.return_value
        self.assertEqual(len(observer._subscriptions), 1)

        # Check the observer.
        self.assertFalse(observer.is_service_available)
        observer._service_available.emit.assert_not_called()
        observer._service_unavailable.emit.assert_not_called()

        # Call the name appeared closure.
        name_appeared_closure(dbus.connection, "my.service", "name.owner")
        self._test_if_service_available(observer)

        # Call the name vanished closure.
        name_vanished_closure(dbus.connection, "my.service")
        self._test_if_service_unavailable(observer)

        # Call the name appeared closure again.
        name_appeared_closure(dbus.connection, "my.service", "name.owner")
        self._test_if_service_available(observer)

        # Disconnect the observer.
        observer.disconnect()

        gio.bus_unwatch_name.assert_called_once_with(
            subscription_id
        )

        self._test_if_service_unavailable(observer)
        self.assertEqual(observer._subscriptions, [])
