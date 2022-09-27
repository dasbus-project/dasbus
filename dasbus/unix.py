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
from dasbus.constants import DBUS_FLAG_NONE
from dasbus.typing import VariantUnpacking, get_variant
from dasbus.client.handler import GLibClient
from dasbus.server.handler import GLibServer

import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio

__all__ = [
    "GLibClientUnix",
    "GLibServerUnix",
]


def variant_replace_handles_with_fdlist_indices(v, fdlist=None):
    """Given a variant, return a new variant
    with all 'h' handles replaced with FDlist indices,
    adding extracted handles to the fdlist passed as an argument.

    FIXME: This is a temporary method. Call UnixFDSwap instead.
    """
    indices = fdlist or []

    def get_index(fd_handler):
        indices.append(fd_handler)
        return len(indices) - 1

    return UnixFDSwap.apply(v, get_index), indices


def variant_replace_fdlist_indices_with_handles(v, fdlist):
    """Given a varaint and an fdlist, find any 'h' handle instances
    and replace them with file descriptors that they represent.

    FIXME: This is a temporary method. Call UnixFDSwap instead.
    """
    indices = fdlist

    def get_handler(fd_index):
        return indices[fd_index]

    return UnixFDSwap.apply(v, get_handler)


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
    def _handle_unix_fd_list_result(cls, result, fd_list):
        """Handle the output fd list."""
        if not fd_list:
            return result

        return variant_replace_fdlist_indices_with_handles(
            result, fd_list.steal_fds()
        )

    @classmethod
    def sync_call(cls, connection, service_name, object_path, interface_name,
                  method_name, parameters, reply_type, flags=DBUS_FLAG_NONE,
                  timeout=GLibClient.DBUS_TIMEOUT_NONE):
        """Synchronously call a DBus method.

        :return: a result of the DBus call
        """
        params = parameters
        fds = None
        if parameters:
            params, fdlist = variant_replace_handles_with_fdlist_indices(
                parameters)
            if fdlist:
                fds = Gio.UnixFDList.new_from_array(fdlist)

        ret = connection.call_with_unix_fd_list_sync(
            service_name,
            object_path,
            interface_name,
            method_name,
            params,
            reply_type,
            flags,
            timeout,
            fds,
            None
        )

        return cls._handle_unix_fd_list_result(*ret)

    @classmethod
    def async_call(cls, connection, service_name, object_path, interface_name,
                   method_name, parameters, reply_type, callback,
                   callback_args=(), flags=DBUS_FLAG_NONE,
                   timeout=GLibClient.DBUS_TIMEOUT_NONE):
        """Asynchronously call a DBus method."""
        params = parameters
        fds = None
        if parameters:
            params, fdlist = variant_replace_handles_with_fdlist_indices(
                parameters)

            if fdlist:
                fds = Gio.UnixFDList.new_from_array(fdlist)

        connection.call_with_unix_fd_list(
            service_name,
            object_path,
            interface_name,
            method_name,
            params,
            reply_type,
            flags,
            timeout,
            fds,
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
            lambda: cls._handle_unix_fd_list_result(
                *source_object.call_with_unix_fd_list_finish(result_object)
            ),
            *callback_args
        )


class GLibServerUnix(GLibServer):
    """The low-level DBus server library based on GLib.

    Adds Unix FD Support to base class"""

    @classmethod
    def set_call_reply(cls, invocation, out_type, out_value):
        """Set the reply of the DBus call.

        :param invocation: an invocation of a DBus call
        :param out_type: a type of the reply
        :param out_value: a value of the reply
        """
        reply_value = cls._get_reply_value(out_type, out_value)
        if reply_value is None:
            invocation.return_value(reply_value)
        else:
            reply, fdlist = variant_replace_handles_with_fdlist_indices(
                reply_value)
            if len(fdlist) != 0:
                invocation.return_value_with_unix_fd_list(
                    reply, Gio.UnixFDList.new_from_array(fdlist))
            else:
                invocation.return_value(reply_value)

    @classmethod
    def _object_callback(cls, connection, sender, object_path,
                         interface_name, method_name, parameters,
                         invocation, user_data):
        # Prepare the user's callback.
        callback, callback_args = user_data

        fdlist = invocation.get_message().get_unix_fd_list()
        if fdlist is not None:
            parameters = variant_replace_fdlist_indices_with_handles(
                parameters, fdlist.peek_fds())
        # Call user's callback.
        callback(
            invocation,
            interface_name,
            method_name,
            parameters,
            *callback_args
        )
