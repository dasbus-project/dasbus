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
from dasbus.namespace import get_dbus_name, get_dbus_path, \
    get_namespace_from_name


class DBusNamespaceTestCase(unittest.TestCase):

    def test_dbus_name(self):
        """Test DBus path."""
        self.assertEqual(get_dbus_name(), "")
        self.assertEqual(get_dbus_name("a"), "a")
        self.assertEqual(get_dbus_name("a", "b"), "a.b")
        self.assertEqual(get_dbus_name("a", "b", "c"), "a.b.c")
        self.assertEqual(get_dbus_name("org", "freedesktop", "DBus"),
                         "org.freedesktop.DBus")

    def test_dbus_path(self):
        """Test DBus path."""
        self.assertEqual(get_dbus_path(), "/")
        self.assertEqual(get_dbus_path("a"), "/a")
        self.assertEqual(get_dbus_path("a", "b"), "/a/b")
        self.assertEqual(get_dbus_path("a", "b", "c"), "/a/b/c")
        self.assertEqual(get_dbus_path("org", "freedesktop", "DBus"),
                         "/org/freedesktop/DBus")

    def test_namespace(self):
        """Test namespaces."""
        self.assertEqual(get_namespace_from_name("a"), ("a",))
        self.assertEqual(get_namespace_from_name("a.b"), ("a", "b"))
        self.assertEqual(get_namespace_from_name("a.b.c"), ("a", "b", "c"))
        self.assertEqual(get_namespace_from_name("org.freedesktop.DBus"),
                         ("org", "freedesktop", "DBus"))
