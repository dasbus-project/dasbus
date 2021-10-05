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

from typing import Set

from dasbus.typing import get_dbus_type, is_base_type, get_native, \
    get_variant, get_variant_type, Int, Int16, Int32, Int64, UInt16, UInt32, \
    UInt64, Bool, Byte, Str, Dict, List, Tuple, Variant, Double, ObjPath, \
    UnixFD, unwrap_variant, get_type_name, is_tuple_of_one, get_type_arguments

import gi
gi.require_version("GLib", "2.0")
from gi.repository import GLib


class DBusTypingTests(unittest.TestCase):

    def _compare(self, type_hint, expected_string):
        """Compare generated and expected types."""
        # Generate a type string.
        dbus_type = get_dbus_type(type_hint)
        self.assertEqual(dbus_type, expected_string)
        self.assertTrue(GLib.VariantType.string_is_valid(dbus_type))

        # Create a variant type from a type hint.
        variant_type = get_variant_type(type_hint)
        self.assertIsInstance(variant_type, GLib.VariantType)
        self.assertEqual(variant_type.dup_string(), expected_string)

        expected_type = GLib.VariantType.new(expected_string)
        self.assertTrue(expected_type.equal(variant_type))

        # Create a variant type from a type string.
        variant_type = get_variant_type(expected_string)
        self.assertIsInstance(variant_type, GLib.VariantType)
        self.assertTrue(expected_type.equal(variant_type))

        # Test the is_tuple_of_one function.
        expected_value = is_base_type(type_hint, Tuple) \
            and len(get_type_arguments(type_hint)) == 1

        self.assertEqual(is_tuple_of_one(type_hint), expected_value)
        self.assertEqual(is_tuple_of_one(expected_string), expected_value)

        self.assertTrue(is_tuple_of_one(Tuple[type_hint]))
        self.assertTrue(is_tuple_of_one("({})".format(expected_string)))

    def test_unknown(self):
        """Test the unknown type."""

        class UnknownType:
            pass

        with self.assertRaises(TypeError) as cm:
            get_dbus_type(UnknownType)

        self.assertEqual(
            "Invalid DBus type 'UnknownType'.",
            str(cm.exception)
        )

        with self.assertRaises(TypeError) as cm:
            get_dbus_type(List[UnknownType])

        self.assertEqual(
            "Invalid DBus type 'UnknownType'.",
            str(cm.exception)
        )

        with self.assertRaises(TypeError) as cm:
            get_dbus_type(Tuple[Int, Str, UnknownType])

        self.assertEqual(
            "Invalid DBus type 'UnknownType'.",
            str(cm.exception)
        )

        with self.assertRaises(TypeError) as cm:
            get_dbus_type(Dict[Int, UnknownType])

        self.assertEqual(
            "Invalid DBus type 'UnknownType'.",
            str(cm.exception)
        )

    def test_invalid(self):
        """Test the invalid types."""
        msg = "Invalid DBus type of dictionary key: '{}'"

        with self.assertRaises(TypeError) as cm:
            get_dbus_type(Dict[List[Bool], Bool])

        self.assertEqual(
            msg.format(get_type_name(List[Bool])),
            str(cm.exception)
        )

        with self.assertRaises(TypeError) as cm:
            get_dbus_type(Dict[Variant, Int])

        self.assertEqual(
            msg.format("Variant"),
            str(cm.exception)
        )

        with self.assertRaises(TypeError) as cm:
            get_dbus_type(Tuple[Int, Double, Dict[Tuple[Int, Int], Bool]])

        self.assertEqual(
            msg.format(get_type_name(Tuple[Int, Int])),
            str(cm.exception)
        )

        msg = "Invalid DBus type '{}'."

        with self.assertRaises(TypeError) as cm:
            get_dbus_type(Set[Int])

        self.assertEqual(
            msg.format(get_type_name(Set[Int])),
            str(cm.exception),
        )

    def test_simple(self):
        """Test simple types."""
        self._compare(int, "i")
        self._compare(bool, "b")
        self._compare(float, "d")
        self._compare(str, "s")

    def test_basic(self):
        """Test basic types."""
        self._compare(Int, "i")
        self._compare(Bool, "b")
        self._compare(Double, "d")
        self._compare(Str, "s")
        self._compare(ObjPath, "o")
        self._compare(UnixFD, "h")
        self._compare(Variant, "v")

    def test_int(self):
        """Test integer types."""
        self._compare(Byte, "y")
        self._compare(Int16, "n")
        self._compare(UInt16, "q")
        self._compare(Int32, "i")
        self._compare(UInt32, "u")
        self._compare(Int64, "x")
        self._compare(UInt64, "t")

    def test_container(self):
        """Test container types."""
        self._compare(Tuple[Bool], "(b)")
        self._compare(Tuple[Int, Str], "(is)")
        self._compare(Tuple[UnixFD, Variant, Double], "(hvd)")

        self._compare(List[Int], "ai")
        self._compare(List[Bool], "ab")
        self._compare(List[UnixFD], "ah")
        self._compare(List[ObjPath], "ao")

        self._compare(Dict[Str, Int], "a{si}")
        self._compare(Dict[Int, Bool], "a{ib}")

    def test_alias(self):
        """Test type aliases."""
        AliasType = List[Double]
        self._compare(Dict[Str, AliasType], "a{sad}")

    def test_depth(self):
        """Test difficult type structures."""
        self._compare(Tuple[Int, Tuple[Str, Str]], "(i(ss))")
        self._compare(Tuple[Tuple[Tuple[Int]]], "(((i)))")
        self._compare(Tuple[Bool, Tuple[Tuple[Int], Str]], "(b((i)s))")

        self._compare(List[List[List[Int]]], "aaai")
        self._compare(List[Tuple[Dict[Str, Int]]], "a(a{si})")
        self._compare(List[Dict[Str, Tuple[UnixFD, Variant]]], "aa{s(hv)}")

        self._compare(Dict[Str, List[Bool]], "a{sab}")
        self._compare(Dict[Str, Tuple[Int, Int, Double]], "a{s(iid)}")
        self._compare(Dict[Str, Tuple[Int, Int, Dict[Int, Str]]],
                      "a{s(iia{is})}")

    def test_base_type(self):
        """Test the base type checks."""
        self.assertEqual(is_base_type(Int, Int), True)
        self.assertEqual(is_base_type(UInt16, UInt16), True)
        self.assertEqual(is_base_type(Variant, Variant), True)

        self.assertEqual(is_base_type(Int, Bool), False)
        self.assertEqual(is_base_type(Bool, List), False)
        self.assertEqual(is_base_type(UInt16, Dict), False)
        self.assertEqual(is_base_type(UInt16, Int), False)
        self.assertEqual(is_base_type(Variant, Tuple), False)

        self.assertEqual(is_base_type(List[Int], List), True)
        self.assertEqual(is_base_type(List[Bool], List), True)
        self.assertEqual(is_base_type(List[Variant], List), True)

        self.assertEqual(is_base_type(Tuple[Int], Tuple), True)
        self.assertEqual(is_base_type(Tuple[Bool], Tuple), True)
        self.assertEqual(is_base_type(Tuple[Variant], Tuple), True)

        self.assertEqual(is_base_type(Dict[Str, Int], Dict), True)
        self.assertEqual(is_base_type(Dict[Str, Bool], Dict), True)
        self.assertEqual(is_base_type(Dict[Str, Variant], Dict), True)

        self.assertEqual(is_base_type(List[Int], Tuple), False)
        self.assertEqual(is_base_type(Tuple[Bool], Dict), False)
        self.assertEqual(is_base_type(Dict[Str, Variant], List), False)

    def test_base_class(self):
        """Test the base class checks."""
        class Data(object):
            pass

        class DataA(Data):
            pass

        class DataB(Data):
            pass

        self.assertEqual(is_base_type(Data, Data), True)
        self.assertEqual(is_base_type(DataA, Data), True)
        self.assertEqual(is_base_type(DataB, Data), True)

        self.assertEqual(is_base_type(Data, DataA), False)
        self.assertEqual(is_base_type(Data, DataB), False)
        self.assertEqual(is_base_type(DataA, DataB), False)
        self.assertEqual(is_base_type(DataB, DataA), False)

        self.assertEqual(is_base_type(List[Data], List), True)
        self.assertEqual(is_base_type(Tuple[DataA], Tuple), True)
        self.assertEqual(is_base_type(Dict[Str, DataB], Dict), True)


