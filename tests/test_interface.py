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

from dasbus.typing import Int, Str, List, Double, File, Tuple, Bool
from dasbus.server.interface import dbus_interface, dbus_class, dbus_signal, \
    get_xml, DBusSpecificationGenerator, DBusSpecificationError
from dasbus.xml import XMLGenerator


class InterfaceGeneratorTestCase(unittest.TestCase):

    def setUp(self):
        self.generator = DBusSpecificationGenerator
        self.maxDiff = None

    def _compare(self, cls, expected_xml):
        """Compare cls specification with the given xml."""
        generated_xml = get_xml(cls)  # pylint: disable=no-member

        self.assertEqual(
            XMLGenerator.prettify_xml(generated_xml),
            XMLGenerator.prettify_xml(expected_xml)
        )

    def test_exportable(self):
        """Test if the given name should be exported."""
        self.assertTrue(self.generator._is_exportable("Name"))
        self.assertTrue(self.generator._is_exportable("ValidName"))
        self.assertTrue(self.generator._is_exportable("ValidName123"))
        self.assertTrue(self.generator._is_exportable("Valid123Name456"))
        self.assertTrue(self.generator._is_exportable("VALIDNAME123"))

        self.assertFalse(self.generator._is_exportable("name"))
        self.assertFalse(self.generator._is_exportable("_Name"))
        self.assertFalse(self.generator._is_exportable("__Name"))
        self.assertFalse(self.generator._is_exportable("invalid_name"))
        self.assertFalse(self.generator._is_exportable("invalid_name_123"))
        self.assertFalse(self.generator._is_exportable("Invalid_Name"))
        self.assertFalse(self.generator._is_exportable("invalidname"))
        self.assertFalse(self.generator._is_exportable("invalid123"))
        self.assertFalse(self.generator._is_exportable("invalidName"))
        self.assertFalse(self.generator._is_exportable("123InvalidName"))

    def test_invalid_member(self):
        """Test invalid members."""

        class InvalidMemberClass(object):
            Test1 = None

        with self.assertRaises(DBusSpecificationError) as cm:
            self.generator._generate_interface(
                InvalidMemberClass,
                {},
                "my.example.Interface"
            )

        self.assertEqual(
            "Unsupported definition of DBus member 'Test1'.",
            str(cm.exception)
        )

    def test_is_method(self):
        """Test if methods are DBus methods."""

        class IsMethodClass(object):

            def Test1(self, a: Int):
                pass

            Test2 = None

            @property
            def Test3(self):
                return None

            @dbus_signal
            def Test4(self):
                pass

        self.assertTrue(self.generator._is_method(IsMethodClass.Test1))
        self.assertFalse(self.generator._is_method(IsMethodClass.Test2))
        self.assertFalse(self.generator._is_method(IsMethodClass.Test3))
        self.assertFalse(self.generator._is_method(IsMethodClass.Test4))

    def test_invalid_method(self):
        """Test invalid methods."""

        class InvalidMethodClass(object):

            def Test1(self, a):
                pass

            def Test2(self, a=None):
                pass

            def Test3(self, a, b):
                pass

            def Test4(self, a: Int, b: Str, c):
                pass

            def Test5(self, a: Int, b: Str, c) -> Int:
                pass

            def Test6(self, *arg):
                pass

            def Test7(self, **kwargs):
                pass

            def Test8(self, a: Int, b: Double, *, c, d=None):
                pass

        self._check_invalid_method(
            InvalidMethodClass.Test1,
            "Undefined type of parameter 'a'."
        )
        self._check_invalid_method(
            InvalidMethodClass.Test2,
            "Undefined type of parameter 'a'."
        )
        self._check_invalid_method(
            InvalidMethodClass.Test3,
            "Undefined type of parameter 'a'."
        )
        self._check_invalid_method(
            InvalidMethodClass.Test4,
            "Undefined type of parameter 'c'."
        )
        self._check_invalid_method(
            InvalidMethodClass.Test5,
            "Undefined type of parameter 'c'."
        )
        self._check_invalid_method(
            InvalidMethodClass.Test6,
            "Only positional or keyword arguments are allowed."
        )
        self._check_invalid_method(
            InvalidMethodClass.Test7,
            "Only positional or keyword arguments are allowed."
        )
        self._check_invalid_method(
            InvalidMethodClass.Test8,
            "Only positional or keyword arguments are allowed."
        )

    def _check_invalid_method(self, method, message):
        """Try to generate a specification for an invalid method."""
        with self.assertRaises(DBusSpecificationError) as cm:
            self.generator._generate_method(method, method.__name__)

        self.assertEqual(str(cm.exception), message)

    def test_method(self):
        """Test interface with a method."""

        @dbus_interface("my.example.Interface")
        class MethodClass(object):

            def Method1(self):
                pass

            def Method2(self, x: Int):
                pass

            def Method3(self) -> Int:
                pass

            def Method4(self, x: List[Double], y: File) -> Tuple[Int, Bool]:
                return 0, True

        expected_xml = '''
        <node>
            <!--Specifies MethodClass-->
            <interface name="my.example.Interface">
                <method name="Method1"/>
                <method name="Method2">
                    <arg direction="in" name="x" type="i"/>
                </method>
                <method name="Method3">
                    <arg direction="out" name="return" type="i"/>
                </method>
                <method name="Method4">
                    <arg direction="in" name="x" type="ad"/>
                    <arg direction="in" name="y" type="h"/>
                    <arg direction="out" name="return" type="(ib)"/>
                </method>
            </interface>
        </node>
        '''

        self._compare(MethodClass, expected_xml)

    def test_is_property(self):
        """Test property detection."""

        class IsPropertyClass(object):

            @property
            def Property1(self) -> Int:
                return 1

            def _get_property2(self):
                return 2

            Property2 = property(fget=_get_property2)

            def Property3(self) -> Int:
                return 3

            @dbus_signal
            def Property4(self):
                pass

        self.assertTrue(self.generator._is_property(
            IsPropertyClass.Property1
        ))
        self.assertTrue(self.generator._is_property(
            IsPropertyClass.Property2
        ))
        self.assertFalse(self.generator._is_property(
            IsPropertyClass.Property3
        ))
        self.assertFalse(self.generator._is_property(
            IsPropertyClass.Property4
        ))

    def test_property(self):
        """Test the interface with a property."""

        @dbus_interface("Interface", namespace=("my", "example"))
        class ReadWritePropertyClass(object):

            def __init__(self):
                self._property = 0

            @property
            def Property(self) -> Int:
                return self._property

            @Property.setter
            def Property(self, value: Int):
                self._property = value

        expected_xml = '''
        <node>
            <!--Specifies ReadWritePropertyClass-->
            <interface name="my.example.Interface">
                <property name="Property" type="i" access="readwrite" />
            </interface>
        </node>
        '''

        self._compare(ReadWritePropertyClass, expected_xml)

    def test_invalid_property(self):
        """Test the interface with an invalid property."""

        class InvalidPropertyClass(object):

            InvalidProperty = property()

            @property
            def NoHintProperty(self):
                return 1

        with self.assertRaises(DBusSpecificationError) as cm:
            self.generator._generate_property(
                InvalidPropertyClass.InvalidProperty,
                "InvalidProperty"
            )

        self.assertEqual(
            "DBus property 'InvalidProperty' is not accessible.",
            str(cm.exception)
        )

        with self.assertRaises(DBusSpecificationError) as cm:
            self.generator._generate_property(
                InvalidPropertyClass.NoHintProperty,
                "NoHintProperty"
            )

        self.assertEqual(
            "Undefined type of DBus property 'NoHintProperty'.",
            str(cm.exception)
        )

    def test_property_readonly(self):
        """Test readonly property."""

        @dbus_interface("Interface")
        class ReadonlyPropertyClass(object):

            def __init__(self):
                self._property = 0

            @property
            def Property(self) -> Int:
                return self._property

        expected_xml = '''
        <node>
            <!--Specifies ReadonlyPropertyClass-->
            <interface name="Interface">
                <property name="Property" type="i" access="read" />
            </interface>
        </node>
        '''

        self._compare(ReadonlyPropertyClass, expected_xml)

    def test_property_writeonly(self):
        """Test writeonly property."""

        @dbus_interface("Interface")
        class WriteonlyPropertyClass(object):

            def __init__(self):
                self._property = 0

            def set_property(self, x: Int):
                self._property = x

            Property = property(fset=set_property)

        expected_xml = '''
        <node>
            <!--Specifies WriteonlyPropertyClass-->
            <interface name="Interface">
                <property name="Property" type="i" access="write" />
            </interface>
        </node>
        '''

        self._compare(WriteonlyPropertyClass, expected_xml)

    def test_is_signal(self):
        """Test signal detection."""

        class IsSignalClass(object):

            @dbus_signal
            def Signal1(self):
                pass

            @dbus_signal
            def Signal2(self, x: Int, y: Double):
                pass

            Signal3 = dbus_signal()

            def Signal4(self):
                pass

            @property
            def Signal5(self):
                return None

            Signal6 = None

        self.assertTrue(self.generator._is_signal(IsSignalClass.Signal1))
        self.assertTrue(self.generator._is_signal(IsSignalClass.Signal2))
        self.assertTrue(self.generator._is_signal(IsSignalClass.Signal3))
        self.assertFalse(self.generator._is_signal(IsSignalClass.Signal4))
        self.assertFalse(self.generator._is_signal(IsSignalClass.Signal5))
        self.assertFalse(self.generator._is_signal(IsSignalClass.Signal6))

    def test_simple_signal(self):
        """Test interface with a simple signal."""

        @dbus_interface("Interface")
        class SimpleSignalClass(object):
            SimpleSignal = dbus_signal()

        expected_xml = '''
        <node>
            <!--Specifies SimpleSignalClass-->
            <interface name="Interface">
                <signal name="SimpleSignal"/>
            </interface>
        </node>
        '''

        self._compare(SimpleSignalClass, expected_xml)

    def test_signal(self):
        """Test interface with signals."""

        @dbus_interface("Interface")
        class SignalClass(object):

            @dbus_signal
            def SomethingHappened(self):
                """Signal that something happened."""
                pass

            @dbus_signal
            def SignalSomething(self, x: Int, y: Str):
                """
                Signal that something happened.

                :param x: Parameter x.
                :param y: Parameter y
                """
                pass

            def _emit_signals(self):
                self.SomethingHappened.emit()  # pylint: disable=no-member
                self.SignalSomething.emit(0, "Something!")

        expected_xml = '''
        <node>
            <!--Specifies SignalClass-->
            <interface name="Interface">
                <signal name="SignalSomething">
                    <arg direction="out" name="x" type="i"/>
                    <arg direction="out" name="y" type="s"/>
                </signal>
                <signal name="SomethingHappened"/>
            </interface>
        </node>
        '''

        self._compare(SignalClass, expected_xml)

    def test_invalid_signal(self):
        """Test interface with an invalid signal."""

        class InvalidSignalClass(object):

            @dbus_signal
            def Signal1(self, x):
                pass

            @dbus_signal
            def Signal2(self) -> Int:
                return 1

        with self.assertRaises(DBusSpecificationError) as cm:
            self.generator._generate_signal(
                InvalidSignalClass.Signal1,
                "Signal1"
            )

        self.assertEqual(
            "Undefined type of parameter 'x'.",
            str(cm.exception)
        )

        with self.assertRaises(DBusSpecificationError) as cm:
            self.generator._generate_signal(
                InvalidSignalClass.Signal2,
                "Signal2"
            )

        self.assertEqual(
            "Invalid return type of DBus signal 'Signal2'.",
            str(cm.exception)
        )

    def test_override_method(self):
        """Test interface with overridden methods."""

        @dbus_interface("A")
        class AClass(object):

            def MethodA1(self, x: Int) -> Double:
                return x + 1.0

            def MethodA2(self) -> Bool:
                return False

            def MethodA3(self, x: List[Int]):
                pass

        class BClass(AClass):

            def MethodA1(self, x: Int) -> Double:
                return x + 2.0

            def MethodB1(self) -> Str:
                return ""

        @dbus_interface("C")
        class CClass(object):

            def MethodC1(self) -> Tuple[Int, Int]:
                return 1, 2

            def MethodC2(self, x: Double):
                pass

        @dbus_interface("D")
        class DClass(BClass, CClass):

            def MethodD1(self) -> Tuple[Int, Str]:
                return 0, ""

            def MethodA3(self, x: List[Int]):
                pass

            def MethodC2(self, x: Double):
                pass

        expected_xml = '''
        <node>
            <!--Specifies DClass-->
            <interface name="A">
                <method name="MethodA1">
                    <arg direction="in" name="x" type="i"/>
                    <arg direction="out" name="return" type="d"/>
                </method>
                <method name="MethodA2">
                    <arg direction="out" name="return" type="b"/>
                </method>
                <method name="MethodA3">
                    <arg direction="in" name="x" type="ai"/>
                </method>
            </interface>
            <interface name="C">
                <method name="MethodC1">
                    <arg direction="out" name="return" type="(ii)"/>
                </method>
                <method name="MethodC2">
                    <arg direction="in" name="x" type="d"/>
                </method>
            </interface>
            <interface name="D">
                <method name="MethodB1">
                    <arg direction="out" name="return" type="s"/>
                </method>
                <method name="MethodD1">
                    <arg direction="out" name="return" type="(is)"/>
                </method>
            </interface>
        </node>
        '''

        self._compare(DClass, expected_xml)

    def test_complex(self):
        """Test complex example."""

        @dbus_interface("ComplexA")
        class ComplexClassA(object):

            def __init__(self):
                self.a = 1

            @dbus_signal
            def SignalA(self, x: Int):
                pass

            @property
            def PropertyA(self) -> Double:
                return self.a + 2.5

            def MethodA(self) -> Int:
                return self.a

            def _methodA(self):
                return None

        expected_xml = '''
        <node>
            <!--Specifies ComplexClassA-->
            <interface name="ComplexA">
                <method name="MethodA">
                    <arg direction="out" name="return" type="i"/>
                </method>
                <property access="read" name="PropertyA" type="d"/>
                <signal name="SignalA">
                   <arg direction="out" name="x" type="i"/>
                </signal>
            </interface>
        </node>
        '''

        self._compare(ComplexClassA, expected_xml)

        @dbus_interface("ComplexB")
        class ComplexClassB(ComplexClassA):

            def __init__(self):
                super().__init__()
                self.b = 2.0

            @dbus_signal
            def SignalB(self, x: Bool, y: Double, z: Tuple[Int, Int]):
                pass

            @property
            def PropertyB(self) -> Double:
                return self.b

            def MethodA(self) -> Int:
                return int(self.b)

            def MethodB(self, a: Str, b: List[Double], c: Int) -> Int:
                return int(self.b)

            def _methodB(self, x: Bool):
                pass

        expected_xml = '''
        <node>
            <!--Specifies ComplexClassB-->
           <interface name="ComplexA">
                <method name="MethodA">
                    <arg direction="out" name="return" type="i"/>
                </method>
                <property access="read" name="PropertyA" type="d"/>
                <signal name="SignalA">
                   <arg direction="out" name="x" type="i"/>
                </signal>
            </interface>
            <interface name="ComplexB">
                <method name="MethodB">
                    <arg direction="in" name="a" type="s"/>
                    <arg direction="in" name="b" type="ad"/>
                    <arg direction="in" name="c" type="i"/>
                    <arg direction="out" name="return" type="i"/>
                </method>
                <property access="read" name="PropertyB" type="d"/>
                <signal name="SignalB">
                    <arg direction="out" name="x" type="b"/>
                    <arg direction="out" name="y" type="d"/>
                    <arg direction="out" name="z" type="(ii)"/>
                </signal>
            </interface>
        </node>
        '''

        self._compare(ComplexClassB, expected_xml)

        @dbus_class
        class ComplexClassC(ComplexClassB):

            def MethodB(self, a: Str, b: List[Double], c: Int) -> Int:
                return 1

        expected_xml = '''
        <node>
            <!--Specifies ComplexClassC-->
           <interface name="ComplexA">
                <method name="MethodA">
                    <arg direction="out" name="return" type="i"/>
                </method>
                <property access="read" name="PropertyA" type="d"/>
                <signal name="SignalA">
                   <arg direction="out" name="x" type="i"/>
                </signal>
            </interface>
            <interface name="ComplexB">
                <method name="MethodB">
                    <arg direction="in" name="a" type="s"/>
                    <arg direction="in" name="b" type="ad"/>
                    <arg direction="in" name="c" type="i"/>
                    <arg direction="out" name="return" type="i"/>
                </method>
                <property access="read" name="PropertyB" type="d"/>
                <signal name="SignalB">
                    <arg direction="out" name="x" type="b"/>
                    <arg direction="out" name="y" type="d"/>
                    <arg direction="out" name="z" type="(ii)"/>
                </signal>
            </interface>
        </node>
        '''

        self._compare(ComplexClassC, expected_xml)

    def test_standard_interfaces(self):
        """Test members of standard interfaces."""

        @dbus_interface("InterfaceWithoutStandard")
        class ClassWithStandard(object):

            @property
            def Property(self) -> Int:
                return 1

            def Method(self):
                pass

            def Ping(self):
                # This method shouldn't be part of the interface
                pass

            @dbus_signal
            def PropertiesChanged(self, a, b, c):
                # This signal shouldn't be part of the interface
                pass

        expected_xml = '''
        <node>
            <!--Specifies ClassWithStandard-->
           <interface name="InterfaceWithoutStandard">
                <method name="Method" />
                <property access="read" name="Property" type="i"/>
            </interface>
        </node>
        '''

        self._compare(ClassWithStandard, expected_xml)
