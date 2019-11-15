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

from dasbus.server.interface import dbus_signal
from dasbus.signal import Signal


class DBusSignalTestCase(unittest.TestCase):
    """Test DBus signals."""

    def test_create_signal(self):
        """Create a signal."""
        class Interface(object):

            @dbus_signal
            def Signal(self):
                pass

        interface = Interface()
        signal = interface.Signal
        self.assertIsInstance(signal, Signal)
        self.assertTrue(hasattr(interface, "__dbus_signal_signal"))
        self.assertEqual(getattr(interface, "__dbus_signal_signal"), signal)

    def test_emit_signal(self):
        """Emit a signal."""
        class Interface(object):

            @dbus_signal
            def Signal(self, a, b, c):
                pass

        interface = Interface()
        signal = interface.Signal

        callback = Mock()
        signal.connect(callback)  # pylint: disable=no-member

        signal.emit(1, 2, 3)  # pylint: disable=no-member
        callback.assert_called_once_with(1, 2, 3)
        callback.reset_mock()

        signal.emit(4, 5, 6)  # pylint: disable=no-member
        callback.assert_called_once_with(4, 5, 6)
        callback.reset_mock()

    def test_disconnect_signal(self):
        """Disconnect a signal."""
        class Interface(object):

            @dbus_signal
            def Signal(self):
                pass

        interface = Interface()
        callback = Mock()
        interface.Signal.connect(callback)  # pylint: disable=no-member

        interface.Signal()
        callback.assert_called_once_with()
        callback.reset_mock()

        interface.Signal.disconnect(callback)  # pylint: disable=no-member
        interface.Signal()
        callback.assert_not_called()

        interface.Signal.connect(callback)  # pylint: disable=no-member
        interface.Signal.disconnect()  # pylint: disable=no-member
        interface.Signal()
        callback.assert_not_called()

    def test_signals(self):
        """Test a class with two signals."""
        class Interface(object):

            @dbus_signal
            def Signal1(self):
                pass

            @dbus_signal
            def Signal2(self):
                pass

        interface = Interface()
        signal1 = interface.Signal1
        signal2 = interface.Signal2

        self.assertNotEqual(signal1, signal2)

        callback1 = Mock()
        signal1.connect(callback1)  # pylint: disable=no-member

        callback2 = Mock()
        signal2.connect(callback2)  # pylint: disable=no-member

        signal1.emit()  # pylint: disable=no-member
        callback1.assert_called_once_with()
        callback2.assert_not_called()
        callback1.reset_mock()

        signal2.emit()  # pylint: disable=no-member
        callback1.assert_not_called()
        callback2.assert_called_once_with()

    def test_instances(self):
        """Test two instances of the class with a signal."""
        class Interface(object):

            @dbus_signal
            def Signal(self):
                pass

        interface1 = Interface()
        signal1 = interface1.Signal

        interface2 = Interface()
        signal2 = interface2.Signal
        self.assertNotEqual(signal1, signal2)

        callback = Mock()
        signal1.connect(callback)  # pylint: disable=no-member

        callback2 = Mock()
        signal2.connect(callback2)  # pylint: disable=no-member

        signal1.emit()  # pylint: disable=no-member
        callback.assert_called_once_with()
        callback2.assert_not_called()
