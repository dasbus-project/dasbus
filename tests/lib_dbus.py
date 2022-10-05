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
import multiprocessing
import sys
import unittest

from abc import abstractmethod, ABCMeta
from contextlib import contextmanager
from threading import Thread

import gi
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import GLib, Gio


def run_loop(timeout=3):
    """Run an event loop for the specified timeout.

    If any of the events fail or there are some pending
    events after the timeout, raise AssertionError.

    :param int timeout: a number of seconds
    """
    loop = GLib.MainLoop()

    def _kill_loop():
        loop.quit()
        return False

    GLib.timeout_add_seconds(timeout, _kill_loop)

    with catch_errors() as errors:
        loop.run()

    assert not errors, "The loop has failed!"
    assert not loop.get_context().pending()


@contextmanager
def catch_errors():
    """Catch exceptions raised in this context.

    :return: a list of exceptions
    """
    errors = []

    def _handle_error(*exc_info):
        errors.append(exc_info)
        sys.__excepthook__(*exc_info)

    try:
        sys.excepthook = _handle_error
        yield errors
    finally:
        sys.excepthook = sys.__excepthook__


class AbstractDBusTestCase(unittest.TestCase, metaclass=ABCMeta):
    """Test DBus support with a real DBus connection."""

    def setUp(self):
        """Set up the test."""
        self.maxDiff = None

        # Initialize the service and the clients.
        self.service = self._get_service()
        self.clients = []

        # Start a testing bus.
        self.bus = Gio.TestDBus()
        self.bus.up()

        # Create a connection to the testing bus.
        self.bus_address = self.bus.get_bus_address()
        self.message_bus = self._get_message_bus(
            self.bus_address
        )

    @abstractmethod
    def _get_service(self):
        """Get a service."""
        return None

    @classmethod
    @abstractmethod
    def _get_message_bus(cls, bus_address):
        """Get a testing message bus."""
        return None

    @classmethod
    def _get_service_proxy(cls, message_bus, **proxy_args):
        """Get a proxy of the example service."""
        return message_bus.get_proxy(
            "my.testing.Example",
            "/my/testing/Example",
            **proxy_args
        )

    def _add_client(self, callback, *args, **kwargs):
        """Add a client."""
        self.clients.append(callback)

    def _publish_service(self):
        """Publish the service on DBus."""
        self.message_bus.publish_object(
            "/my/testing/Example",
            self.service
        )
        self.message_bus.register_service(
            "my.testing.Example"
        )

    def _run_test(self):
        """Run a test."""
        self._publish_service()

        for client in self.clients:
            client.start()

        run_loop()

        for client in self.clients:
            client.join()

    def tearDown(self):
        """Tear down the test."""
        if self.message_bus:
            self.message_bus.disconnect()

        if self.bus:
            self.bus.down()


class DBusThreadedTestCase(AbstractDBusTestCase, metaclass=ABCMeta):
    """Test DBus support with a real DBus connection and threads."""

    def _add_client(self, callback, *args, **kwargs):
        """Add a client thread."""
        thread = Thread(
            target=callback,
            args=args,
            kwargs=kwargs,
            daemon=True,
        )
        super()._add_client(thread)


class DBusSpawnedTestCase(AbstractDBusTestCase, metaclass=ABCMeta):
    """Test DBus support with a real DBus connections and spawned processes."""

    def setUp(self):
        """Set up the test."""
        super().setUp()
        self.context = multiprocessing.get_context('spawn')

    def _add_client(self, callback, *args, **kwargs):
        """Add a client process."""
        process = self.context.Process(
            name=callback.__name__,
            target=callback,
            args=(self.bus_address, *args),
            kwargs=kwargs,
            daemon=True,
        )
        super()._add_client(process)

    def _run_test(self):
        """Run a test."""
        super()._run_test()

        # Check the exit codes of the clients.
        for client in self.clients:
            msg = "{} has finished with {}".format(
                client.name,
                client.exitcode
            )
            self.assertEqual(client.exitcode, 0, msg)
