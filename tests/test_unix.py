#
# Copyright (C) 2022  Red Hat, Inc.  All rights reserved.
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
import os
import tempfile
import unittest
import unittest.mock

from dasbus.connection import AddressedMessageBus
from dasbus.typing import get_variant, UnixFD, Str, Variant, Tuple, \
    List, Dict, Int, Double, Bool
from dasbus.server.interface import dbus_interface, dbus_signal
from dasbus.unix import GLibClientUnix, GLibServerUnix, acquire_fds, \
    restore_fds
from dasbus.xml import XMLGenerator

from tests.lib_dbus import run_loop, DBusSpawnedTestCase
from tests.test_dbus import DBusExampleTestCase, error_mapper

import gi
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio

__all__ = [
    "UnixFDSwapTests",
    "DBusSpawnedTestCase",
]


def mocked(callback):
    """Wrap the local callback in a mock object."""
    return unittest.mock.Mock(side_effect=callback)


def read_string(fd):
    """Read a value from the given file descriptor."""
    with open(os.dup(fd), "rb", closefd=True) as i:
        value = i.read().decode("utf-8")

    return value


def write_string(value):
    """Write a value to the given file descriptor."""
    with tempfile.TemporaryFile(mode="wb", buffering=0) as o:
        o.write(value.encode("utf-8"))
        o.seek(0)
        out = os.dup(o.fileno())

    return UnixFD(out)


@dbus_interface("my.testing.UnixExample")
class UnixExampleInterface(object):
    """A DBus interface with UnixFD types."""

    def __init__(self):
        self._pipes = []

    @property
    def Pipes(self) -> List[UnixFD]:
        return self._pipes

    @Pipes.setter
    def Pipes(self, pipes: List[UnixFD]):
        self._pipes = pipes

    def Hello(self, name_fd: UnixFD) -> Str:
        name = read_string(name_fd)
        return "Hello, {0}!".format(name)

    def Goodbye(self, name: Str) -> UnixFD:
        return write_string("Goodbye, {0}!".format(name))

    @dbus_signal
    def Signal(self, name: Str, name_fd: UnixFD):
        pass

    def Trigger(self, name: Str, name_fd: UnixFD):
        self.Signal(name, name_fd)


class UnixMessageBus(AddressedMessageBus):
    """A message bus connection with the UnixFD support."""

    def publish_object(self, *args, **kwargs):
        return super().publish_object(*args, **kwargs, server=GLibServerUnix)

    def get_proxy(self, *args, **kwargs):
        return super().get_proxy(*args, **kwargs, client=GLibClientUnix)


