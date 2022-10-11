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
from unittest import mock
from unittest.mock import Mock

from dasbus.client.proxy import disconnect_proxy
from dasbus.connection import AddressedMessageBus
from dasbus.error import ErrorMapper, get_error_decorator
from dasbus.server.interface import dbus_interface, dbus_signal, \
    accepts_additional_arguments, returns_multiple_arguments
from dasbus.typing import get_variant, Str, Int, Dict, Variant, List, \
    Tuple, Bool
from dasbus.xml import XMLGenerator
from threading import Event

from tests.lib_dbus import DBusThreadedTestCase

# Define the error mapper and decorator.
error_mapper = ErrorMapper()
dbus_error = get_error_decorator(error_mapper)


@dbus_error("my.testing.Error")
class ExampleException(Exception):
    pass


@dbus_interface("my.testing.Example")
class ExampleInterface(object):

    def __init__(self):
        self._knocked = False
        self._names = []
        self._values = [0]
        self._secrets = []

    @property
    def Name(self) -> Str:
        return "My example"

    @property
    def Value(self) -> Int:
        return self._values[-1]

    @Value.setter
    def Value(self, value: Int):
        self._values.append(value)
        self.PropertiesChanged(
            "my.testing.Example",
            {"Value": get_variant(Int, value)},
            ["Name"]
        )

    def _set_secret(self, secret: Str):
        self._secrets.append(secret)

    Secret = property(fset=_set_secret)

    def Knock(self):
        self._knocked = True
        self.Knocked()

    def Hello(self, name: Str) -> Str:
        self._names.append(name)
        self.Visited(name)
        return "Hello, {0}!".format(name)

    @dbus_signal
    def Knocked(self):
        pass

    @dbus_signal
    def Visited(self, name: Str):
        pass

    def Raise(self, message: Str):
        raise ExampleException(message)

    @dbus_signal
    def PropertiesChanged(self, interface: Str, changed: Dict[Str, Variant],
                          invalid: List[Str]):
        pass

    @accepts_additional_arguments
    def GetInfo(self, arg: Str, *, call_info) -> Str:
        return "{0}: {1}".format(arg, call_info)

    @returns_multiple_arguments
    def ReturnArgs(self) -> Tuple[Int, Bool, Str]:
        return 0, False, "zero"


