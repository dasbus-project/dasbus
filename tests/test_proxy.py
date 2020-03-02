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
from unittest.mock import Mock

from dasbus.client.proxy import ObjectProxy, get_object_path


class DBusProxyTestCase(unittest.TestCase):
    """Test support for object proxies."""

    def test_get_object_path(self):
        """Test get_object_path."""
        proxy = ObjectProxy(Mock(), "my.service", "/my/path")
        self.assertEqual(get_object_path(proxy), "/my/path")

        with self.assertRaises(TypeError) as cm:
            get_object_path(None)

        self.assertEqual(
            "Invalid type 'NoneType'.",
            str(cm.exception)
        )