class UnixFDSwapTests(unittest.TestCase):
    """Test swapping of Unix file descriptors."""

    def setUp(self):
        """Set up the test."""
        self._r, self._w = os.pipe()

    def tearDown(self):
        """Tear down the test."""
        os.close(self._r)
        os.close(self._w)

    def _swap_fds(self, in_variant, out_variant, fds=None):
        """Swap Unix file descriptors in the input."""
        variant, fd_list = self._acquire_fds(in_variant, out_variant, fds)
        self._restore_fds(variant, fd_list, expected_variant=in_variant)

    def _acquire_fds(self, variant, expected_variant, expected_fds):
        """Acquire Unix file descriptors in the variant."""
        variant, fd_list = acquire_fds(variant)

        # Check the list of acquired fds.
        if expected_fds is None:
            self.assertIsNone(fd_list)
        else:
            self.assertIsInstance(fd_list, Gio.UnixFDList)
            self.assertEqual(fd_list.peek_fds(), expected_fds)

        # Check the variant without fds.
        if expected_variant is None:
            self.assertIsNone(variant)
        else:
            self.assertIsInstance(variant, Variant)
            self.assertEqual(variant.unpack(), expected_variant.unpack())
            self.assertTrue(variant.equal(expected_variant))

        return variant, fd_list

    def _restore_fds(self, variant, fd_list, expected_variant):
        """Restore Unix file descriptors in the variant."""
        variant = restore_fds(variant, fd_list)

        # Check the variant with fds.
        if expected_variant is None:
            self.assertIsNone(variant)
        else:
            self.assertIsInstance(variant, Variant)
            self.assertEqual(variant.unpack(), expected_variant.unpack())
            self.assertTrue(variant.equal(expected_variant))

    def test_empty_fd_list(self):
        """Restore a value if the fd list is empty."""
        self._restore_fds(
            variant=get_variant(Int, 0),
            fd_list=Gio.UnixFDList(),
            expected_variant=get_variant(Int, 0)
        )

    def test_invalid_index(self):
        """Restore a value with an invalid index."""
        self._restore_fds(
            variant=get_variant(UnixFD, 2),
            fd_list=Gio.UnixFDList.new_from_array([self._r, self._w]),
            expected_variant=get_variant(UnixFD, -1)
        )

    def test_values_without_fds(self):
        """Swap values without fds."""
        self._swap_fds(
            in_variant=None,
            out_variant=None,
        )
        self._swap_fds(
            in_variant=get_variant(Int, 0),
            out_variant=get_variant(Int, 0),
        )
        self._swap_fds(
            in_variant=get_variant(Str, "Hi!"),
            out_variant=get_variant(Str, "Hi!"),
        )
        self._swap_fds(
            in_variant=get_variant(Tuple[Double], (1.0, )),
            out_variant=get_variant(Tuple[Double], (1.0, )),
        )
        self._swap_fds(
            in_variant=get_variant(List[Bool], [False]),
            out_variant=get_variant(List[Bool], [False]),
        )

    def test_value_with_fds(self):
        """Swap a basic value with fds."""
        self._swap_fds(
            in_variant=get_variant(UnixFD, self._r),
            out_variant=get_variant(UnixFD, 0),
            fds=[self._r],
        )

    def test_variant_with_fds(self):
        """Swap a variant with fds."""
        self._swap_fds(
            in_variant=get_variant(Variant, get_variant(
                UnixFD, self._r
            )),
            out_variant=get_variant(Variant, get_variant(
                UnixFD, 0
            )),
            fds=[self._r],
        )

    def test_tuple_with_fds(self):
        """Swap a tuple with fds."""
        self._swap_fds(
            in_variant=get_variant(Tuple[UnixFD, UnixFD], (
                self._r, self._w
            )),
            out_variant=get_variant(Tuple[UnixFD, UnixFD], (
                0, 1
            )),
            fds=[self._r, self._w],
        )

    def test_variant_tuple_with_fds(self):
        """Swap a tuple of variants with fds."""
        self._swap_fds(
            in_variant=get_variant(Tuple[Variant, Variant], (
                get_variant(UnixFD, self._r),
                get_variant(UnixFD, self._w),
            )),
            out_variant=get_variant(Tuple[Variant, Variant], (
                get_variant(UnixFD, 0),
                get_variant(UnixFD, 1),
            )),
            fds=[self._r, self._w],
        )

    def test_list_with_fds(self):
        """Swap a list with fds."""
        self._swap_fds(
            in_variant=get_variant(List[UnixFD], [
                self._r, self._w
            ]),
            out_variant=get_variant(List[UnixFD], [
                0, 1
            ]),
            fds=[self._r, self._w],
        )

    def test_variant_list_with_fds(self):
        """Swap a list of variants with fds."""
        self._swap_fds(
            in_variant=get_variant(List[Variant], [
                get_variant(UnixFD, self._r),
                get_variant(UnixFD, self._w)
            ]),
            out_variant=get_variant(List[Variant], [
                get_variant(UnixFD, 0),
                get_variant(UnixFD, 1)
            ]),
            fds=[self._r, self._w],
        )

    def test_dictionary_with_fds_values(self):
        """Swap a dictionary with fds values."""
        self._swap_fds(
            in_variant=get_variant(Dict[Str, UnixFD], {
                "r": self._r, "w": self._w
            }),
            out_variant=get_variant(Dict[Str, UnixFD], {
                "r": 0, "w": 1
            }),
            fds=[self._r, self._w]
        )

    def test_dictionary_with_fds_keys(self):
        """Swap a dictionary with fds keys."""
        self._swap_fds(
            in_variant=get_variant(Dict[UnixFD, Str], {
                self._r: "r", self._w: "w"
            }),
            out_variant=get_variant(Dict[UnixFD, Str], {
                0: "r", 1: "w"
            }),
            fds=[self._r, self._w]
        )

    def test_variant_dictionary_with_fds(self):
        """Swap a dictionary of variants with fds."""
        self._swap_fds(
            in_variant=get_variant(Dict[Str, Variant], {
                "r": get_variant(UnixFD, self._r),
                "w": get_variant(UnixFD, self._w)
            }),
            out_variant=get_variant(Dict[Str, Variant], {
                "r": get_variant(UnixFD, 0),
                "w": get_variant(UnixFD, 1)
            }),
            fds=[self._r, self._w]
        )

    def test_nested_variants_with_fds(self):
        """Swap nested variants with fds."""
        self._swap_fds(
            in_variant=get_variant(Variant, get_variant(
                Variant, get_variant(UnixFD, self._r)),
            ),
            out_variant=get_variant(Variant, get_variant(
                Variant, get_variant(UnixFD, 0)),
            ),
            fds=[self._r],
        )

    def test_nested_containers_with_fds(self):
        """Swap nested containers with fds."""
        self._swap_fds(
            in_variant=get_variant(
                Tuple[List[UnixFD], Dict[Str, Variant]],
                ([self._r], {"w": get_variant(UnixFD, self._w)})
            ),
            out_variant=get_variant(
                Tuple[List[UnixFD], Dict[Str, Variant]],
                ([0], {"w": get_variant(UnixFD, 1)})
            ),
            fds=[self._r, self._w],
        )


class DBusUnixCompatibilityTestCase(DBusExampleTestCase):
    """Test the Unix support compatibility with a real DBus connection."""

    def _get_message_bus(self, bus_address):
        """Get a message bus."""
        return UnixMessageBus(bus_address, error_mapper)


