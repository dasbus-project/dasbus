#
# Client support for DBus objects
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
from abc import ABCMeta, abstractmethod
from functools import partial

from dasbus.client.property import PropertyProxy
from dasbus.error import ErrorMapper
from dasbus.signal import Signal
from dasbus.constants import DBUS_FLAG_NONE
from dasbus.specification import DBusSpecification
from dasbus.typing import get_variant, get_variant_type, unwrap_variant

import gi
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib

__all__ = [
    "GLibClient",
    "AbstractClientObjectHandler",
    "ClientObjectHandler"
]


class GLibClient(object):
    """The low-level DBus client library based on GLib."""

    # Infinite timeout of a DBus call
    DBUS_TIMEOUT_NONE = GLib.MAXINT

    @classmethod
    def sync_call(cls, connection, service_name, object_path, interface_name,
                  method_name, parameters, reply_type, flags=DBUS_FLAG_NONE,
                  timeout=DBUS_TIMEOUT_NONE):
        """Synchronously call a DBus method.

        :return: a result of the DBus call
        """
        return connection.call_sync(
            service_name,
            object_path,
            interface_name,
            method_name,
            parameters,
            reply_type,
            flags,
            timeout,
            None
        )

    @classmethod
    def async_call(cls, connection, service_name, object_path, interface_name,
                   method_name, parameters, reply_type, callback,
                   callback_args=(), flags=DBUS_FLAG_NONE,
                   timeout=DBUS_TIMEOUT_NONE):
        """Asynchronously call a DBus method."""
        connection.call(
            service_name,
            object_path,
            interface_name,
            method_name,
            parameters,
            reply_type,
            flags,
            timeout,
            callback=cls._async_call_finish,
            user_data=(callback, callback_args)
        )

    @classmethod
    def _async_call_finish(cls, source_object, result_object, user_data):
        """Finish an asynchronous DBus method call."""
        # Prepare the user's callback.
        callback, callback_args = user_data

        # Call user's callback.
        callback(
            lambda: source_object.call_finish(result_object),
            *callback_args
        )

    @classmethod
    def subscribe_signal(cls, connection, service_name, object_path,
                         interface_name, signal_name, callback,
                         callback_args=(), flags=DBUS_FLAG_NONE):
        """Subscribe to a signal.

        :return: a callback to unsubscribe
        """
        subscription_id = connection.signal_subscribe(
            service_name,
            interface_name,
            signal_name,
            object_path,
            None,
            flags,
            callback=cls._signal_callback,
            user_data=(callback, callback_args)
        )

        return partial(
            cls._unsubscribe_signal,
            connection,
            subscription_id
        )

    @classmethod
    def _signal_callback(cls, connection, sender_name, object_path,
                         interface_name, signal_name, parameters, user_data):
        """A callback that is called when a DBus signal is emitted."""
        # Prepare the user's callback.
        callback, callback_args = user_data

        # Call user's callback.
        callback(parameters, *callback_args)

    @classmethod
    def _unsubscribe_signal(cls, connection, subscription_id):
        """Unsubscribe from a signal."""
        connection.signal_unsubscribe(subscription_id)

    @classmethod
    def is_remote_error(cls, error):
        """Is it a remote DBus error?"""
        return isinstance(error, GLib.Error) \
            and Gio.DBusError.is_remote_error(error)

    @classmethod
    def get_remote_error_name(cls, error):
        """Get a DBus name of the remote DBus error."""
        return Gio.DBusError.get_remote_error(error)

    @classmethod
    def get_remote_error_message(cls, error):
        """Get a message of the remote DBus error."""
        name = cls.get_remote_error_name(error)
        message = error.message
        prefix = "{}:{}: ".format("GDBus.Error", name)

        if message.startswith(prefix):
            return message[len(prefix):]

        return message


