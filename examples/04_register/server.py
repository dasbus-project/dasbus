#
# Run the service org.example.Register.
#
from dasbus.loop import EventLoop
from dasbus.server.interface import dbus_interface
from dasbus.server.property import emits_properties_changed
from dasbus.server.template import InterfaceTemplate
from dasbus.signal import Signal
from dasbus.typing import Structure, List
from dasbus.xml import XMLGenerator
from common import SESSION_BUS, REGISTER, User, InvalidUser


@dbus_interface(REGISTER.interface_name)
class RegisterInterface(InterfaceTemplate):
    """The DBus interface of the user register."""

    def connect_signals(self):
        """Connect the signals."""
        self.watch_property("Users", self.implementation.users_changed)

    @property
    def Users(self) -> List[Structure]:
        """The list of users."""
        return User.to_structure_list(self.implementation.users)

    @emits_properties_changed
    def RegisterUser(self, user: Structure):
        """Register a new user."""
        self.implementation.register_user(User.from_structure(user))


class Register(object):
    """The implementation of the user register."""

    def __init__(self):
        self._users = []
        self._users_changed = Signal()

    @property
    def users(self):
        """The list of users."""
        return self._users

    @property
    def users_changed(self):
        """Signal the user list change."""
        return self._users_changed

    def register_user(self, user: User):
        """Register a new user."""
        if any(u for u in self.users if u.name == user.name):
            raise InvalidUser("User {} exists.".format(user.name))

        self._users.append(user)
        self._users_changed.emit()


if __name__ == "__main__":
    # Print the generated XML specification.
    print(XMLGenerator.prettify_xml(RegisterInterface.__dbus_xml__))

    try:
        # Create the register.
        register = Register()

        # Publish the register at /org/example/Register.
        SESSION_BUS.publish_object(
            REGISTER.object_path,
            RegisterInterface(register)
        )

        # Register the service name org.example.Register.
        SESSION_BUS.register_service(
            REGISTER.service_name
        )

        # Start the event loop.
        loop = EventLoop()
        loop.run()
    finally:
        # Unregister the DBus service and objects.
        SESSION_BUS.disconnect()