class DBusExampleTestCase(DBusThreadedTestCase):
    """Test DBus support with a real DBus connection."""

    def _get_service(self):
        """Get the example service."""
        return ExampleInterface()

    @classmethod
    def _get_message_bus(cls, bus_address):
        """Get a message bus."""
        return AddressedMessageBus(bus_address, error_mapper)

    def _get_proxy(self, **proxy_args):
        """Get a proxy of the example service."""
        return self._get_service_proxy(self.message_bus, **proxy_args)

    def test_message_bus(self):
        """Test the message bus."""
        self.assertTrue(self.message_bus.check_connection())
        self.assertEqual(self.message_bus.address, self.bus.get_bus_address())
        self.assertEqual(self.message_bus.proxy.Ping(), None)

    def test_xml_specification(self):
        """Test the generated specification."""
        expected_xml = '''
        <node>
          <!--Specifies ExampleInterface-->
          <interface name="my.testing.Example">
            <method name="GetInfo">
              <arg direction="in" name="arg" type="s"></arg>
              <arg direction="out" name="return" type="s"></arg>
            </method>
            <method name="Hello">
              <arg direction="in" name="name" type="s"></arg>
              <arg direction="out" name="return" type="s"></arg>
            </method>
            <method name="Knock"></method>
            <signal name="Knocked"></signal>
            <property access="read" name="Name" type="s"></property>
            <method name="Raise">
              <arg direction="in" name="message" type="s"></arg>
            </method>
            <method name="ReturnArgs">
              <arg direction="out" name="return_0" type="i"></arg>
              <arg direction="out" name="return_1" type="b"></arg>
              <arg direction="out" name="return_2" type="s"></arg>
            </method>
            <property access="write" name="Secret" type="s"></property>
            <property access="readwrite" name="Value" type="i"></property>
            <signal name="Visited">
              <arg direction="out" name="name" type="s"></arg>
            </signal>
          </interface>
        </node>
        '''

        generated_xml = self.service.__dbus_xml__

        self.assertEqual(
            XMLGenerator.prettify_xml(expected_xml),
            XMLGenerator.prettify_xml(generated_xml)
        )

    def test_knock(self):
        """Call a simple DBus method."""
        self.assertEqual(self.service._knocked, False)

        def test():
            proxy = self._get_proxy()
            self.assertEqual(None, proxy.Knock())

        self._add_client(test)
        self._run_test()

        self.assertEqual(self.service._knocked, True)

    def test_hello(self):
        """Call a DBus method."""

        def test1():
            proxy = self._get_proxy()
            self.assertEqual("Hello, Foo!", proxy.Hello("Foo"))

        def test2():
            proxy = self._get_proxy()
            self.assertEqual("Hello, Bar!", proxy.Hello("Bar"))

        self._add_client(test1)
        self._add_client(test2)
        self._run_test()

        self.assertEqual(sorted(self.service._names), ["Bar", "Foo"])

    def test_timeout(self):
        """Call a DBus method with a timeout."""

        def test1():
            proxy = self._get_proxy()
            proxy.Hello("Foo", timeout=1000)

        def test2():
            proxy = self._get_proxy()

            with self.assertRaises(TimeoutError):
                proxy.Hello("Bar", timeout=0)

        self._add_client(test1)
        self._add_client(test2)
        self._run_test()

        self.assertEqual(sorted(self.service._names), ["Bar", "Foo"])

    def test_name(self):
        """Use a DBus read-only property."""

        def test1():
            proxy = self._get_proxy()
            self.assertEqual("My example", proxy.Name)

        def test2():
            proxy = self._get_proxy()
            self.assertEqual("My example", proxy.Name)

        def test3():
            proxy = self._get_proxy()
            with self.assertRaises(AttributeError) as cm:
                proxy.Name = "Another example"

            self.assertEqual(
                "Can't set DBus property.",
                str(cm.exception)
            )

            self.assertEqual("My example", proxy.Name)

        self._add_client(test1)
        self._add_client(test2)
        self._add_client(test3)
        self._run_test()

    def test_secret(self):
        """Use a DBus write-only property."""

        def test1():
            proxy = self._get_proxy()
            proxy.Secret = "Secret 1"

        def test2():
            proxy = self._get_proxy()
            proxy.Secret = "Secret 2"

        def test3():
            proxy = self._get_proxy()
            with self.assertRaises(AttributeError) as cm:
                self.fail(proxy.Secret)

            self.assertEqual(
                "Can't read DBus property.",
                str(cm.exception)
            )

        self._add_client(test1)
        self._add_client(test2)
        self._add_client(test3)
        self._run_test()

        self.assertEqual(sorted(self.service._secrets), [
            "Secret 1",
            "Secret 2"
        ])

    def test_value(self):
        """Use a DBus read-write property."""

        def test1():
            proxy = self._get_proxy()
            self.assertIn(proxy.Value, (0, 3, 4))
            proxy.Value = 1
            self.assertIn(proxy.Value, (1, 3, 4))
            proxy.Value = 2
            self.assertIn(proxy.Value, (2, 3, 4))

        def test2():
            proxy = self._get_proxy()
            self.assertIn(proxy.Value, (0, 1, 2))
            proxy.Value = 3
            self.assertIn(proxy.Value, (3, 1, 2))
            proxy.Value = 4
            self.assertIn(proxy.Value, (4, 1, 2))

        self._add_client(test1)
        self._add_client(test2)
        self._run_test()

        self.assertEqual(sorted(self.service._values), [0, 1, 2, 3, 4])
        self.assertEqual(self.service._values[0], 0)
        self.assertLess(self.service._values.index(1),
                        self.service._values.index(2))
        self.assertLess(self.service._values.index(3),
                        self.service._values.index(4))

    def test_knocked(self):
        """Use a simple DBus signal."""
        event = Event()
        knocked = Mock()

        def callback():
            knocked("Knocked!")

        def test_1():
            proxy = self._get_proxy()
            proxy.Knocked.connect(callback)
            event.set()

        def test_2():
            event.wait()
            proxy = self._get_proxy()
            proxy.Knock()
            proxy.Knock()
            proxy.Knock()

        self._add_client(test_1)
        self._add_client(test_2)
        self._run_test()

        knocked.assert_has_calls([
            mock.call("Knocked!"),
            mock.call("Knocked!"),
            mock.call("Knocked!")
        ])

    def test_visited(self):
        """Use a DBus signal."""
        event = Event()
        visited = Mock()

        def callback(name):
            visited("Visited by {0}.".format(name))

        def test1():
            proxy = self._get_proxy()
            proxy.Visited.connect(callback)
            event.set()

        def test2():
            event.wait()
            proxy = self._get_proxy()
            proxy.Hello("Foo")
            proxy.Hello("Bar")

        self._add_client(test1)
        self._add_client(test2)
        self._run_test()

        visited.assert_has_calls([
            mock.call("Visited by Foo."),
            mock.call("Visited by Bar.")
        ])

    def test_unsubscribed(self):
        """Use an unsubscribed DBus signal."""
        event = Event()
        knocked = Mock()

        def callback():
            knocked("Knocked!")

        def test_1():
            proxy = self._get_proxy()
            proxy.Knocked.connect(callback)
            disconnect_proxy(proxy)
            event.set()

        def test_2():
            event.wait()
            proxy = self._get_proxy()
            proxy.Knock()
            proxy.Knock()
            proxy.Knock()

        self._add_client(test_1)
        self._add_client(test_2)
        self._run_test()

        knocked.assert_not_called()

    def test_asynchronous(self):
        """Call a DBus method asynchronously."""
        returned = Mock()

        def callback(call, number):
            returned(number, call())

        def test():
            proxy = self._get_proxy()
            proxy.Hello("Foo", callback=callback, callback_args=(1, ))
            proxy.Hello("Foo", callback=callback, callback_args=(2, ))
            proxy.Hello("Bar", callback=callback, callback_args=(3, ))

        self._add_client(test)
        self._run_test()

        returned.assert_has_calls([
            mock.call(1, "Hello, Foo!"),
            mock.call(2, "Hello, Foo!"),
            mock.call(3, "Hello, Bar!"),
        ])

    def test_error(self):
        """Handle a DBus error."""
        raised = Mock()

        def callback(call, number):
            try:
                call()
            except ExampleException as e:
                raised(number, str(e))

        def test1():
            proxy = self._get_proxy()
            proxy.Raise("Foo failed!", callback=callback, callback_args=(1, ))
            proxy.Raise("Foo failed!", callback=callback, callback_args=(2, ))
            proxy.Raise("Bar failed!", callback=callback, callback_args=(3, ))

        def test2():
            proxy = self._get_proxy()

            try:
                proxy.Raise("My message")
            except ExampleException as e:
                self.assertEqual(str(e), "My message")
            else:
                self.fail("Exception wasn't raised!")

        self._add_client(test1)
        self._add_client(test2)

        with self.assertLogs(level='WARN'):
            self._run_test()

        raised.assert_has_calls([
            mock.call(1, "Foo failed!"),
            mock.call(2, "Foo failed!"),
            mock.call(3, "Bar failed!"),
        ])

    def test_properties_changed(self):
        """Test the PropertiesChanged signal."""
        event = Event()
        callback = Mock()

        def test_1():
            proxy = self._get_proxy()
            proxy.PropertiesChanged.connect(callback)
            event.set()

        def test_2():
            event.wait()
            proxy = self._get_proxy()
            proxy.Value = 10

        self._add_client(test_1)
        self._add_client(test_2)
        self._run_test()

        callback.assert_called_once_with(
            "my.testing.Example",
            {"Value": get_variant(Int, 10)},
            ["Name"]
        )

    def test_interface(self):
        """Use a specific DBus interface."""

        def test_1():
            proxy = self._get_proxy(interface_name="my.testing.Example")
            proxy.Knock()

            with self.assertRaises(AttributeError):
                proxy.Ping()

        def test_2():
            proxy = self._get_proxy(interface_name="org.freedesktop.DBus.Peer")
            proxy.Ping()

            with self.assertRaises(AttributeError):
                proxy.Knock()

        self._add_client(test_1)
        self._add_client(test_2)
        self._run_test()

    def test_additional_arguments(self):
        """Call a DBus method."""

        def test1():
            proxy = self._get_proxy()
            self.assertEqual(
                proxy.GetInfo("Foo"),
                "Foo: {'sender': ':1.0'}"
            )

        def test2():
            proxy = self._get_proxy()
            self.assertEqual(
                proxy.GetInfo("Bar"),
                "Bar: {'sender': ':1.0'}"
            )

        self._add_client(test1)
        self._add_client(test2)
        self._run_test()

    def test_multiple_output_arguments(self):
        """Call a DBus method with multiple output arguments."""

        def test1():
            proxy = self._get_proxy()
            self.assertEqual(
                proxy.ReturnArgs(),
                (0, False, "zero")
            )

        self._add_client(test1)
        self._run_test()
