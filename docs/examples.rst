Examples
========

Look at the `complete examples <https://github.com/rhinstaller/dasbus/tree/master/examples>`_ or
`DBus services <https://github.com/rhinstaller/anaconda/tree/master/pyanaconda/modules>`_ of
the Anaconda Installer for more inspiration.

Basic usage
-----------

Show the current hostname.

.. code-block:: python

    from dasbus.connection import SystemMessageBus
    bus = SystemMessageBus()

    proxy = bus.get_proxy(
        "org.freedesktop.hostname1",
        "/org/freedesktop/hostname1"
    )

    print(proxy.Hostname)

Send a notification to the notification server.

.. code-block:: python

    from dasbus.connection import SessionMessageBus
    bus = SessionMessageBus()

    proxy = bus.get_proxy(
        "org.freedesktop.Notifications",
        "/org/freedesktop/Notifications"
    )

    id = proxy.Notify(
        "", 0, "face-smile", "Hello World!",
        "This notification can be ignored.",
        [], {}, 0
    )

    print("The notification {} was sent.".format(id))

Handle a closed notification.

.. code-block:: python

    from dasbus.loop import EventLoop
    loop = EventLoop()

    from dasbus.connection import SessionMessageBus
    bus = SessionMessageBus()

    proxy = bus.get_proxy(
        "org.freedesktop.Notifications",
        "/org/freedesktop/Notifications"
    )

    def callback(id, reason):
        print("The notification {} was closed.".format(id))

    proxy.NotificationClosed.connect(callback)
    loop.run()

Asynchronously fetch a list of network devices.

.. code-block:: python

    from dasbus.loop import EventLoop
    loop = EventLoop()

    from dasbus.connection import SystemMessageBus
    bus = SystemMessageBus()

    proxy = bus.get_proxy(
        "org.freedesktop.NetworkManager",
        "/org/freedesktop/NetworkManager"
    )

    def callback(call):
        print(call())

    proxy.GetDevices(callback=callback)
    loop.run()


Run a DBus service
------------------

Define the org.example.HelloWorld service.

.. code-block:: python

    class HelloWorld(object):
        __dbus_xml__ = """
        <node>
            <interface name="org.example.HelloWorld">
                <method name="Hello">
                    <arg direction="in" name="name" type="s" />
                    <arg direction="out" name="return" type="s" />
                </method>
            </interface>
        </node>
        """

        def Hello(self, name):
            return "Hello {}!".format(name)

Define the org.example.HelloWorld service with an automatically generated XML specification.

.. code-block:: python

    from dasbus.server.interface import dbus_interface
    from dasbus.typing import Str

    @dbus_interface("org.example.HelloWorld")
    class HelloWorld(object):

        def Hello(self, name: Str) -> Str:
            return "Hello {}!".format(name)

    print(HelloWorld.__dbus_xml__)

Publish the org.example.HelloWorld service on the session message bus. The service will
be unregistered automatically via the bus context manager.

.. code-block:: python

    from dasbus.connection import SessionMessageBus
    with SessionMessageBus() as bus:

        bus.publish_object("/org/example/HelloWorld", HelloWorld())
        bus.register_service("org.example.HelloWorld")

Start the event loop to process incoming D-Bus calls.

.. code-block:: python

    from dasbus.loop import EventLoop
    loop = EventLoop()
    loop.run()


Use Unix file descriptors
-------------------------

The support for Unix file descriptors is disabled by default. It needs to be explicitly enabled
when you create a DBus proxy or publish a DBus object that could send or receive Unix file
descriptors.

.. warning::

    This functionality is supported only on UNIX.

Send and receive Unix file descriptors with a DBus proxy.

.. code-block:: python

    import os
    from dasbus.connection import SystemMessageBus
    from dasbus.unix import GLibClientUnix
    bus = SystemMessageBus()

    proxy = bus.get_proxy(
        "org.freedesktop.login1",
        "/org/freedesktop/login1",
        client=GLibClientUnix
    )

    fd = proxy.Inhibit(
        "sleep", "my-example", "Running an example", "block"
    )

    proxy.ListInhibitors()
    os.close(fd)

Allow to send and receive Unix file descriptors within the /org/example/HelloWorld DBus object.

.. code-block:: python

    from dasbus.unix import GLibServerUnix
    bus.publish_object(
        "/org/example/HelloWorld",
        HelloWorld(),
        server=GLibServerUnix
    )

Manage DBus names
-----------------

Use constants to define DBus services and objects.

