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
from textwrap import dedent
from unittest.mock import Mock

from dasbus.error import ErrorMapper, ErrorRule
from dasbus.server.handler import ServerObjectHandler, GLibServer
from dasbus.server.interface import accepts_additional_arguments
from dasbus.signal import Signal
from dasbus.specification import DBusSpecificationError
from dasbus.typing import get_variant


class MethodFailedException(Exception):
    """The method has failed."""
    pass


class DBusServerTestCase(unittest.TestCase):
    """Test DBus server support."""

    NO_PARAMETERS = get_variant("()", tuple())

    def setUp(self):
        self.message_bus = Mock()
        self.connection = self.message_bus.connection
        self.error_mapper = ErrorMapper()
        self.object = None
        self.object_path = "/my/path"
        self.handler = None

    def _publish_object(self, xml="<node />"):
        """Publish a mocked object."""
        self.object = Mock(__dbus_xml__=dedent(xml))

        # Raise AttributeError for default methods.
        del self.object.Get
        del self.object.Set
        del self.object.GetAll

        # Create object signals.
        self.object.Signal1 = Signal()
        self.object.Signal2 = Signal()

        # Create default object signals.
        self.object.PropertiesChanged = Signal()

        self.handler = ServerObjectHandler(
            self.message_bus,
            self.object_path,
            self.object,
            error_mapper=self.error_mapper
        )
        self.handler.connect_object()

    def _call_method(self, interface, method, parameters=NO_PARAMETERS,
                     reply=None):
        invocation = Mock()
        invocation.get_sender.return_value = ":1.0"

        GLibServer._object_callback(
            self.connection, Mock(), self.object_path, interface, method,
            parameters, invocation, (self.handler._method_callback, ())
        )

        invocation.return_dbus_error.assert_not_called()
        invocation.return_value.assert_called_once_with(reply)

    def _call_method_with_error(self, interface, method,
                                parameters=NO_PARAMETERS,
                                error_name=None,
                                error_message=None):
        invocation = Mock()

        with self.assertLogs(level='WARN'):
            self.handler._method_callback(
                invocation,
                interface,
                method,
                parameters
            )

        invocation.return_dbus_error.assert_called_once()
        invocation.return_value.assert_not_called()

        (name, msg), kwargs = invocation.return_dbus_error.call_args

        self.assertEqual(kwargs, {})
        self.assertEqual(name, error_name, "Unexpected error name.")

        if error_message is not None:
            self.assertEqual(msg, error_message, "Unexpected error message.")

    def test_register(self):
        """Test the object registration."""
        with self.assertRaises(DBusSpecificationError) as cm:
            self._publish_object("<node />")

        self.assertEqual(
            "No DBus interfaces for registration.",
            str(cm.exception)
        )

        self._publish_object("""
        <node>
            <interface name="Interface" />
        </node>
        """)
        self.message_bus.connection.register_object.assert_called()

        self.handler.disconnect_object()
        self.message_bus.connection.unregister_object.assert_called()

    def test_method(self):
        """Test the method publishing."""
        self._publish_object("""
        <node>
            <interface name="Interface">
                <method name="Method1"/>
                <method name="Method2">
                    <arg direction="in" name="x" type="i"/>
                </method>
                <method name="Method3">
                    <arg direction="out" name="return" type="i"/>
                </method>
                <method name="Method4">
                    <arg direction="in" name="x" type="ad"/>
                    <arg direction="in" name="y" type="o"/>
                    <arg direction="out" name="return" type="(ib)"/>
                </method>
                <method name="Method5">
                    <arg direction="out" name="return" type="i"/>
                    <arg direction="out" name="return" type="b"/>
                </method>
            </interface>
        </node>
        """)

        self.object.Method2.return_value = None
        self._call_method(
            "Interface",
            "Method2",
            parameters=get_variant("(i)", (1, ))
        )
        self.object.Method2.assert_called_once_with(1)

        self.object.Method1.return_value = None
        self._call_method("Interface", "Method1")
        self.object.Method1.assert_called_once_with()

        self.object.Method3.return_value = 0
        self._call_method(
            "Interface",
            "Method3",
            reply=get_variant("(i)", (0, ))
        )
        self.object.Method3.assert_called_once_with()

        self.object.Method4.return_value = (1, True)
        self._call_method(
            "Interface",
            "Method4",
            parameters=get_variant("(ado)", ([1.2, 2.3], "/my/path")),
            reply=get_variant("((ib))", ((1, True), ))
        )
        self.object.Method4.assert_called_once_with([1.2, 2.3], "/my/path")

        self.object.Method5.return_value = (1, True)
        self._call_method(
            "Interface",
            "Method5",
            reply=get_variant("(ib)", (1, True))
        )
        self.object.Method5.assert_called_once_with()

        self._call_method_with_error(
            "Interface",
            "MethodInvalid",
            error_name="not.known.Error.DBusSpecificationError",
            error_message="DBus specification has no member "
                          "'Interface.MethodInvalid'."
        )

        self.error_mapper.add_rule(ErrorRule(
            exception_type=MethodFailedException,
            error_name="MethodFailed"
        ))

        self.object.Method1.side_effect = MethodFailedException(
            "The method has failed."
        )
        self._call_method_with_error(
            "Interface",
            "Method1",
            error_name="MethodFailed",
            error_message="The method has failed."
        )

    def test_invalid_method_result(self):
        """Test a method with an invalid result."""
        self._publish_object("""
        <node>
            <interface name="Interface">
                <method name="Method">
                    <arg direction="out" name="return" type="t"/>
                </method>
            </interface>
        </node>
        """)

        self.object.Method.return_value = -1
        self._call_method_with_error(
            "Interface",
            "Method",
            error_name="not.known.Error.OverflowError"
        )

    def test_property(self):
        """Test the property publishing."""
        self._publish_object("""
        <node>
            <interface name="Interface">
                <property name="Property1" type="i" access="readwrite" />
                <property name="Property2" type="s" access="read" />
                <property name="Property3" type="b" access="write" />
            </interface>
        </node>
        """)

        self.object.Property1 = 0
        self._call_method(
            "org.freedesktop.DBus.Properties", "Get",
            parameters=get_variant("(ss)", (
                "Interface",
                "Property1"
            )),
            reply=get_variant("(v)", (get_variant("i", 0), ))
        )

        self._call_method(
            "org.freedesktop.DBus.Properties", "Set",
            parameters=get_variant("(ssv)", (
                "Interface",
                "Property1",
                get_variant("i", 1)
            )),
        )
        self.assertEqual(self.object.Property1, 1)

        self.object.Property2 = "Hello"
        self._call_method(
            "org.freedesktop.DBus.Properties", "Get",
            parameters=get_variant("(ss)", (
                "Interface",
                "Property2"
            )),
            reply=get_variant("(v)", (get_variant("s", "Hello"), ))
        )
        self._call_method_with_error(
            "org.freedesktop.DBus.Properties", "Set",
            parameters=get_variant("(ssv)", (
                "Interface",
                "Property2",
                get_variant("s", "World")
            )),
            error_name="not.known.Error.AttributeError",
            error_message="The property Interface.Property2 "
                          "is not writable."
        )
        self.assertEqual(self.object.Property2, "Hello")

        self.object.Property3 = True
        self._call_method_with_error(
            "org.freedesktop.DBus.Properties", "Get",
            parameters=get_variant("(ss)", (
                "Interface",
                "Property3"
            )),
            error_name="not.known.Error.AttributeError",
            error_message="The property Interface.Property3 "
                          "is not readable."
        )
        self._call_method(
            "org.freedesktop.DBus.Properties", "Set",
            parameters=get_variant("(ssv)", (
                "Interface",
                "Property3",
                get_variant("b", False)
            )),
        )
        self.assertEqual(self.object.Property3, False)

        self._call_method(
            "org.freedesktop.DBus.Properties", "GetAll",
            parameters=get_variant("(s)", ("Interface", )),
            reply=get_variant("(a{sv})", ({
                "Property1": get_variant("i", 1),
                "Property2": get_variant("s", "Hello")
            }, ))
        )

        self.object.PropertiesChanged(
            "Interface",
            {"Property1": get_variant("i", 1)},
            ["Property2"]
        )
        self.message_bus.connection.emit_signal.assert_called_once_with(
            None,
            self.object_path,
            "org.freedesktop.DBus.Properties",
            "PropertiesChanged",
            get_variant("(sa{sv}as)", (
                "Interface",
                {"Property1": get_variant("i", 1)},
                ["Property2"]
            ))
        )

    def test_signal(self):
        """Test the signal publishing."""
        self._publish_object("""
        <node>
            <interface name="Interface">
                <signal name="Signal1" />
                <signal name="Signal2">
                    <arg direction="out" name="x" type="i"/>
                    <arg direction="out" name="y" type="s"/>
                </signal>
            </interface>
        </node>
        """)
        self.object.Signal1()
        self.message_bus.connection.emit_signal.assert_called_once_with(
            None,
            self.object_path,
            "Interface",
            "Signal1",
            None
        )

        self.message_bus.connection.emit_signal.reset_mock()

        self.object.Signal2(1, "Test")
        self.message_bus.connection.emit_signal.assert_called_once_with(
            None,
            self.object_path,
            "Interface",
            "Signal2",
            get_variant("(is)", (1, "Test"))
        )

    def test_call_info(self):
        self._publish_object("""
        <node>
            <interface name="Interface">
                <method name="Method1"/>
                <method name="Method2">
                    <arg direction="in" name="x" type="i"/>
                </method>
            </interface>
        </node>
        """)

        accepts_additional_arguments(self.object.Method1)
        self._call_method("Interface", "Method1")
        self.object.Method1.assert_called_once_with(
            call_info={"sender": ":1.0"}
        )

        accepts_additional_arguments(self.object.Method2)
        self._call_method(
            "Interface",
            "Method2",
            parameters=get_variant("(i)", (1, ))
        )
        self.object.Method2.assert_called_once_with(
            1, call_info={"sender": ":1.0"}
        )
