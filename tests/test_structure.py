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

from dasbus.typing import get_variant, get_native, Int, Str, List, Bool, \
    Dict, Structure, Variant
from dasbus.structure import DBusData, DBusStructureError, compare_data, \
    generate_string_from_data


class DBusStructureTestCase(unittest.TestCase):
    """Test the DBus structure support."""

    def test_empty_structure(self):
        with self.assertRaises(DBusStructureError) as cm:
            class NoData(DBusData):
                pass

            NoData()

        self.assertEqual(str(cm.exception), "No fields found.")

    def test_readonly_structure(self):
        with self.assertRaises(DBusStructureError) as cm:
            class ReadOnlyData(DBusData):
                @property
                def x(self) -> Int:
                    return 1

            ReadOnlyData()

        self.assertEqual(str(cm.exception), "Field 'x' cannot be set.")

    def test_writeonly_structure(self):
        with self.assertRaises(DBusStructureError) as cm:
            class WriteOnlyData(DBusData):
                def __init__(self):
                    self._x = 0

                def set_x(self, x):
                    self._x = x

                x = property(None, set_x)

            WriteOnlyData()

        self.assertEqual(str(cm.exception), "Field 'x' cannot be get.")

    def test_no_type_structure(self):
        with self.assertRaises(DBusStructureError) as cm:
            class NoTypeData(DBusData):
                def __init__(self):
                    self._x = 0

                @property
                def x(self):
                    return self._x

                @x.setter
                def x(self, x):
                    self._x = x

            NoTypeData()

        self.assertEqual(str(cm.exception), "Field 'x' has unknown type.")

    class SkipData(DBusData):

        class_attribute = 1

        def __init__(self):
            self._x = 0
            self._y = 1

        @property
        def x(self) -> Int:
            return self._x

        @property
        def _private_property(self):
            return 1

        @x.setter
        def x(self, x):
            self._x = x

        def method(self):
            pass

    def test_skip_members(self):
        data = self.SkipData()

        structure = self.SkipData.to_structure(data)
        self.assertEqual(structure, {
            'x': get_variant(Int, 0)
        })

        data = self.SkipData.from_structure({
            'x': get_variant(Int, 10)
        })

        self.assertEqual(data.x, 10)

    class SimpleData(DBusData):

        def __init__(self):
            self._x = 0

        @property
        def x(self) -> Int:
            return self._x

        @x.setter
        def x(self, x):
            self._x = x

    def test_get_simple_structure(self):
        data = self.SimpleData()
        self.assertEqual(data.x, 0)

        structure = self.SimpleData.to_structure(data)
        self.assertEqual(structure, {'x': get_variant(Int, 0)})

        data.x = 10
        self.assertEqual(data.x, 10)

        structure = self.SimpleData.to_structure(data)
        self.assertEqual(structure, {'x': get_variant(Int, 10)})

    def test_get_simple_structure_list(self):
        d1 = self.SimpleData()
        d1.x = 1

        d2 = self.SimpleData()
        d2.x = 2

        d3 = self.SimpleData()
        d3.x = 3

        structures = self.SimpleData.to_structure_list([d1, d2, d3])

        self.assertEqual(structures, [
            {'x': get_variant(Int, 1)},
            {'x': get_variant(Int, 2)},
            {'x': get_variant(Int, 3)}
        ])

    def test_apply_simple_structure(self):
        data = self.SimpleData()
        self.assertEqual(data.x, 0)

        structure = {'x': get_variant(Int, 10)}
        data = self.SimpleData.from_structure(structure)

        self.assertEqual(data.x, 10)

    def test_apply_simple_invalid_structure(self):
        with self.assertRaises(DBusStructureError) as cm:
            self.SimpleData.from_structure({'y': get_variant(Int, 10)})

        self.assertEqual(str(cm.exception), "Field 'y' doesn't exist.")

    def test_apply_simple_structure_list(self):
        s1 = {'x': get_variant(Int, 1)}
        s2 = {'x': get_variant(Int, 2)}
        s3 = {'x': get_variant(Int, 3)}

        data = self.SimpleData.from_structure_list([s1, s2, s3])

        self.assertEqual(len(data), 3)
        self.assertEqual(data[0].x, 1)
        self.assertEqual(data[1].x, 2)
        self.assertEqual(data[2].x, 3)

    def test_compare_simple_structure(self):
        data = self.SimpleData()

        self.assertTrue(compare_data(data, data))
        self.assertTrue(compare_data(data, self.SimpleData()))

        self.assertFalse(compare_data(data, None))
        self.assertFalse(compare_data(None, data))

        self.assertTrue(compare_data(
            self.SimpleData.from_structure({'x': get_variant(Int, 10)}),
            self.SimpleData.from_structure({'x': get_variant(Int, 10)})
        ))

        self.assertFalse(compare_data(
            self.SimpleData.from_structure({'x': get_variant(Int, 10)}),
            self.SimpleData.from_structure({'x': get_variant(Int, 9)})
        ))

    class OtherData(DBusData):

        def __init__(self):
            self._x = 0

        @property
        def x(self) -> Int:
            return self._x

        @x.setter
        def x(self, x):
            self._x = x

    def test_get_structure_from_invalid_type(self):
        data = self.OtherData()

        with self.assertRaises(TypeError) as cm:
            self.SimpleData.to_structure(data)

        self.assertEqual(str(cm.exception), "Invalid type 'OtherData'.")

    def test_apply_structure_with_invalid_type(self):
        structure = ["x"]

        with self.assertRaises(TypeError) as cm:
            self.SimpleData.from_structure(structure)

        self.assertEqual(str(cm.exception), "Invalid type 'list'.")

    def test_apply_structure_with_invalid_type_variant(self):
        structure = get_variant(List[Structure], [{'x': get_variant(Int, 10)}])

        with self.assertRaises(TypeError) as cm:
            self.SimpleData.from_structure_list(structure)

        self.assertEqual(str(cm.exception), "Invalid type 'Variant'.")

    class ComplicatedData(DBusData):

        def __init__(self):
            self._very_long_property_name = ""
            self._bool_list = []
            self._dictionary = {}

        @property
        def dictionary(self) -> Dict[Int, Str]:
            return self._dictionary

        @dictionary.setter
        def dictionary(self, value):
            self._dictionary = value

        @property
        def bool_list(self) -> List[Bool]:
            return self._bool_list

        @bool_list.setter
        def bool_list(self, value):
            self._bool_list = value

        @property
        def very_long_property_name(self) -> Str:
            return self._very_long_property_name

        @very_long_property_name.setter
        def very_long_property_name(self, value):
            self._very_long_property_name = value

    def test_get_complicated_structure(self):
        data = self.ComplicatedData()
        data.dictionary = {1: "1", 2: "2"}
        data.bool_list = [True, False, False]
        data.very_long_property_name = "My String Value"

        self.assertEqual(
            {
                'dictionary': get_variant(
                    Dict[Int, Str], {1: "1", 2: "2"}
                ),
                'bool-list': get_variant(
                    List[Bool], [True, False, False]
                ),
                'very-long-property-name': get_variant(
                    Str, "My String Value"
                )
            },
            self.ComplicatedData.to_structure(data)
        )

    def test_apply_complicated_structure(self):
        data = self.ComplicatedData.from_structure(
            {
                'dictionary': get_variant(
                    Dict[Int, Str], {1: "1", 2: "2"}
                ),
                'bool-list': get_variant(
                    List[Bool], [True, False, False]
                ),
                'very-long-property-name': get_variant(
                    Str, "My String Value"
                )
            }
        )

        self.assertEqual(data.dictionary, {1: "1", 2: "2"})
        self.assertEqual(data.bool_list, [True, False, False])
        self.assertEqual(data.very_long_property_name, "My String Value")

    def test_compare_complicated_structure(self):
        self.assertTrue(compare_data(
            self.ComplicatedData(),
            self.ComplicatedData(),
        ))

        self.assertFalse(compare_data(
            self.ComplicatedData(),
            self.SimpleData()
        ))

        self.assertFalse(compare_data(
            self.SimpleData(),
            self.ComplicatedData()
        ))

        self.assertTrue(compare_data(
            self.ComplicatedData.from_structure(
                {
                    'dictionary': get_variant(
                        Dict[Int, Str], {1: "1", 2: "2"}
                    ),
                    'bool-list': get_variant(
                        List[Bool], [True, False, False]
                    ),
                    'very-long-property-name': get_variant(
                        Str, "My String Value"
                    )
                }
            ),
            self.ComplicatedData.from_structure(
                {
                    'dictionary': get_variant(
                        Dict[Int, Str], {1: "1", 2: "2"}
                    ),
                    'bool-list': get_variant(
                        List[Bool], [True, False, False]
                    ),
                    'very-long-property-name': get_variant(
                        Str, "My String Value"
                    )
                }
            )
        ))

        self.assertFalse(compare_data(
            self.ComplicatedData.from_structure(
                {
                    'dictionary': get_variant(
                        Dict[Int, Str], {1: "1", 2: "2"}
                    ),
                    'bool-list': get_variant(
                        List[Bool], [True, False, False]
                    ),
                    'very-long-property-name': get_variant(
                        Str, "My String Value"
                    )
                }
            ),
            self.ComplicatedData.from_structure(
                {
                    'dictionary': get_variant(
                        Dict[Int, Str], {1: "1", 2: "2"}
                    ),
                    'bool-list': get_variant(
                        List[Bool], [True, False, True]
                    ),
                    'very-long-property-name': get_variant(
                        Str, "My String Value"
                    )
                }
            )
        ))

    def test_get_native_complicated_structure(self):
        data = self.ComplicatedData.from_structure({
            'dictionary': get_variant(
                Dict[Int, Str], {1: "1", 2: "2"}
            ),
            'bool-list': get_variant(
                List[Bool], [True, False, False]
            ),
            'very-long-property-name': get_variant(
                Str, "My String Value"
            )
        })

        structure = self.ComplicatedData.to_structure(
            data
        )

        dictionary = {
            'dictionary': {1: "1", 2: "2"},
            'bool-list': [True, False, False],
            'very-long-property-name': "My String Value"
        }

        self.assertEqual(get_native(structure), dictionary)
        self.assertEqual(get_native(dictionary), dictionary)

    class StringData(DBusData):

        def __init__(self):
            self._a = 1
            self._b = ""
            self._c = []
            self._d = []

        @property
        def a(self) -> Int:
            return self._a

        @a.setter
        def a(self, value):
            self._a = value

        @property
        def b(self) -> Str:
            return self._b

        @b.setter
        def b(self, value):
            self._b = value

        @property
        def c(self) -> List[Bool]:
            return self._c

        @c.setter
        def c(self, value):
            self._c = value

    def test_string_representation(self):
        data = self.StringData()

        expected = "StringData(a=1, b='', c=[])"
        self.assertEqual(expected, repr(data))
        self.assertEqual(expected, str(data))

        data.a = 123
        data.b = "HELLO"
        data.c = [True, False]

        expected = "StringData(a=123, b='HELLO', c=[True, False])"
        self.assertEqual(expected, repr(data))
        self.assertEqual(expected, str(data))

    class AdvancedStringData(DBusData):

        def __init__(self):
            self._a = ""
            self._b = ""
            self._c = ""

        @property
        def a(self) -> Str:
            return self._a

        @a.setter
        def a(self, value):
            self._a = value

        @property
        def b(self) -> Str:
            return self._b

        @b.setter
        def b(self, value):
            self._b = value

        @property
        def c(self) -> Str:
            return self._c

        @c.setter
        def c(self, value):
            self._c = value

        def __repr__(self):
            return generate_string_from_data(
                obj=self,
                skip=["b"],
                add={"b_is_set": bool(self.b)}
            )

    def test_advanced_string_representation(self):
        data = self.AdvancedStringData()

        expected = "AdvancedStringData(a='', b_is_set=False, c='')"
        self.assertEqual(expected, repr(data))
        self.assertEqual(expected, str(data))

        data.a = "A"
        data.b = "B"
        data.c = "C"

        expected = "AdvancedStringData(a='A', b_is_set=True, c='C')"
        self.assertEqual(expected, repr(data))
        self.assertEqual(expected, str(data))

    def test_generate_string_from_invalid_type(self):
        with self.assertRaises(DBusStructureError) as cm:
            generate_string_from_data({"x": 1})

        self.assertEqual(
            str(cm.exception),
            "Fields are not defined at '__dbus_fields__'."
        )

    def test_nested_structure(self):
        class SimpleData(DBusData):

            def __init__(self):
                self._x = 0

            @property
            def x(self) -> Int:
                return self._x

            @x.setter
            def x(self, value):
                self._x = value

        class SecretData(DBusData):

            def __init__(self):
                self._y = ""

            @property
            def y(self) -> Str:
                return self._y

            @y.setter
            def y(self, value):
                self._y = value

            def __repr__(self):
                return generate_string_from_data(
                    self, skip=["y"], add={"y_set": bool(self.y)}
                )

        class NestedData(DBusData):

            def __init__(self):
                self._attr = SimpleData()
                self._secret = SecretData()
                self._list = []

            @property
            def attr(self) -> SimpleData:
                return self._attr

            @attr.setter
            def attr(self, value):
                self._attr = value

            @property
            def secret(self) -> SecretData:
                return self._secret

            @secret.setter
            def secret(self, value):
                self._secret = value

            @property
            def list(self) -> List[SimpleData]:
                return self._list

            @list.setter
            def list(self, value):
                self._list = value

        data = NestedData()
        expected = \
            "NestedData(" \
            "attr=SimpleData(x=0), " \
            "list=[], " \
            "secret=SecretData(y_set=False))"

        self.assertEqual(str(data), expected)
        self.assertEqual(repr(data), expected)

        data.attr.x = -1
        data.secret.y = "SECRET"

        for x in range(2):
            item = SimpleData()
            item.x = x
            data.list.append(item)

        expected = \
            "NestedData(" \
            "attr=SimpleData(x=-1), " \
            "list=[SimpleData(x=0), SimpleData(x=1)], " \
            "secret=SecretData(y_set=True))"

        self.assertEqual(str(data), expected)
        self.assertEqual(repr(data), expected)

        self.assertEqual(NestedData.to_structure(data), {
            'attr': get_variant(Structure, {
                'x': get_variant(Int, -1)
            }),
            'secret': get_variant(Structure, {
                'y': get_variant(Str, "SECRET")
            }),
            'list': get_variant(List[Structure], [
                {'x': get_variant(Int, 0)},
                {'x': get_variant(Int, 1)}
            ])
        })

        dictionary = {
            'attr': {'x': 10},
            'secret': {'y': "SECRET"},
            'list': [{'x': 200}, {'x': 300}]
        }

        structure = {
            'attr': get_variant(Dict[Str, Variant], {
                'x': get_variant(Int, 10)
            }),
            'secret': get_variant(Dict[Str, Variant], {
                'y': get_variant(Str, "SECRET")
            }),
            'list': get_variant(List[Dict[Str, Variant]], [
                {'x': get_variant(Int, 200)},
                {'x': get_variant(Int, 300)}
            ])
        }

        data = NestedData.from_structure(structure)
        self.assertEqual(data.attr.x, 10)
        self.assertEqual(data.secret.y, "SECRET")
        self.assertEqual(len(data.list), 2)
        self.assertEqual(data.list[0].x, 200)
        self.assertEqual(data.list[1].x, 300)

        structure = NestedData.to_structure(data)
        self.assertEqual(get_native(structure), dictionary)
