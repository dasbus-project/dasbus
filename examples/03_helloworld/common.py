#
# The common definitions
#
from dasbus.connection import SessionMessageBus
from dasbus.identifier import DBusServiceIdentifier

# Define the message bus.
SESSION_BUS = SessionMessageBus()

# Define services and objects.
HELLO_WORLD = DBusServiceIdentifier(
    namespace=("org", "example", "HelloWorld"),
    message_bus=SESSION_BUS
)
