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
from unittest.mock import Mock, patch

from dasbus.error import ErrorRegister, GLibErrorHandler
from dasbus.client.handler import GLibClient
from dasbus.server.handler import GLibServer

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio


class ExceptionA(Exception):
    """My testing exception A."""
    pass


class ExceptionB(Exception):
    """My testing exception B."""
    pass


class ExceptionC(Exception):
    """My testing exception C."""
    pass


class DBusErrorTestCase(unittest.TestCase):
    """Test the DBus error register and handler."""

    def test_error_mapping(self):
        """Test the error mapping."""
        r = ErrorRegister()
        r.set_default_exception(None)
        r.map_exception_to_name(ExceptionA, "org.test.ErrorA")
        r.map_exception_to_name(ExceptionB, "org.test.ErrorB")

        self.assertEqual(
            r.get_error_name(ExceptionA),
            "org.test.ErrorA"
        )
        self.assertEqual(
            r.get_error_name(ExceptionB),
            "org.test.ErrorB"
        )
        self.assertEqual(
            r.get_error_name(ExceptionC),
            "not.known.Error.ExceptionC"
        )

        self.assertEqual(
            r.get_exception_class("org.test.ErrorA"),
            ExceptionA
        )
        self.assertEqual(
            r.get_exception_class("org.test.ErrorB"),
            ExceptionB
        )
        self.assertEqual(
            r.get_exception_class("org.test.ErrorC"),
            None
        )

    def test_default_mapping(self):
        """Test the default error mapping."""
        r = ErrorRegister()
        r.set_default_exception(ExceptionA)

        self.assertEqual(
            r.get_error_name(ExceptionA),
            "not.known.Error.ExceptionA"
        )
        self.assertEqual(
            r.get_exception_class("org.test.ErrorB"),
            ExceptionA
        )
        self.assertEqual(
            r.get_exception_class("org.test.ErrorC"),
            ExceptionA
        )

    def test_default_namespace(self):
        """Test the default namespace."""
        r = ErrorRegister()
        self.assertEqual(
            r.get_error_name(ExceptionA),
            "not.known.Error.ExceptionA"
        )

        r.set_default_namespace(
            "my.namespace.Error"
        )
        self.assertEqual(
            r.get_error_name(ExceptionA),
            "my.namespace.Error.ExceptionA"
        )

        r.set_default_namespace(None)
        self.assertEqual(
            r.get_error_name(ExceptionA),
            "ExceptionA"
        )

    def test_get_message(self):
        """Test the DBus error messages."""
        h = GLibErrorHandler()

        message = h._get_exception_message(
            "org.test.Error",
            "My error message"
        )
        self.assertEqual(
            message,
            "My error message"
        )

        message = h._get_exception_message(
            "org.test.Error",
            "GDBus.Error:org.test.Error: My error message"
        )
        self.assertEqual(
            message,
            "My error message"
        )

        message = h._get_exception_message(
            "org.test.Error",
            "GDBus.Error:org.test.ErrorX: My error message"
        )
        self.assertEqual(
            message,
            "GDBus.Error:org.test.ErrorX: My error message"
        )

    @patch("dasbus.error.GLibErrorHandler.register",
           new_callable=ErrorRegister)
    def test_create_exception(self, register):
        """Test the exception."""
        domain = Gio.DBusError.quark()

        h = GLibErrorHandler()
        h.register.map_exception_to_name(ExceptionA, "org.test.ErrorA")

        e = h._create_exception(
            "org.test.ErrorA",
            "My error message.",
            domain,
            666
        )
        self.assertIsInstance(e, ExceptionA)
        self.assertEqual(str(e), "My error message.")
        self.assertEqual(getattr(e, "dbus_name"), "org.test.ErrorA")
        self.assertEqual(getattr(e, "dbus_domain"), domain)
        self.assertEqual(getattr(e, "dbus_code"), 666)

    @patch("dasbus.error.GLibErrorHandler.register",
           new_callable=ErrorRegister)
    def test_is_name_registered(self, register):
        """Test the registered name."""
        h = GLibErrorHandler()
        h.register.map_exception_to_name(ExceptionA, "org.test.ErrorA")

        self.assertEqual(h._is_name_registered("org.test.ErrorA"), True)
        self.assertEqual(h._is_name_registered("org.test.ErrorB"), False)

    @patch("dasbus.error.GLibErrorHandler.register",
           new_callable=ErrorRegister)
    def test_handle_server_error(self, register):
        """Test the server error handler."""
        h = GLibErrorHandler()
        h.register.map_exception_to_name(
            ExceptionA,
            "org.test.ErrorA"
        )

        invocation = Mock()
        h.handle_server_error(
            GLibServer,
            invocation,
            ExceptionA("My message")
        )
        invocation.return_dbus_error.assert_called_once_with(
            "org.test.ErrorA",
            "My message"
        )

    @patch("dasbus.error.GLibErrorHandler.register",
           new_callable=ErrorRegister)
    def test_handle_client_error(self, register):
        """Test the client error handler."""
        h = GLibErrorHandler()
        h.register.set_default_exception(ExceptionA)
        h.register.map_exception_to_name(ExceptionB, "org.test.ErrorB")

        remote_error = Gio.DBusError.new_for_dbus_error(
            "org.test.Unknown",
            "My message."
        )
        with self.assertRaises(ExceptionA) as cm:
            h.handle_client_error(GLibClient, remote_error)

        self.assertEqual(str(cm.exception), "My message.")

        remote_error = Gio.DBusError.new_for_dbus_error(
            "org.test.ErrorB",
            "My message."
        )
        with self.assertRaises(ExceptionB) as cm:
            h.handle_client_error(GLibClient, remote_error)

        self.assertEqual(str(cm.exception), "My message.")

        with self.assertRaises(ExceptionC) as cm:
            h.handle_client_error(GLibClient, ExceptionC("My message."))

        self.assertEqual(str(cm.exception), "My message.")