class AbstractClientObjectHandler(metaclass=ABCMeta):
    """The abstract handler of a remote DBus object."""

    __slots__ = [
        "_message_bus",
        "_service_name",
        "_object_path",
        "_specification"
    ]

    def __init__(self, message_bus, service_name, object_path):
        """Create a new handler.

        :param message_bus: a message bus
        :param service_name: a DBus name of the service
        :param object_path: a DBus path the object
        """
        self._message_bus = message_bus
        self._service_name = service_name
        self._object_path = object_path
        self._specification = None

    @property
    def service_name(self):
        """DBus service name.

        :return: a DBus name
        """
        return self._service_name

    @property
    def object_path(self):
        """DBus object path.

        :return: a DBus path
        """
        return self._object_path

    @property
    def specification(self):
        """DBus specification."""
        if not self._specification:
            self._specification = self._get_specification()

        return self._specification

    @abstractmethod
    def _get_specification(self):
        """Introspect the DBus object.

        :return: a DBus specification
        """
        return DBusSpecification()

    def create_member(self, interface_name, member_name):
        """Create a member of the DBus object.

        :param interface_name: a name of the interface
        :param member_name: a name of the member
        :return: a signal, a method or a property
        """
        spec = self._find_member_spec(interface_name, member_name)
        handler = self._find_handler(type(spec))
        return handler(spec)

    def _find_member_spec(self, interface_name, member_name):
        """Find a specification of the DBus member.

        :param interface_name: a name of the interface
        :param member_name: a name of the member
        :return: a specification of the member
        """
        return self.specification.get_member(
            interface_name, member_name
        )

    def _find_handler(self, member_type):
        """Find a handler for the given member type.

        :param member_type: a type of the member
        :return: a callback
        """
        if member_type is DBusSpecification.Property:
            return self._get_property

        if member_type is DBusSpecification.Method:
            return self._get_method

        if member_type is DBusSpecification.Signal:
            return self._get_signal

        raise TypeError(
            "Unsupported type: {}".format(member_type.__name__)
        )

    @abstractmethod
    def _get_property(self, property_spec):
        """Get a proxy of the DBus property.

        :param property_spec: a property_specification
        :return: a property object
        """
        pass

    @abstractmethod
    def _get_method(self, method_spec):
        """Get a proxy of the DBus method.

        :param method_spec: a method specification
        :return: a callable object
        """
        pass

    @abstractmethod
    def _get_signal(self, signal_spec):
        """Get a proxy of the DBus signal.

        :param signal_spec: a signal specification
        :return: a signal object
        """
        pass

    @abstractmethod
    def disconnect_members(self):
        """Disconnect members of the DBus object.

        Unsubscribe from DBus signals and disconnect all
        registered callbacks of the proxy signals.
        """
        pass


