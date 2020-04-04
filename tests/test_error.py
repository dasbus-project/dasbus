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

from dasbus.error import ErrorMapper, DBusError, get_error_decorator, ErrorRule


class ExceptionA(Exception):
    """My testing exception A."""
    pass


class ExceptionA1(ExceptionA):
    """My testing exception A1."""
    pass


class ExceptionA2(ExceptionA):
    """My testing exception A2."""
    pass


class ExceptionB(Exception):
    """My testing exception B."""
    pass


class ExceptionC(Exception):
    """My testing exception C."""
    pass


class CustomRule(ErrorRule):
    """My custom rule for subclasses."""

    def match_type(self, exception_type):
        return issubclass(exception_type, self._exception_type)


class DBusErrorTestCase(unittest.TestCase):
    """Test the DBus error register and handler."""

    def setUp(self):
        self.error_mapper = ErrorMapper()

    def _check_type(self, error_name, expected_type):
        exception_type = self.error_mapper.get_exception_type(error_name)
        self.assertEqual(exception_type, expected_type)

    def _check_name(self, exception_type, expected_name):
        error_name = self.error_mapper.get_error_name(exception_type)
        self.assertEqual(error_name, expected_name)

    def test_decorators(self):
        """Test the error decorators."""
        dbus_error = get_error_decorator(self.error_mapper)

        @dbus_error("org.test.ErrorA")
        class DecoratedA(Exception):
            pass

        @dbus_error("ErrorB", namespace=("org", "test"))
        class DecoratedB(Exception):
            pass

        self._check_name(DecoratedA, "org.test.ErrorA")
        self._check_type("org.test.ErrorA", DecoratedA)

        self._check_name(DecoratedB, "org.test.ErrorB")
        self._check_type("org.test.ErrorB", DecoratedB)

    def test_simple_rule(self):
        """Test a simple rule."""
        self.error_mapper.add_rule(ErrorRule(
            exception_type=ExceptionA,
            error_name="org.test.ErrorA"
        ))

        self._check_name(ExceptionA, "org.test.ErrorA")
        self._check_name(ExceptionA1, "not.known.Error.ExceptionA1")
        self._check_name(ExceptionA2, "not.known.Error.ExceptionA2")

        self._check_type("org.test.ErrorA", ExceptionA)
        self._check_type("org.test.ErrorA1", DBusError)
        self._check_type("org.test.ErrorA2", DBusError)

        self._check_name(ExceptionB, "not.known.Error.ExceptionB")
        self._check_type("org.test.ErrorB", DBusError)

    def test_custom_rule(self):
        """Test a custom rule."""
        self.error_mapper.add_rule(CustomRule(
            exception_type=ExceptionA,
            error_name="org.test.ErrorA"
        ))

        self._check_name(ExceptionA, "org.test.ErrorA")
        self._check_name(ExceptionA1, "org.test.ErrorA")
        self._check_name(ExceptionA2, "org.test.ErrorA")

        self._check_type("org.test.ErrorA", ExceptionA)
        self._check_type("org.test.ErrorA1", DBusError)
        self._check_type("org.test.ErrorA2", DBusError)

        self._check_name(ExceptionB, "not.known.Error.ExceptionB")
        self._check_type("org.test.ErrorB", DBusError)

    def test_several_rules(self):
        """Test several rules."""
        self.error_mapper.add_rule(ErrorRule(
            exception_type=ExceptionA,
            error_name="org.test.ErrorA"
        ))
        self.error_mapper.add_rule(ErrorRule(
            exception_type=ExceptionB,
            error_name="org.test.ErrorB"
        ))

        self._check_name(ExceptionA, "org.test.ErrorA")
        self._check_name(ExceptionB, "org.test.ErrorB")
        self._check_name(ExceptionC, "not.known.Error.ExceptionC")

        self._check_type("org.test.ErrorA", ExceptionA)
        self._check_type("org.test.ErrorB", ExceptionB)
        self._check_type("org.test.ErrorC", DBusError)

    def test_rule_priorities(self):
        """Test the priorities of the rules."""
        self.error_mapper.add_rule(ErrorRule(
            exception_type=ExceptionA,
            error_name="org.test.ErrorA1"
        ))

        self._check_name(ExceptionA, "org.test.ErrorA1")
        self._check_type("org.test.ErrorA1", ExceptionA)
        self._check_type("org.test.ErrorA2", DBusError)

        self.error_mapper.add_rule(ErrorRule(
            exception_type=ExceptionA,
            error_name="org.test.ErrorA2"
        ))

        self._check_name(ExceptionA, "org.test.ErrorA2")
        self._check_type("org.test.ErrorA1", ExceptionA)
        self._check_type("org.test.ErrorA2", ExceptionA)

    def test_default_mapping(self):
        """Test the default error mapping."""
        self._check_name(ExceptionA, "not.known.Error.ExceptionA")
        self._check_type("org.test.ErrorB", DBusError)
        self._check_type("org.test.ErrorC", DBusError)

    def test_default_class(self):
        """Test the default class."""
        self._check_type("org.test.ErrorA", DBusError)

    def test_default_namespace(self):
        """Test the default namespace."""
        self._check_name(ExceptionA, "not.known.Error.ExceptionA")

    def test_failed_mapping(self):
        """Test the failed mapping."""
        self.error_mapper._error_rules = []

        with self.assertRaises(LookupError) as cm:
            self.error_mapper.get_error_name(ExceptionA)

        self.assertEqual(
            "No name found for 'ExceptionA'.",
            str(cm.exception)
        )

        with self.assertRaises(LookupError) as cm:
            self.error_mapper.get_exception_type("org.test.ErrorA")

        self.assertEqual(
            "No type found for 'org.test.ErrorA'.",
            str(cm.exception)
        )
