#
# Run the service org.example.HelloWorld.
#
from dasbus.loop import EventLoop
from dasbus.server.interface import dbus_interface
from dasbus.typing import Str
from common import HELLO_WORLD, SESSION_BUS
from dasbus.xml import XMLGenerator


@dbus_interface(HELLO_WORLD.interface_name)
class HelloWorld(object):
    """The DBus interface for HelloWorld."""

    def Hello(self, name: Str) -> Str:
        """Generate a greeting.

        :param name: someone to say hello
        :return: a greeting
        """
        return "Hello {}!".format(name)


if __name__ == "__main__":
    # Print the generated XML specification.
    print(XMLGenerator.prettify_xml(HelloWorld.__dbus_xml__))

    try:
        # Create an instance of the class HelloWorld.
        hello_world = HelloWorld()

        # Publish the instance at /org/example/HelloWorld.
        SESSION_BUS.publish_object(HELLO_WORLD.object_path, hello_world)

        # Register the service name org.example.HelloWorld.
        SESSION_BUS.register_service(HELLO_WORLD.service_name)

        # Start the event loop.
        loop = EventLoop()
        loop.run()
    finally:
        # Unregister the DBus service and objects.
        SESSION_BUS.disconnect()
