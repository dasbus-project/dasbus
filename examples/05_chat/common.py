#
# The common definitions
#
from dasbus.connection import SessionMessageBus
from dasbus.identifier import DBusServiceIdentifier, DBusInterfaceIdentifier
from dasbus.server.container import DBusContainer

# Define the message bus.
SESSION_BUS = SessionMessageBus()

# Define namespaces.
CHAT_NAMESPACE = ("org", "example", "Chat")
ROOMS_NAMESPACE = (*CHAT_NAMESPACE, "Rooms")

# Define services and objects.
CHAT = DBusServiceIdentifier(
    namespace=CHAT_NAMESPACE,
    message_bus=SESSION_BUS
)

ROOM = DBusInterfaceIdentifier(
    namespace=CHAT_NAMESPACE,
    basename="Room"
)

# Define containers.
ROOM_CONTAINER = DBusContainer(
    namespace=ROOMS_NAMESPACE,
    message_bus=SESSION_BUS
)
