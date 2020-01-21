#
# Run the service org.example.Chat.
#
from dasbus.loop import EventLoop
from dasbus.server.interface import dbus_interface, dbus_signal
from dasbus.server.publishable import Publishable
from dasbus.server.template import InterfaceTemplate
from dasbus.signal import Signal
from dasbus.typing import Str, ObjPath
from dasbus.xml import XMLGenerator
from common import SESSION_BUS, CHAT, ROOM, ROOM_CONTAINER


@dbus_interface(ROOM.interface_name)
class RoomInterface(InterfaceTemplate):
    """The DBus interface of the chat room."""

    def connect_signals(self):
        """Connect the signals."""
        self.implementation.message_received.connect(self.MessageReceived)

    @dbus_signal
    def MessageReceived(self, msg: Str):
        """Signal that a message has been received."""
        pass

    def SendMessage(self, msg: Str):
        """Send a message to the chat room."""
        self.implementation.send_message(msg)


class Room(Publishable):
    """The implementation of the chat room."""

    def __init__(self, name):
        self._name = name
        self._message_received = Signal()

    def for_publication(self):
        """Return a DBus representation."""
        return RoomInterface(self)

    @property
    def message_received(self):
        """Signal that a message has been received."""
        return self._message_received

    def send_message(self, msg):
        """Send a message to the chat room."""
        print("{}: {}".format(self._name, msg))
        self.message_received.emit(msg)


@dbus_interface(CHAT.interface_name)
class ChatInterface(InterfaceTemplate):
    """The DBus interface of the chat service."""

    def FindRoom(self, name: Str) -> ObjPath:
        """Find or create a chat room."""
        return ROOM_CONTAINER.to_object_path(
            self.implementation.find_room(name)
        )


class Chat(Publishable):
    """The implementation of the chat."""

    def __init__(self):
        self._rooms = {}

    def for_publication(self):
        """Return a DBus representation."""
        return ChatInterface(self)

    def find_room(self, name):
        """Find or create a chat room."""
        if name not in self._rooms:
            self._rooms[name] = Room(name)

        return self._rooms[name]


if __name__ == "__main__":
    # Print the generated XML specifications.
    print(XMLGenerator.prettify_xml(ChatInterface.__dbus_xml__))
    print(XMLGenerator.prettify_xml(RoomInterface.__dbus_xml__))

    try:
        # Create the chat.
        chat = Chat()

        # Publish the chat at /org/example/Chat.
        SESSION_BUS.publish_object(CHAT.object_path, chat.for_publication())

        # Register the service name org.example.Chat.
        SESSION_BUS.register_service(CHAT.service_name)

        # Start the event loop.
        loop = EventLoop()
        loop.run()
    finally:
        # Unregister the DBus service and objects.
        SESSION_BUS.disconnect()
