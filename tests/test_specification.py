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

from dasbus.specification import DBusSpecificationParser, DBusSpecification, \
    DBusSpecificationError


class SpecificationTestCase(unittest.TestCase):

    def test_from_members(self):
        """Test a specification created from members."""
        method = DBusSpecification.Method(
            name="Method",
            interface_name="A",
            in_type="()",
            out_type="(s)"
        )

        signal = DBusSpecification.Signal(
            name="Signal",
            interface_name="B",
            type="(ii)"
        )

        prop = DBusSpecification.Property(
            name="Property",
            interface_name="B",
            readable=True,
            writable=False,
            type="i"
        )

        specification = DBusSpecification()
        specification.add_member(method)
        specification.add_member(signal)
        specification.add_member(prop)

        with self.assertRaises(DBusSpecificationError) as cm:
            specification.get_member("A", "Invalid")

        self.assertEqual(
            "DBus specification has no member 'A.Invalid'.",
            str(cm.exception)
        )

        with self.assertRaises(DBusSpecificationError) as cm:
            specification.get_member("Invalid", "Method")

        self.assertEqual(
            "DBus specification has no member 'Invalid.Method'.",
            str(cm.exception)
        )

        self.assertEqual(specification.interfaces, ["A", "B"])
        self.assertEqual(specification.members, [method, signal, prop])
        self.assertEqual(specification.get_member("A", "Method"), method)
        self.assertEqual(specification.get_member("B", "Signal"), signal)
        self.assertEqual(specification.get_member("B", "Property"), prop)

    def test_from_xml(self):
        """Test a specification created from XML."""
        xml = '''
        <node>
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
        specification = DBusSpecification.from_xml(xml)
        self.assertEqual(specification.interfaces, [
            'org.freedesktop.DBus.Introspectable',
            'org.freedesktop.DBus.Peer',
            'org.freedesktop.DBus.Properties',
            'ComplexA',
            'ComplexB',
        ])

        self.assertEqual(specification.members, [
            DBusSpecification.Method(
                name='Introspect',
                interface_name='org.freedesktop.DBus.Introspectable',
                in_type=None,
                out_type='(s)'
            ),
            DBusSpecification.Method(
                name='Ping',
                interface_name='org.freedesktop.DBus.Peer',
                in_type=None,
                out_type=None
            ),
            DBusSpecification.Method(
                name='GetMachineId',
                interface_name='org.freedesktop.DBus.Peer',
                in_type=None,
                out_type='(s)'
            ),
            DBusSpecification.Method(
                name='Get',
                interface_name='org.freedesktop.DBus.Properties',
                in_type='(ss)',
                out_type='(v)'
            ),
            DBusSpecification.Method(
                name='GetAll',
                interface_name='org.freedesktop.DBus.Properties',
                in_type='(s)',
                out_type='(a{sv})'
            ),
            DBusSpecification.Method(
                name='Set',
                interface_name='org.freedesktop.DBus.Properties',
                in_type='(ssv)',
                out_type=None
            ),
            DBusSpecification.Signal(
                name='PropertiesChanged',
                interface_name='org.freedesktop.DBus.Properties',
                type='(sa{sv}as)'
            ),
            DBusSpecification.Method(
                name='MethodA',
                interface_name='ComplexA',
                in_type=None,
                out_type='(i)'
            ),
            DBusSpecification.Property(
                name='PropertyA',
                interface_name='ComplexA',
                readable=True,
                writable=False,
                type='d'
            ),
            DBusSpecification.Signal(
                name='SignalA',
                interface_name='ComplexA',
                type='(i)'
            ),
            DBusSpecification.Method(
                name='MethodB',
                interface_name='ComplexB',
                in_type='(sadi)',
                out_type='(i)'
            ),
            DBusSpecification.Property(
                name='PropertyB',
                interface_name='ComplexB',
                readable=True,
                writable=False,
                type='d'
            ),
            DBusSpecification.Signal(
                name='SignalB',
                interface_name='ComplexB',
                type='(bd(ii))'
            )
        ])


class SpecificationParserTestCase(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

    def _compare(self, xml, expected_members):
        """Compare members of the specification."""
        specification = DBusSpecification()
        DBusSpecificationParser._parse_xml(specification, xml)
        self.assertEqual(specification.members, expected_members)

    def test_method(self):
        """Test XML with methods."""
        xml = '''
        <node>
            <interface name="Interface">
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
        self._compare(xml, [
            DBusSpecification.Method(
                name='Method1',
                interface_name='Interface',
                in_type=None,
                out_type=None
            ),
            DBusSpecification.Method(
                name='Method2',
                interface_name='Interface',
                in_type='(i)',
                out_type=None
            ),
            DBusSpecification.Method(
                name='Method3',
                interface_name='Interface',
                in_type=None,
                out_type='(i)'
            ),
            DBusSpecification.Method(
                name='Method4',
                interface_name='Interface',
                in_type='(adh)',
                out_type='((ib))'
            )
        ])

    def test_property(self):
        """Test XML with a property."""
        xml = '''
        <node>
            <interface name="Interface">
                <property name="Property" type="i" access="readwrite" />
            </interface>
        </node>
        '''
        self._compare(xml, [
            DBusSpecification.Property(
                name='Property',
                interface_name='Interface',
                readable=True,
                writable=True,
                type='i'
            )
        ])

    def test_property_readonly(self):
        """Test readonly property."""
        xml = '''
        <node>
            <interface name="Interface">
                <property name="Property" type="i" access="read" />
            </interface>
        </node>
        '''
        self._compare(xml, [
            DBusSpecification.Property(
                name='Property',
                interface_name='Interface',
                readable=True,
                writable=False,
                type='i'
            )
        ])

    def test_property_writeonly(self):
        """Test writeonly property."""
        xml = '''
        <node>
            <interface name="Interface">
                <property name="Property" type="i" access="write" />
            </interface>
        </node>
        '''
        self._compare(xml, [
            DBusSpecification.Property(
                name='Property',
                interface_name='Interface',
                readable=False,
                writable=True,
                type='i'
            )
        ])

    def test_simple_signal(self):
        """Test interface with a simple signal."""
        xml = '''
        <node>
            <interface name="Interface">
                <signal name="SimpleSignal"/>
            </interface>
        </node>
        '''
        self._compare(xml, [
            DBusSpecification.Signal(
                name='SimpleSignal',
                interface_name='Interface',
                type=None
            )
        ])

    def test_signal(self):
        """Test interface with signals."""
        xml = '''
        <node>
            <interface name="Interface">
                <signal name="SignalSomething">
                    <arg direction="out" name="x" type="i"/>
                    <arg direction="out" name="y" type="s"/>
                </signal>
                <signal name="SomethingHappened"/>
            </interface>
        </node>
        '''
        self._compare(xml, [
            DBusSpecification.Signal(
                name='SignalSomething',
                interface_name='Interface',
                type='(is)'
            ),
            DBusSpecification.Signal(
                name='SomethingHappened',
                interface_name='Interface',
                type=None
            )
        ])

    def test_ignore(self):
        """Ignore invalid XML elements.."""
        xml = '''
        <node>
           <interface name="InterfaceA">
                <method name="MethodA">
                    <arg direction="out" name="return" type="i"/>
                    <ignored />
                </method>
                <property access="read" name="PropertyA" type="d"/>
                <signal name="SignalA">
                   <ignored />
                </signal>
                <ignored />
            </interface>
            <ignored />
        </node>
        '''
        self._compare(xml, [
            DBusSpecification.Method(
                name='MethodA',
                interface_name='InterfaceA',
                in_type=None,
                out_type='(i)'
            ),
            DBusSpecification.Property(
                name='PropertyA',
                interface_name='InterfaceA',
                readable=True,
                writable=False,
                type='d'
            ),
            DBusSpecification.Signal(
                name='SignalA',
                interface_name='InterfaceA',
                type=None
            )
        ])

        self._compare("<ignored />", [])

    def test_standard_interfaces(self):
        """Test with the standard interfaces."""
        specification = DBusSpecificationParser.parse_specification('<node />')
        self.assertEqual(specification.members, [
            DBusSpecification.Method(
                name='Introspect',
                interface_name='org.freedesktop.DBus.Introspectable',
                in_type=None,
                out_type='(s)'
            ),
            DBusSpecification.Method(
                name='Ping',
                interface_name='org.freedesktop.DBus.Peer',
                in_type=None,
                out_type=None
            ),
            DBusSpecification.Method(
                name='GetMachineId',
                interface_name='org.freedesktop.DBus.Peer',
                in_type=None,
                out_type='(s)'
            ),
            DBusSpecification.Method(
                name='Get',
                interface_name='org.freedesktop.DBus.Properties',
                in_type='(ss)',
                out_type='(v)'
            ),
            DBusSpecification.Method(
                name='GetAll',
                interface_name='org.freedesktop.DBus.Properties',
                in_type='(s)',
                out_type='(a{sv})'
            ),
            DBusSpecification.Method(
                name='Set',
                interface_name='org.freedesktop.DBus.Properties',
                in_type='(ssv)',
                out_type=None
            ),
            DBusSpecification.Signal(
                name='PropertiesChanged',
                interface_name='org.freedesktop.DBus.Properties',
                type='(sa{sv}as)'
            )
        ])
