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

from dasbus.typing import UnixFD, Str, get_variant, unwrap_variant
from dasbus.connection import AddressedMessageBus
from dasbus.loop import EventLoop
from dasbus.server.interface import dbus_interface
from dasbus.unix import GLibClientUnix, GLibServerUnix, \
    variant_replace_handles_with_fdlist_indices, \
    variant_replace_fdlist_indices_with_handles
from dasbus.xml import XMLGenerator

from tests.test_dbus import DBusTestCase, error_mapper

import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib

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

    def test_handle(self):
        """Test handle replacement (with UnixFDList indices)"""
        # open some file descriptors to pass around
        r, w = os.pipe()

        simple_fd = get_variant("(h)", (r,))
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(
            simple_fd)
        self.assertEqual(len(fdlist), 1)
        self.assertEqual(unwrap_variant(replaced)[0], 0)
        self.assertEqual(fdlist[0], r)

        incoming_fd = get_variant("(h)", (0,))
        restored = variant_replace_fdlist_indices_with_handles(
            incoming_fd, [w])
        self.assertEqual(unwrap_variant(restored)[0], w)

        os.close(r)
        os.close(w)

    def test_array_handles(self):
        """Test handle replacement in arrays (with UnixFDList indices)"""
        r, w = os.pipe()

        array_fd = get_variant("(ah)", ((r,w),))
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(
            array_fd)
        self.assertEqual(len(fdlist), 2)
        self.assertEqual(unwrap_variant(replaced)[0][0], 0)
        self.assertEqual(unwrap_variant(replaced)[0][1], 1)
        self.assertEqual(fdlist[0], r)
        self.assertEqual(fdlist[1], w)

        array_fd = get_variant("(ah)", ((0, 1),))
        fdlist = [r, w]
        replaced = variant_replace_fdlist_indices_with_handles(
            array_fd, fdlist)
        self.assertEqual(unwrap_variant(replaced)[0][0], r)
        self.assertEqual(unwrap_variant(replaced)[0][1], w)

        os.close(r)
        os.close(w)

        r, w = os.pipe()

        array_fd = get_variant("(av)",
                               ((get_variant('h', r),
                                 get_variant('h', w)),))
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(
            array_fd)
        self.assertEqual(len(fdlist), 2)
        self.assertEqual(unwrap_variant(unwrap_variant(replaced)[0][0]), 0)
        self.assertEqual(unwrap_variant(unwrap_variant(replaced)[0][1]), 1)
        self.assertEqual(fdlist[0], r)
        self.assertEqual(fdlist[1], w)

        array_fd = get_variant("(av)",
                               ((get_variant('h', 0),
                                 get_variant('h', 1)),))
        fdlist = [r, w]
        replaced = variant_replace_fdlist_indices_with_handles(
            array_fd, fdlist)
        self.assertEqual(unwrap_variant(unwrap_variant(replaced)[0][0]), r)
        self.assertEqual(unwrap_variant(unwrap_variant(replaced)[0][1]), w)

        os.close(r)
        os.close(w)

    def test_handle_nested(self):
        """Test handle replacement in nested containers
        (with UnixFDList indices)"""

        r, w = os.pipe()

        structure_fd = get_variant("((h))", (((r,),)))
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(
            structure_fd)
        self.assertEqual(len(fdlist), 1)
        self.assertEqual(unwrap_variant(replaced)[0][0], 0)
        self.assertEqual(fdlist[0], r)

        structure_fd = get_variant("((h))", (((0,),)))
        fdlist = [r]
        replaced = variant_replace_fdlist_indices_with_handles(
            structure_fd, fdlist)
        self.assertEqual(unwrap_variant(replaced)[0][0], r)

        os.close(r)
        os.close(w)

        r, w = os.pipe()

        var_fd = get_variant("(v)", (get_variant(UnixFD, r),))
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(
            var_fd)
        self.assertEqual(len(fdlist), 1)
        self.assertEqual(fdlist[0], r)
        self.assertEqual(unwrap_variant(unwrap_variant(replaced)[0]), 0)

        var_fd = get_variant("(v)", (get_variant(UnixFD, 0),))
        fdlist = [r]
        replaced = variant_replace_fdlist_indices_with_handles(
            var_fd, fdlist)
        self.assertEqual(unwrap_variant(unwrap_variant(replaced)[0]), r)

        os.close(r)
        os.close(w)

    def test_handle_dictionary(self):
        """Test handle replacement in dictionaries
        (with UnixFDList indices)"""

        r, w = os.pipe()

        var_fd = get_variant("(a{sh})", ({"read":r, "write":w},))
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(
            var_fd)
        self.assertEqual(len(fdlist), 2)
        self.assertEqual(fdlist[replaced[0]['read']], r)
        self.assertEqual(fdlist[replaced[0]['write']], w)

        var_fd = get_variant("(a{sh})", ({"read":0, "write":1},))
        fdlist = [r, w]
        replaced = variant_replace_fdlist_indices_with_handles(
            var_fd, fdlist)

        self.assertEqual(replaced[0]['read'], r)
        self.assertEqual(replaced[0]['write'], w)

        os.close(r)
        os.close(w)

        r, w = os.pipe()

        var_fd = get_variant("a{sh}", {"read":r, "write":w})
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(var_fd)
        self.assertEqual(len(fdlist), 2)
        self.assertEqual(fdlist[replaced['read']], r)
        self.assertEqual(fdlist[replaced['write']], w)

        var_fd = get_variant("a{sh}", {"read":0, "write":1})
        fdlist = [r, w]
        replaced = variant_replace_fdlist_indices_with_handles(var_fd, fdlist)

        self.assertEqual(replaced['read'], r)
        self.assertEqual(replaced['write'], w)

        os.close(r)
        os.close(w)

    def test_handle_dictionary_reverse(self):
        """Test handle replacement in inverted dictionaries
        (with UnixFDList indices)"""

        r, w = os.pipe()

        var_fd = get_variant("(a{hs})", ({r:"read", w:"write"},))
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(
            var_fd)
        self.assertEqual(len(fdlist), 2)

        inv = {v: k for k, v in replaced[0].items()}
        self.assertEqual(fdlist[inv['read']], r)
        self.assertEqual(fdlist[inv['write']], w)

        var_fd = get_variant("(a{hs})", ({0:"read", 1:"write"},))
        fdlist = [r, w]
        replaced = variant_replace_fdlist_indices_with_handles(
            var_fd, fdlist)

        inv = {v: k for k, v in replaced[0].items()}
        self.assertEqual(fdlist[0], inv['read'])
        self.assertEqual(fdlist[1], inv['write'])

        os.close(r)
        os.close(w)

    def test_handle_complex_dictionary(self):
        """Test handle replacement in weirder dictionaries
        (with UnixFDList indices)"""
        r, w = os.pipe()

        var_fd = get_variant("a{sv}",
                             {"read":get_variant('h', r),
                              "write":get_variant('h', w)})
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(var_fd)
        self.assertEqual(len(fdlist), 2)
        self.assertEqual(fdlist[replaced['read']], r)
        self.assertEqual(fdlist[replaced['write']], w)

        var_fd = get_variant("a{sv}",
                             {"read":get_variant('h', 0),
                              "write":get_variant('h', 1)})
        fdlist = [r, w]
        replaced = variant_replace_fdlist_indices_with_handles(var_fd, fdlist)

        self.assertEqual(replaced['read'], r)
        self.assertEqual(replaced['write'], w)

        os.close(r)
        os.close(w)

        r, w = os.pipe()

        var_fd = get_variant("a{s(h)}",
                             {"read":get_variant('(h)', (r,)),
                              "write":get_variant('(h)', (w,))})
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(var_fd)
        self.assertEqual(len(fdlist), 2)
        self.assertEqual(fdlist[replaced['read'][0]], r)
        self.assertEqual(fdlist[replaced['write'][0]], w)

        var_fd = get_variant("a{s(h)}",
                             {"read":get_variant('(h)', (0,)),
                              "write":get_variant('(h)', (1,))})
        fdlist = [r, w]
        replaced = variant_replace_fdlist_indices_with_handles(var_fd, fdlist)

        self.assertEqual(replaced['read'][0], r)
        self.assertEqual(replaced['write'][0], w)

        os.close(r)
        os.close(w)

        r, w = os.pipe()

        var_fd = get_variant("a{saa{sv}}",
                             {"fds": [{"read":get_variant('h', r),
                                       "write":get_variant('h', w)}],
                              "not-fds": [{"one":get_variant('d', 1.0),
                                           "two":get_variant('d', 2.0)}]})
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(var_fd)
        self.assertEqual(len(fdlist), 2)
        self.assertEqual(fdlist[replaced['fds'][0]['read']], r)
        self.assertEqual(fdlist[replaced['fds'][0]['write']], w)

        var_fd = get_variant("a{saa{sv}}",
                             {"fds": [{"read":get_variant('h', 0),
                                       "write":get_variant('h', 1)}],
                              "not-fds": [{"one":get_variant('d', 1.0),
                                           "two":get_variant('d', 2.0)}]})
        fdlist = [r, w]
        replaced = variant_replace_fdlist_indices_with_handles(var_fd, fdlist)

        self.assertEqual(replaced['fds'][0]['read'], r)
        self.assertEqual(replaced['fds'][0]['write'], w)

        os.close(r)
        os.close(w)

    def test_handle_null_replacement(self):
        """Test handle replacement (with UnixFDList indices)
        for variants that don't have any"""
        # now some controls
        int_fd = get_variant("(i)", (25,))
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(int_fd)
        self.assertEqual(len(fdlist), 0)
        self.assertEqual(unwrap_variant(replaced)[0], 25)

        int_fd = get_variant("(i)", (25,))
        replaced = variant_replace_fdlist_indices_with_handles(int_fd, [])
        self.assertEqual(len(fdlist), 0)
        self.assertEqual(unwrap_variant(replaced)[0], 25)

        str_fd = get_variant("s", "teststr")
        replaced, fdlist = variant_replace_handles_with_fdlist_indices(str_fd)
        self.assertEqual(len(fdlist), 0)
        self.assertEqual(unwrap_variant(replaced), "teststr")

        str_fd = get_variant("s", "teststr")
        replaced = variant_replace_fdlist_indices_with_handles(str_fd, [])
        self.assertEqual(len(fdlist), 0)
        self.assertEqual(unwrap_variant(replaced), "teststr")


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
