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
import subprocess
import sys
import tempfile
import unittest

from textwrap import dedent

from dasbus.typing import get_variant, UnixFD, Str, Variant, Tuple, \
    List, Dict, Int, Double, Bool
from dasbus.connection import AddressedMessageBus
from dasbus.loop import EventLoop
from dasbus.server.interface import dbus_interface
from dasbus.unix import GLibClientUnix, GLibServerUnix, acquire_fds, \
    restore_fds
from dasbus.xml import XMLGenerator

from tests.test_dbus import DBusTestCase, error_mapper

import gi
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib

__all__ = [
    "UnixFDSwapTests",
    "DBusForkedTestCase",
]


def read_name(fd):
    """Read a name from the given file descriptor."""
    with open(os.dup(fd), "rb", closefd=True) as ifile:
        name = ifile.read().decode("utf-8")

    return name


def write_hello(pattern, name):
    """Write a greeting to the given file descriptor."""
    with tempfile.TemporaryFile(mode="wb", buffering=0, prefix=name) as o:
        o.write(pattern.format(name).encode("utf-8"))
        o.seek(0)
        out = os.dup(o.fileno())

    return UnixFD(out)


@dbus_interface("my.testing.UnixExample")
class UnixExampleInterface(object):
    """A DBus interface with UnixFD types."""

    def __init__(self):
        self._names = []

    def HelloFD(self, name_fd: UnixFD) -> UnixFD:
        name = read_name(name_fd)
        self._names.append(name)
        return write_hello("Hello, {0}!", name)

    def GoodbyeFD(self, name: Str) -> UnixFD:
        return write_hello("Goodbye, {0}!", name)


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


class DBusForkedTestCase(DBusTestCase):
    """Test DBus support with a real DBus connection."""

    def setUp(self):
        super().setUp()
        self.server_args = {"server": GLibServerUnix}
        self.client_args = {"client": GLibClientUnix}

    def test_xml_specification(self):
        """Test the generated specification."""
        self._set_service(UnixExampleInterface())

        expected_xml = '''
        <node>
          <!--Specifies UnixExampleInterface-->
          <interface name="my.testing.UnixExample">
            <method name="GoodbyeFD">
              <arg direction="in" name="name" type="s"></arg>
              <arg direction="out" name="return" type="h"></arg>
            </method>
            <method name="HelloFD">
              <arg direction="in" name="name_fd" type="h"></arg>
              <arg direction="out" name="return" type="h"></arg>
            </method>
          </interface>
        </node>
        '''

        generated_xml = self.service.__dbus_xml__

        self.assertEqual(
            XMLGenerator.prettify_xml(expected_xml),
            XMLGenerator.prettify_xml(generated_xml)
        )

    def _add_client(self, test_name, test_string):
        self.clients.append([test_name, test_string])

    def _run_test(self):
        proc = []
        for func, name in self.clients:
            cmd = dedent(f"""
            from tests.test_unix import {func}
            import sys
            addr=sys.stdin.readline()
            exit({func}(addr, "{name}"))
            """)

            # pylint: disable=R1732
            proc.append(subprocess.Popen(
                [sys.executable, "-u", "-c", cmd],
                stdin=subprocess.PIPE))

        self.message_bus.publish_object(
            "/my/testing/Example",
            self.service,
            **self.server_args
        )

        self.message_bus.register_service(
            "my.testing.Example"
        )

        address = self.message_bus.address

        for client in proc:
            client.stdin.write(bytes(address + "\n", "utf-8"))
            client.stdin.close()

        self.assertTrue(self._run_service())

        for client in proc:
            client.wait(4)

    def test_hello_fd(self):
        """Call a DBus method, passing and returning UnixFD handles"""
        self._set_service(UnixExampleInterface())
        self.assertEqual(self.service._names, [])
        self.assertEqual(self.clients, [])

        test1 = ("_hello_fdtest", "FooFD")
        test2 = ("_hello_fdtest", "BarFD")
        test3 = ("_hello_fdtest_async", "FooAsyncFD")
        test4 = ("_hello_fdtest_async", "BarAsyncFD")

        self._add_client(*test1)
        self._add_client(*test2)
        self._add_client(*test3)
        self._add_client(*test4)
        self._run_test()

        self.assertEqual(
            sorted(self.service._names),
            ["BarAsyncFD", "BarFD", "FooAsyncFD", "FooFD"]
        )

    def test_goodbye_fd(self):
        """Test that a valid UnixFD can be
        returned when not also passing one."""
        self._set_service(UnixExampleInterface())
        self.assertEqual(self.service._names, [])

        tests = [
            ("_goodbye_fd_test", 'FooFD'),
            ("_goodbye_fd_test", 'BarFD'),
            ("_goodbye_fd_test_async", 'AsyncFooFD'),
            ("_goodbye_fd_test_async", 'AsyncBarFD')
        ]

        for test in tests:
            self._add_client(*test)

        self._run_test()