class DBusUnixExampleTestCase(DBusSpawnedTestCase):
    """Test Unix support with a real DBus connection."""

    def _get_service(self):
        """Get the example service."""
        return UnixExampleInterface()

    @classmethod
    def _get_message_bus(cls, bus_address):
        """Get a message bus."""
        return UnixMessageBus(bus_address)

    @classmethod
    def _get_proxy(cls, bus_address, **proxy_args):
        """Get a proxy of the example service."""
        message_bus = cls._get_message_bus(bus_address)
        return cls._get_service_proxy(message_bus, **proxy_args)

    def test_xml_specification(self):
        """Test the generated specification."""
        expected_xml = '''
        <node>
          <!--Specifies UnixExampleInterface-->
          <interface name="my.testing.UnixExample">
            <method name="Goodbye">
              <arg direction="in" name="name" type="s"></arg>
              <arg direction="out" name="return" type="h"></arg>
            </method>
            <method name="Hello">
              <arg direction="in" name="name_fd" type="h"></arg>
              <arg direction="out" name="return" type="s"></arg>
            </method>
            <property access="readwrite" name="Pipes" type="ah"></property>
            <signal name="Signal">
                <arg direction="out" name="name" type="s"></arg>
                <arg direction="out" name="name_fd" type="h"></arg>
            </signal>
            <method name="Trigger">
                <arg direction="in" name="name" type="s"></arg>
                <arg direction="in" name="name_fd" type="h"></arg>
            </method>
          </interface>
        </node>
        '''
        generated_xml = self.service.__dbus_xml__

        self.assertEqual(
            XMLGenerator.prettify_xml(expected_xml),
            XMLGenerator.prettify_xml(generated_xml)
        )

    def test_sync_calls(self):
        """Test DBus sync calls with fds."""
        self._add_client(self._call_hello_sync)
        self._add_client(self._call_goodbye_sync)
        self._run_test()

    @classmethod
    def _call_hello_sync(cls, bus_address):
        """Say sync hello to Foo."""
        proxy = cls._get_proxy(bus_address)
        fd = write_string("Foo")
        greeting = proxy.Hello(fd)
        assert greeting == "Hello, Foo!", greeting

    @classmethod
    def _call_goodbye_sync(cls, bus_address):
        """Say sync goodbye to Bar."""
        proxy = cls._get_proxy(bus_address)
        fd = proxy.Goodbye("Bar")
        greeting = read_string(fd)
        assert greeting == "Goodbye, Bar!", greeting

    def test_async_calls(self):
        """Test DBus async calls with fds."""
        self._add_client(self._call_hello_async)
        self._add_client(self._call_goodbye_async)
        self._run_test()

    @classmethod
    def _call_hello_async(cls, bus_address):
        """Say async hello to Foo."""
        proxy = cls._get_proxy(bus_address)

        @mocked
        def callback(call):
            greeting = call()
            assert greeting == "Hello, Foo!", greeting

        fd = write_string("Foo")
        proxy.Hello(fd, callback=callback)
        run_loop()

        callback.assert_called_once()

    @classmethod
    def _call_goodbye_async(cls, bus_address):
        """Say async goodbye to Bar."""
        proxy = cls._get_proxy(bus_address)

        @mocked
        def callback(call):
            greeting = read_string(call())
            assert greeting == "Goodbye, Bar!", greeting

        proxy.Goodbye("Bar", callback=callback)
        run_loop()

        callback.assert_called_once()

    def test_properties(self):
        """Test DBus properties with fds."""
        self._add_client(self._set_pipes)
        self._add_client(self._get_pipes)
        self._run_test()

    @classmethod
    def _set_pipes(cls, bus_address):
        proxy = cls._get_proxy(bus_address)
        pipes = list(map(write_string, ["1", "2", "3"]))
        proxy.Pipes = pipes

    @classmethod
    def _get_pipes(cls, bus_address):
        proxy = cls._get_proxy(bus_address)
        pipes = []

        while not pipes:
            pipes = proxy.Pipes

        values = list(map(read_string, pipes))
        assert values == ["1", "2", "3"]

    def test_signals(self):
        """Test DBus signals with fds."""
        event = self.context.Event()
        self._add_client(self._trigger_signal, event)
        self._add_client(self._watch_signal, event)
        self._run_test()

    @classmethod
    def _trigger_signal(cls, bus_address, event):
        event.wait()
        proxy = cls._get_proxy(bus_address)
        proxy.Trigger("Foo", write_string("Foo"))

    @classmethod
    def _watch_signal(cls, bus_address, event):
        proxy = cls._get_proxy(bus_address)

        @mocked
        def callback(name, name_fd):
            # GLib doesn't support fds in signals, so we
            # are not able to restore fds in this case.
            # Because of that, name_fd is just an index.
            assert name == "Foo"
            assert name_fd == 0

        proxy.Signal.connect(callback)
        event.set()
        run_loop()

        callback.assert_called_once()