class ClientObjectHandler(AbstractClientObjectHandler):
    """The client handler of a DBus object."""

    __slots__ = [
        "_client",
        "_signal_factory",
        "_error_mapper",
        "_subscriptions"
    ]

    def __init__(self, message_bus, service_name, object_path,
                 error_mapper=None, client=GLibClient,
                 signal_factory=Signal):
        """Create a new handler.

        :param message_bus: a message bus
        :param service_name: a DBus name of the service
        :param object_path: a DBus path the object
        :param error_mapper: a DBus error mapper
        :param client: a DBus client library
        :param signal_factory: a signal factory
        """
        super().__init__(message_bus, service_name, object_path)
        self._client = client
        self._signal_factory = signal_factory
        self._error_mapper = error_mapper or ErrorMapper()
        self._subscriptions = []

    def _get_specification(self):
        """Introspect the DBus object."""
        xml = self._call_method(
            "org.freedesktop.DBus.Introspectable",
            "Introspect",
            None,
            "(s)"
        )

        return DBusSpecification.from_xml(xml)

    def _get_signal(self, signal_spec):
        """Get a proxy of the DBus signal."""
        # Create a signal.
        signal = self._signal_factory()

        # Subscribe to a DBus signal.
        unsubscribe = self._client.subscribe_signal(
            self._message_bus.connection,
            self._service_name,
            self._object_path,
            signal_spec.interface_name,
            signal_spec.name,
            callback=self._signal_callback,
            callback_args=(signal.emit,)
        )

        # Keep the subscriptions.
        self._subscriptions.append(unsubscribe)
        self._subscriptions.append(signal.disconnect)

        return signal

    def _signal_callback(self, parameters, callback):
        """A callback that is called when a DBus signal is emitted."""
        callback(*unwrap_variant(parameters))

    def _get_property(self, property_spec):
        """Get a proxy of the DBus property."""
        getter = None
        setter = None

        if property_spec.readable:
            getter = partial(self._get_property_value, property_spec)

        if property_spec.writable:
            setter = partial(self._set_property_value, property_spec)

        return PropertyProxy(getter, setter)

    def _get_property_value(self, property_spec):
        """Get a value of the DBus property."""
        variant = self._call_method(
            "org.freedesktop.DBus.Properties",
            "Get",
            "(ss)",
            "(v)",
            property_spec.interface_name,
            property_spec.name
        )
        return unwrap_variant(variant)

    def _set_property_value(self, property_spec, property_value):
        """Set a value of the DBus property."""
        return self._call_method(
            "org.freedesktop.DBus.Properties",
            "Set",
            "(ssv)",
            None,
            property_spec.interface_name,
            property_spec.name,
            get_variant(property_spec.type, property_value)
        )

    def _get_method(self, method_spec):
        """Get a callable proxy of the DBus method."""
        return partial(
            self._call_method,
            method_spec.interface_name,
            method_spec.name,
            method_spec.in_type,
            method_spec.out_type
        )

    def _call_method(self, interface_name, method_name, in_type,
                     out_type, *parameters, **kwargs):
        """Call a DBus method.

        :return: a result of the call or None
        """
        # Create variants.
        if not parameters:
            parameters = None

        if in_type is not None:
            parameters = get_variant(in_type, parameters)

        # Create variant types.
        reply_type = None

        if out_type is not None:
            reply_type = get_variant_type(out_type)

        # Collect arguments.
        args = (
            self._message_bus.connection,
            self._service_name,
            self._object_path,
            interface_name,
            method_name,
            parameters,
            reply_type,
        )

        # Get the callback.
        callback = kwargs.pop("callback", None)
        callback_args = kwargs.pop("callback_args", tuple())

        # Choose the type of invocation.
        if not callback:
            return self._get_method_reply(
                self._client.sync_call,
                *args,
                **kwargs,
            )
        else:
            return self._client.async_call(
                *args,
                **kwargs,
                callback=self._method_callback,
                callback_args=(callback, callback_args)
            )

    def _method_callback(self, getter, callback, callback_args):
        """A callback of an asynchronous DBus method call."""
        callback(
            lambda: self._get_method_reply(getter),
            *callback_args
        )

    def _get_method_reply(self, call, *args, **kwargs):
        """Get a result of a DBus call.

        :param call: a callback
        :param args: arguments of the callback
        :param kwargs: keyword arguments of the callback
        :return: a result of the callback
        :raise: an exception raised by the callback
        """
        try:
            result = call(*args, **kwargs)
            return self._handle_method_result(result)
        except Exception as error:  # pylint: disable=broad-except
            return self._handle_method_error(error)

    def _handle_method_error(self, error):
        """Handle an error of a DBus call.

        :param error: an exception raised during the call
        """
        # Re-raise if it is not a remote DBus error.
        if not self._client.is_remote_error(error):
            raise error

        name = self._client.get_remote_error_name(error)
        cls = self._error_mapper.get_exception_type(name)
        message = self._client.get_remote_error_message(error)

        # Create a new exception.
        exception = cls(message)
        exception.dbus_name = name

        # Raise a new instance of the exception class.
        raise exception from None

    def _handle_method_result(self, result):
        """Handle a result of a DBus call.

        :param result: a variant tuple
        """
        # Unwrap a variant tuple.
        values = unwrap_variant(result)

        # Return None if there are no values.
        if not values:
            return None

        # Return one value.
        if len(values) == 1:
            return values[0]

        # Return multiple values.
        return values

    def disconnect_members(self):
        """Disconnect members of the DBus object."""
        while self._subscriptions:
            callback = self._subscriptions.pop()
            callback()