def _goodbye_fd_test(addr, n):
    message_bus = AddressedMessageBus(
        addr,
        error_mapper=error_mapper
    )
    proxy = message_bus.get_proxy(
        "my.testing.Example",
        "/my/testing/Example",
        client=GLibClientUnix
    )

    fd = proxy.GoodbyeFD(n)
    with open(os.dup(fd), "rb", closefd=True) as rfd:
        buf = rfd.read()

        a = 'Goodbye, {0}!'.format(n)
        b = buf.decode(encoding='utf-8')
        return a == b


def _goodbye_fd_test_async(addr, n):
    result = [False]
    message_bus = AddressedMessageBus(
        addr,
        error_mapper=error_mapper
    )
    proxy = message_bus.get_proxy(
        "my.testing.Example",
        "/my/testing/Example",
        client=GLibClientUnix
    )

    def complete(fd_getter):
        fd = fd_getter()
        with open(os.dup(fd), 'rb', closefd=True) as rfd:
            buf = rfd.read()

            a = 'Goodbye, {0}!'.format(n)
            b = buf.decode(encoding='utf-8')

            result[0] = a == b

    proxy.GoodbyeFD(n, callback=complete)
    loop = EventLoop()
    GLib.timeout_add_seconds(3, lambda x: loop.quit(), loop)
    loop.run()
    return result


def _hello_fdtest(addr, n):
    message_bus = AddressedMessageBus(
        addr,
        error_mapper=error_mapper
    )
    proxy = message_bus.get_proxy(
        "my.testing.Example",
        "/my/testing/Example",
        client=GLibClientUnix
    )

    with tempfile.TemporaryFile(mode="wb",
                                buffering=0,
                                prefix=n) as otmp:
        otmp.write(n.encode("utf-8"))
        otmp.seek(0)

        # closefd=False here because passing a
        # file descriptor to dbus closes it
        with open(os.dup(otmp.fileno()), "rb", closefd=False) as o:
            i = proxy.HelloFD(UnixFD(o.fileno()))

            with open(os.dup(i), "rb", closefd=True) as ifile:
                buf = ifile.read()
                # can't use an assert here, because we're in
                # another address space, so return a boolean to get
                # communicated back to the server
                a = "Hello, {0}!".format(n)
                b = buf.decode("utf-8")
                return a == b


def _hello_fdtest_async(addr, n):
    result = [False]
    message_bus = AddressedMessageBus(
        addr,
        error_mapper=error_mapper
    )
    proxy = message_bus.get_proxy(
        "my.testing.Example",
        "/my/testing/Example",
        client=GLibClientUnix
    )

    def callback(fd_getter):
        fd = fd_getter()
        with open(os.dup(fd), "rb", closefd=True) as ifile:
            buf = ifile.read()
            # can't use an assert here, because we're in
            # another address space, so return a boolean to get
            # communicated back to the server
            r = "Hello, {0}!".format(n) == buf.decode("utf-8")
            result[0] = r

    with tempfile.TemporaryFile(mode="wb",
                                buffering=0,
                                prefix=n) as otmp:
        otmp.write(n.encode("utf-8"))
        otmp.seek(0)

        # closefd=False here because passing a
        # file descriptor to dbus closes it
        with open(os.dup(otmp.fileno()), "rb", closefd=False) as o:
            proxy.HelloFD(UnixFD(o.fileno()), callback=callback)
            loop = EventLoop()

            GLib.timeout_add_seconds(3, lambda x: loop.quit(), loop)

            loop.run()
            return result[0]
