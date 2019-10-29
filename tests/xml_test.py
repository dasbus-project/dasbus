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
from dasbus.xml import XMLParser, XMLGenerator


class XMLParserTestCase(unittest.TestCase):

    def is_member_test(self):
        """Test if the element is a member of an interface."""
        element = XMLParser.xml_to_element('<method name="MethodName" />')
        self.assertEqual(XMLParser.is_member(element), True)

        element = XMLParser.xml_to_element('<signal name="SignalName" />')
        self.assertEqual(XMLParser.is_member(element), True)

        element = XMLParser.xml_to_element(
            '<property '
            'access="PropertyAccess" '
            'name="PropertyName" '
            'type="PropertyType" />'
        )
        self.assertEqual(XMLParser.is_member(element), True)

    def is_interface_test(self):
        """Test if the element is an interface."""
        element = XMLParser.xml_to_element('<interface name="InterfaceName" />')
        self.assertEqual(XMLParser.is_interface(element), True)

    def is_signal_test(self):
        """Test if the element is a signal."""
        element = XMLParser.xml_to_element('<signal name="SignalName" />')
        self.assertEqual(XMLParser.is_signal(element), True)

    def is_method_test(self):
        """Test if the element is a method."""
        element = XMLParser.xml_to_element('<method name="MethodName" />')
        self.assertEqual(XMLParser.is_method(element), True)

    def is_property_test(self):
        """Test if the element is a property."""
        element = XMLParser.xml_to_element(
            '<property '
            'access="PropertyAccess" '
            'name="PropertyName" '
            'type="PropertyType" />'
        )
        self.assertEqual(XMLParser.is_property(element), True)

    def is_parameter_test(self):
        """Test if the element is a parameter."""
        element = XMLParser.xml_to_element(
            '<arg '
            'direction="ParameterDirection" '
            'name="ParameterName" '
            'type="ParameterType" />'
        )
        self.assertEqual(XMLParser.is_parameter(element), True)

    def has_name_test(self):
        """Test if the element has the specified name."""
        element = XMLParser.xml_to_element('<method name="MethodName" />')
        self.assertEqual(XMLParser.has_name(element, "MethodName"), True)
        self.assertEqual(XMLParser.has_name(element, "AnotherName"), False)

    def get_name_test(self):
        """Get the name attribute."""
        element = XMLParser.xml_to_element('<method name="MethodName" />')
        self.assertEqual(XMLParser.get_name(element), "MethodName")

    def get_type_test(self):
        """Get the type attribute."""
        element = XMLParser.xml_to_element(
            '<arg '
            'direction="ParameterDirection" '
            'name="ParameterName" '
            'type="ParameterType" />'
        )
        self.assertEqual(XMLParser.get_type(element), "ParameterType")

    def get_access_test(self):
        """Get the access attribute."""
        element = XMLParser.xml_to_element(
            '<property '
            'access="PropertyAccess" '
            'name="PropertyName" '
            'type="PropertyType" />'
        )
        self.assertEqual(XMLParser.get_access(element), "PropertyAccess")

    def get_direction_test(self):
        """Get the direction attribute."""
        element = XMLParser.xml_to_element(
            '<arg '
            'direction="ParameterDirection" '
            'name="ParameterName" '
            'type="ParameterType" />'
        )
        self.assertEqual(XMLParser.get_direction(element), "ParameterDirection")

    def get_interfaces_from_node_test(self):
        """Get interfaces from the node."""
        element = XMLParser.xml_to_element('''
        <node>
            <interface name="A" />
            <interface name="B" />
            <interface name="C" />
        </node>
        ''')
        interfaces = XMLParser.get_interfaces_from_node(element)
        self.assertEqual(interfaces.keys(), {"A", "B", "C"})


class XMLGeneratorTestCase(unittest.TestCase):

    def _compare(self, element, xml):
        self.assertEqual(
            XMLGenerator.prettify_xml(XMLGenerator.element_to_xml(element)),
            XMLGenerator.prettify_xml(xml)
        )

    def node_test(self):
        """Test the node element."""
        self._compare(XMLGenerator.create_node(), '<node />')

    def interface_test(self):
        """Test the interface element."""
        self._compare(
            XMLGenerator.create_interface("InterfaceName"),
            '<interface name="InterfaceName" />'
        )

    def parameter_test(self):
        """Test the parameter element."""
        self._compare(
            XMLGenerator.create_parameter("ParameterName",
                                          "ParameterType",
                                          "ParameterDirection"),
            '<arg '
            'direction="ParameterDirection" '
            'name="ParameterName" '
            'type="ParameterType" />')

    def property_test(self):
        """Test the property element."""
        self._compare(
            XMLGenerator.create_property("PropertyName",
                                         "PropertyType",
                                         "PropertyAccess"),
            '<property '
            'access="PropertyAccess" '
            'name="PropertyName" '
            'type="PropertyType" />'
        )

    def method_test(self):
        """Test the method element."""
        element = XMLGenerator.create_method("MethodName")
        xml = '<method name="MethodName" />'
        self._compare(element, xml)

    def signal_test(self):
        """Test the signal element."""
        element = XMLGenerator.create_signal("SignalName")
        xml = '<signal name="SignalName" />'
        self._compare(element, xml)