class DBusTypingVariantTests(unittest.TestCase):

    def _test_variant(self, type_hint, expected_string, value):
        """Create a variant."""
        # Create a variant from a type hint.
        v1 = get_variant(type_hint, value)
        self.assertTrue(isinstance(v1, Variant))
        self.assertEqual(v1.format_string, expected_string)
        self.assertEqual(v1.unpack(), value)
        self.assertEqual(unwrap_variant(v1), value)

        v2 = Variant(expected_string, value)
        self.assertTrue(v2.equal(v1))

        self.assertEqual(get_native(v1), value)
        self.assertEqual(get_native(v1), get_native(v2))
        self.assertEqual(get_native(value), value)

        # Create a variant from a type string.
        v3 = get_variant(expected_string, value)
        self.assertTrue(isinstance(v3, Variant))
        self.assertTrue(v2.equal(v3))

    def test_variant_invalid(self):
        """Test invalid variants."""

        class UnknownType:
            pass

        with self.assertRaises(TypeError) as cm:
            get_variant(UnknownType, 1)

        self.assertEqual(
            "Invalid DBus type 'UnknownType'.",
            str(cm.exception)
        )

        with self.assertRaises(TypeError) as cm:
            get_variant(Int, None)

        self.assertEqual(
            "Invalid DBus value 'None'.",
            str(cm.exception)
        )

        with self.assertRaises(TypeError):
            get_variant(List[Int], True)

    def test_variant_basic(self):
        """Test variants with basic types."""
        self._test_variant(Int, "i", 1)
        self._test_variant(Bool, "b", True)
        self._test_variant(Double, "d", 1.0)
        self._test_variant(Str, "s", "Hi!")
        self._test_variant(ObjPath, "o", "/org/something")

    def test_variant_int(self):
        """Test variants with integer types."""
        self._test_variant(Int16, "n", 2)
        self._test_variant(UInt16, "q", 3)
        self._test_variant(Int32, "i", 4)
        self._test_variant(UInt32, "u", 5)
        self._test_variant(Int64, "x", 6)
        self._test_variant(UInt64, "t", 7)

    def test_variant_container(self):
        """Test variants with container types."""
        self._test_variant(Tuple[Bool], "(b)", (False,))
        self._test_variant(Tuple[Int, Str], "(is)", (0, "zero"))

        self._test_variant(List[Int], "ai", [1, 2, 3])
        self._test_variant(List[Bool], "ab", [True, False, True])

        self._test_variant(Dict[Str, Int], "a{si}", {"a": 1, "b": 2})
        self._test_variant(Dict[Int, Bool], "a{ib}", {1: True, 2: False})

    def test_variant_alias(self):
        """Test variants with type aliases."""
        AliasType = List[Double]
        self._test_variant(Dict[Str, AliasType], "a{sad}", {
            "test": [1.1, 2.2]
        })

    def _test_native(self, variants, values):
        """Test native values of variants."""
        for variant, value in zip(variants, values):
            self.assertEqual(get_native(variant), value)

        self.assertEqual(get_native(tuple(variants)), tuple(values))
        self.assertEqual(get_native(list(variants)), list(values))
        self.assertEqual(get_native(dict(enumerate(variants))),
                         dict(enumerate(values)))

        variant = get_variant(
            Tuple[Variant, Variant, Variant, Variant],
            tuple(variants)
        )
        self.assertEqual(unwrap_variant(variant), tuple(variants))

        variant = get_variant(
            List[Variant],
            list(variants)
        )
        self.assertEqual(unwrap_variant(variant), list(variants))

        variant = get_variant(
            Dict[Int, Variant],
            dict(enumerate(variants))
        )
        self.assertEqual(unwrap_variant(variant), dict(enumerate(variants)))

    def test_basic_native(self):
        """Test get_native with basic variants."""
        self._test_native(
            [
                get_variant(Double, 1.2),
                get_variant(List[Int], [0, -1]),
                get_variant(Tuple[Bool, Bool], (True, False)),
                get_variant(Dict[Str, Int], {"key": 0}),
            ],
            [
                1.2,
                [0, -1],
                (True, False),
                {"key": 0}
            ]
        )

    def test_complex_native(self):
        """Test get_native with complex variants."""
        self._test_native(
            [
                get_variant(Variant, get_variant(Double, 1.2)),
                get_variant(List[Variant], [
                    get_variant(Int, 0),
                    get_variant(Int, -1)
                ]),
                get_variant(Tuple[Variant, Bool], (
                    get_variant(Bool, True),
                    False
                )),
                get_variant(Dict[Str, Variant], {
                    "key": get_variant(Int, 0)
                })
            ],
            [
                1.2,
                [0, -1],
                (True, False),
                {"key": 0}
            ]
        )
