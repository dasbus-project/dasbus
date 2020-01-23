#
# The common definitions
#
from dasbus.connection import SessionMessageBus
from dasbus.error import dbus_error, DBusError
from dasbus.identifier import DBusServiceIdentifier
from dasbus.structure import DBusData
from dasbus.typing import Str, Int

# Define the message bus.
SESSION_BUS = SessionMessageBus()

# Define namespaces.
REGISTER_NAMESPACE = ("org", "example", "Register")

# Define services and objects.
REGISTER = DBusServiceIdentifier(
    namespace=REGISTER_NAMESPACE,
    message_bus=SESSION_BUS
)


# Define errors.
@dbus_error("InvalidUserError", namespace=REGISTER_NAMESPACE)
class InvalidUser(DBusError):
    """The user is invalid."""
    pass


# Define structures.
class User(DBusData):
    """The user data."""

    def __init__(self):
        self._name = ""
        self._age = 0

    @property
    def name(self) -> Str:
        """Name of the user."""
        return self._name

    @name.setter
    def name(self, value: Str):
        self._name = value

    @property
    def age(self) -> Int:
        """Age of the user."""
        return self._age

    @age.setter
    def age(self, value: Int):
        self._age = value
