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

from dasbus.typing import get_variant, \
    UnixFD, unwrap_variant, \
    variant_replace_handles_with_fdlist_indices, \
    variant_replace_fdlist_indices_with_handles
import os


class DBusHandleTests(unittest.TestCase):

    def test_handle(self):
        """Test handle replacement (with UnixFDList indices)"""
        #open some file descriptors to pass around
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
        #now some controls
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
