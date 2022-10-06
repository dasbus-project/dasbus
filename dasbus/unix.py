#
# Support for Unix file descriptors.
#
# Copyright (C) 2022  Red Hat, Inc.  All rights reserved.
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
import logging

from dasbus.constants import DBUS_FLAG_NONE
from dasbus.typing import VariantUnpacking, get_variant
from dasbus.client.handler import GLibClient
from dasbus.server.handler import GLibServer

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio

log = logging.getLogger(__name__)

__all__ = [
    "GLibClientUnix",
    "GLibServerUnix",
]


def acquire_fds(variant):
    """Acquire Unix file descriptors contained in a variant.

    Return a variant with indexes into a list of Unix file descriptors
    and the list of Unix file descriptors.

    If the variant is None, or the variant doesn't contain any Unix
    file descriptors, return None instead of the list.

    :param variant: a variant with Unix file descriptors
    :return: a variant with indexes and a list of Unix file descriptors
    """
    if variant is None:
        return None, None

    fd_list = []

    def _get_idx(fd):
        fd_list.append(fd)
        return len(fd_list) - 1

    variant_without_fds = UnixFDSwap.apply(variant, _get_idx)

    if not fd_list:
        return variant, None

    return variant_without_fds, Gio.UnixFDList.new_from_array(fd_list)


def restore_fds(variant, fd_list: Gio.UnixFDList):
    """Restore Unix file descriptors in a variant.

    If the variant is None, return None. Otherwise, return
    a variant with Unix file descriptors.

    :param variant: a variant with indexes into fd_list
    :param fd_list: a list of Unix file descriptors
    :return: a variant with Unix file descriptors
    """
    if variant is None:
        return None

    if fd_list is None:
        return variant

    fd_list = fd_list.steal_fds()

    if not fd_list:
        return variant

    def _get_fd(index):
        try:
            return fd_list[index]
        except IndexError:
            return -1

    return UnixFDSwap.apply(variant, _get_fd)


class UnixFDSwap(VariantUnpacking):
    """Class for swapping values of the UnixFD type."""

    @classmethod
    def apply(cls, variant, swap):
        """Swap unix file descriptors with indices.

        The provided function should swap a unix file
        descriptor with an index into an array of unix
        file descriptors or vice versa.

        :param variant: a variant to modify
        :param swap: a swapping function
        :return: a modified variant
        """
        return cls._recreate_variant(variant, swap)

    @classmethod
    def _handle_variant(cls, variant, *extras):
        """Handle a variant."""
        return cls._recreate_variant(variant.get_variant(), *extras)

    @classmethod
    def _handle_value(cls, variant, *extras):
        """Handle a basic value."""
        type_string = variant.get_type_string()

        # Handle the unix file descriptor.
        if type_string == 'h':
            # Get the swapping function.
            swap, *_ = extras
            # Swap the values.
            return swap(variant.get_handle())

        return variant.unpack()

    @classmethod
    def _recreate_variant(cls, variant, *extras):
        """Create a variant with swapped values."""
        type_string = variant.get_type_string()

        # Do nothing if there is no unix file descriptor to handle.
        if 'h' not in type_string and 'v' not in type_string:
            return variant

        # Get a new value of the variant.
        value = cls._process_variant(variant, *extras)

        # Create a new variant.
        return get_variant(type_string, value)


class GLibClientUnix(GLibClient):
    """The low-level DBus client library based on GLib."""

    @classmethod
    def sync_call(cls, connection, service_name, object_path, interface_name,
                  method_name, parameters, reply_type, flags=DBUS_FLAG_NONE,
                  timeout=GLibClient.DBUS_TIMEOUT_NONE):
        """Synchronously call a DBus method.

        :return: a result of the DBus call
        """
        # Process Unix file descriptors in parameters.
        parameters, fd_list = acquire_fds(parameters)

        # Call the DBus method.
        result = connection.call_with_unix_fd_list_sync(
            service_name,
            object_path,
            interface_name,
            method_name,
            parameters,
            reply_type,
            flags,
            timeout,
            fd_list,
            None
        )

        # Restore Unix file descriptors in the result.
        return restore_fds(*result)

    @classmethod
    def async_call(cls, connection, service_name, object_path, interface_name,
                   method_name, parameters, reply_type, callback,
                   callback_args=(), flags=DBUS_FLAG_NONE,
                   timeout=GLibClient.DBUS_TIMEOUT_NONE):
        """Asynchronously call a DBus method."""
        # Process Unix file descriptors in parameters.
        parameters, fd_list = acquire_fds(parameters)

        # Call the DBus method.
        connection.call_with_unix_fd_list(
            service_name,
            object_path,
            interface_name,
            method_name,
            parameters,
            reply_type,
            flags,
            timeout,
            fd_list,
            callback=cls._async_call_finish,
            user_data=(callback, callback_args)
        )

    @classmethod
    def _async_call_finish(cls, source_object, result_object, user_data):
        """Finish an asynchronous DBus method call."""
        # Prepare the user's callback.
        callback, callback_args = user_data

        def _finish_call():
            # Retrieve the result of the call.
            result = source_object.call_with_unix_fd_list_finish(
                result_object
            )
            # Restore Unix file descriptors in the result.
            return restore_fds(*result)

        # Call user's callback.
        callback(_finish_call, *callback_args)


class GLibServerUnix(GLibServer):
    """The low-level DBus server library based on GLib.

    Adds Unix FD Support to base class"""

    @classmethod
    def emit_signal(cls, connection, object_path, interface_name,
                    signal_name, parameters, destination=None):
        """Emit a DBus signal.

        GLib doesn't seem to support Unix file descriptors in signals.
        Swap Unix file descriptors with indexes into a list of Unix file
        descriptors, but emit just the indexes. Log a warning to inform
        users about the limited support.
        """
        # Process Unix file descriptors in parameters.
        parameters, fd_list = acquire_fds(parameters)

        if fd_list:
            log.warning("Unix file descriptors in signals are unsupported.")

        # Emit the signal without Unix file descriptors.
        connection.emit_signal(
            destination,
            object_path,
            interface_name,
            signal_name,
            parameters
        )

    @classmethod
    def set_call_reply(cls, invocation, out_type, out_value):
        """Set the reply of the DBus call."""
        # Process Unix file descriptors in the reply.
        reply_value = cls._get_reply_value(out_type, out_value)
        reply_args = acquire_fds(reply_value)

        # Send the reply.
        invocation.return_value_with_unix_fd_list(*reply_args)

    @classmethod
    def _object_callback(cls, connection, sender, object_path,
                         interface_name, method_name, parameters,
                         invocation, user_data):
        """A method call closure of a DBus object."""
        # Prepare the user's callback.
        callback, callback_args = user_data

        # Restore Unix file descriptors in parameters.
        fd_list = invocation.get_message().get_unix_fd_list()
        parameters = restore_fds(parameters, fd_list)

        # Call user's callback.
        callback(
            invocation,
            interface_name,
            method_name,
            parameters,
            *callback_args
        )
