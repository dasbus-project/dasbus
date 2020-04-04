#
# The common definitions
#
from dasbus.connection import SessionMessageBus
from dasbus.error import DBusError, ErrorMapper, get_error_decorator
from dasbus.identifier import DBusServiceIdentifier
from dasbus.structure import DBusData
from dasbus.typing import Str, Int

# Define the error mapper.
ERROR_MAPPER = ErrorMapper()

# Define the message bus.
SESSION_BUS = SessionMessageBus(
    error_mapper=ERROR_MAPPER
)

# Define namespaces.
REGISTER_NAMESPACE = ("org", "example", "Register")

# Define services and objects.
REGISTER = DBusServiceIdentifier(
    namespace=REGISTER_NAMESPACE,
    message_bus=SESSION_BUS
)

# The decorator for DBus errors.
dbus_error = get_error_decorator(ERROR_MAPPER)


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
