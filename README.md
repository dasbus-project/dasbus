# dasbus
This DBus library is written in Python 3, based on GLib and inspired by pydbus. Find out more in
the [documentation](https://dasbus.readthedocs.io/en/latest/).

The code used to be part of the [Anaconda Installer](https://github.com/rhinstaller/anaconda)
project. It was based on the [pydbus](https://github.com/LEW21/pydbus) library, but we replaced
it with our own solution because its upstream development stalled. The dasbus library is
a result of this effort.

[![Build Status](https://travis-ci.com/rhinstaller/dasbus.svg?branch=master)](https://travis-ci.com/rhinstaller/dasbus)
[![Documentation Status](https://readthedocs.org/projects/dasbus/badge/?version=latest)](https://dasbus.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/rhinstaller/dasbus/branch/master/graph/badge.svg)](https://codecov.io/gh/rhinstaller/dasbus)

## Requirements

* Python 3.6+
* PyGObject 3

You can install [PyGObject](https://pygobject.readthedocs.io) provided by your system or use PyPI.
The system package is usually called `python3-gi`, `python3-gobject` or `pygobject3`. See the
[instructions](https://pygobject.readthedocs.io/en/latest/getting_started.html) for your platform
(only for PyGObject, you don't need cairo or GTK).

The library is known to work with Python 3.8, PyGObject 3.34 and GLib 2.63, but these are not the
required minimal versions.

## Installation

Install the package from [PyPI](https://pypi.org/project/dasbus/). Follow the instructions above
to install the required dependencies.

```
pip3 install dasbus
```

Or install the RPM package on Fedora 31+.

```
sudo dnf install python3-dasbus
```

## Examples

Show the current hostname.

```python
from dasbus.connection import SystemMessageBus
bus = SystemMessageBus()

proxy = bus.get_proxy(
    "org.freedesktop.hostname1",
    "/org/freedesktop/hostname1"
)

print(proxy.Hostname)
```

Send a notification to the notification server.

```python
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
```

Handle a closed notification.

```python
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
```

Run the service org.example.HelloWorld.

```python
from dasbus.loop import EventLoop
loop = EventLoop()

from dasbus.connection import SessionMessageBus
bus = SessionMessageBus()

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

bus.publish_object("/org/example/HelloWorld", HelloWorld())
bus.register_service("org.example.HelloWorld")
loop.run()
```


## Features

Use constants to define DBus services and objects.

```python
from dasbus.connection import SystemMessageBus
from dasbus.identifier import DBusServiceIdentifier

NETWORK_MANAGER = DBusServiceIdentifier(
    namespace=("org", "freedesktop", "NetworkManager"),
    message_bus=SystemMessageBus()
)

proxy = NETWORK_MANAGER.get_proxy()
print(proxy.NetworkingEnabled)
```

Use exceptions to propagate and handle DBus errors. Create an error mapper and a decorator for
mapping Python exception classes to DBus error names. The message bus will use the given error
mapper to transform Python exceptions to DBus errors and back.

```python
from dasbus.error import ErrorMapper, DBusError, get_error_decorator
error_mapper = ErrorMapper()
dbus_error = get_error_decorator(error_mapper)

from dasbus.connection import SessionMessageBus
bus = SessionMessageBus(error_mapper=error_mapper)

@dbus_error("org.freedesktop.DBus.Error.InvalidArgs")
class InvalidArgs(DBusError):
    pass
```

Call DBus methods asynchronously.

```python
from dasbus.loop import EventLoop
loop = EventLoop()

def callback(call):
    print(call())

proxy = NETWORK_MANAGER.get_proxy()
proxy.GetDevices(callback=callback)
loop.run()
```

Generate XML specifications from Python classes.

```python
from dasbus.server.interface import dbus_interface
from dasbus.typing import Str

@dbus_interface("org.example.HelloWorld")
class HelloWorld(object):

    def Hello(self, name: Str) -> Str:
        return "Hello {}!".format(name)

print(HelloWorld.__dbus_xml__)
```

Represent DBus structures by Python objects.

```python
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
```

Create Python objects that can be published on DBus.

```python
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

```

Use DBus containers to publish dynamically created Python objects.

```python
from dasbus.connection import SessionMessageBus
from dasbus.server.container import DBusContainer

container = DBusContainer(
    namespace=("org", "example", "Chat"),
    message_bus=SessionMessageBus()
)

print(container.to_object_path(Chat()))
```

## Inspiration

Look at the [complete examples](https://github.com/rhinstaller/dasbus/tree/master/examples) or
[DBus services](https://github.com/rhinstaller/anaconda/tree/master/pyanaconda/modules) of
the Anaconda Installer for more inspiration.