.. code-block:: python

    from dasbus.connection import SystemMessageBus
    from dasbus.identifier import DBusServiceIdentifier, DBusObjectIdentifier

    NETWORK_MANAGER_NAMESPACE = (
        "org", "freedesktop", "NetworkManager"
    )

    NETWORK_MANAGER = DBusServiceIdentifier(
        namespace=NETWORK_MANAGER_NAMESPACE,
        message_bus=SystemMessageBus()
    )

    NETWORK_MANAGER_SETTINGS = DBusObjectIdentifier(
        namespace=NETWORK_MANAGER_NAMESPACE,
        basename="Settings"
    )

Create a proxy of the org.freedesktop.NetworkManager service.

.. code-block:: python

    proxy = NETWORK_MANAGER.get_proxy()
    print(proxy.NetworkingEnabled)

Create a proxy of the /org/freedesktop/NetworkManager/Settings object.

.. code-block:: python

    proxy = NETWORK_MANAGER.get_proxy(NETWORK_MANAGER_SETTINGS)
    print(proxy.Hostname)

See `a complete example <https://github.com/rhinstaller/dasbus/tree/master/examples/05_chat>`__.

Handle DBus errors
------------------

Use exceptions to propagate and handle DBus errors. Create an error mapper and a decorator for
mapping Python exception classes to DBus error names.

.. code-block:: python

    from dasbus.error import ErrorMapper, DBusError, get_error_decorator
    error_mapper = ErrorMapper()
    dbus_error = get_error_decorator(error_mapper)

Use the decorator to register Python exceptions that represent DBus errors. These exceptions
can be raised by DBus services and caught by DBus clients in the try-except block.

.. code-block:: python

    @dbus_error("org.freedesktop.DBus.Error.InvalidArgs")
    class InvalidArgs(DBusError):
        pass

The message bus will use the specified error mapper to automatically transform Python exceptions
to DBus errors and back.

.. code-block:: python

    from dasbus.connection import SessionMessageBus
    bus = SessionMessageBus(error_mapper=error_mapper)

See `a complete example <https://github.com/rhinstaller/dasbus/tree/master/examples/04_register>`__.

Call methods with timeout
-------------------------

Call DBus methods with a timeout (specified in milliseconds).

.. code-block:: python

    proxy = NETWORK_MANAGER.get_proxy()

    try:
        proxy.CheckConnectivity(timeout=3)
    except TimeoutError:
        print("The call timed out!")


Handle DBus structures
----------------------

Represent DBus structures by Python objects. A DBus structure is a dictionary of attributes that
maps attribute names to variants with attribute values. Use Python objects to define such
structures. They can be easily converted to a dictionary, send via DBus and converted back to
an object.

.. code-block:: python

    from dasbus.structure import DBusData
    from dasbus.typing import Str, get_variant

    class UserData(DBusData):
        def __init__(self):
            self._name = ""

        @property
        def name(self) -> Str:
            return self._name

        @name.setter
        def name(self, name):
            self._name = name

    data = UserData()
    data.name = "Alice"

    print(UserData.to_structure(data))
    print(UserData.from_structure({
        "name": get_variant(Str, "Bob")
    }))

See `a complete example <https://github.com/rhinstaller/dasbus/tree/master/examples/04_register>`__.

Manage groups of DBus objects
-----------------------------

Create Python objects that can be automatically published on DBus. These objects are usually
managed by DBus containers and published on demand.

.. code-block:: python

    from dasbus.server.interface import dbus_interface
    from dasbus.server.template import InterfaceTemplate
    from dasbus.server.publishable import Publishable
    from dasbus.typing import Str

    @dbus_interface("org.example.Chat")
    class ChatInterface(InterfaceTemplate):

        def Send(self, message: Str):
            return self.implementation.send()

    class Chat(Publishable):

        def for_publication(self):
            return ChatInterface(self)

        def send(self, message):
            print(message)

Use DBus containers to automatically publish dynamically created Python objects. A DBus container
converts publishable Python objects into DBus paths and back. It generates unique DBus paths in
the specified namespace and assigns them to objects. Each object is published when its DBus path
is requested for the first time.

.. code-block:: python

    from dasbus.connection import SessionMessageBus
    from dasbus.server.container import DBusContainer

    container = DBusContainer(
        namespace=("org", "example", "Chat"),
        message_bus=SessionMessageBus()
    )

    print(container.to_object_path(Chat()))

See `a complete example <https://github.com/rhinstaller/dasbus/tree/master/examples/05_chat>`__.
