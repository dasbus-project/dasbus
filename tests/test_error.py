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
from unittest.mock import patch

from dasbus.error import ErrorRegister, dbus_error, dbus_error_by_default


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

    @patch("dasbus.error.register", new_callable=ErrorRegister)
    def test_decorators(self, register):
        """Test the error decorators."""
        r = register

        @dbus_error("org.test.ErrorA")
        class DecoratedA(Exception):
            pass

        @dbus_error("ErrorB", namespace=("org", "test"))
        class DecoratedB(Exception):
            pass

        @dbus_error_by_default
        class DecoratedC(Exception):
            pass

        self.assertEqual(r.get_error_name(DecoratedA), "org.test.ErrorA")
        self.assertEqual(r.get_error_name(DecoratedB), "org.test.ErrorB")

        self.assertEqual(r.get_exception_class("org.test.ErrorA"), DecoratedA)
        self.assertEqual(r.get_exception_class("org.test.ErrorB"), DecoratedB)
        self.assertEqual(r.get_exception_class("org.test.ErrorC"), DecoratedC)

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
        self.assertEqual(r.get_error_name(ExceptionA), "ExceptionA")
