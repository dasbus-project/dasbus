#
# Handle changed properties.
# Start the server, start the listener and run the client.
#
from dasbus.loop import EventLoop
from common import REGISTER


def callback(interface, changed_properties, invalid_properties):
    """The callback of the DBus signal PropertiesChanged."""
    print("Properties of {} has changed: {}".format(
        interface, changed_properties
    ))


if __name__ == "__main__":
    # Create a proxy of the object /org/example/Register
    # provided by the service org.example.Register
    proxy = REGISTER.get_proxy()

    # Connect the callback to the DBus signal PropertiesChanged.
    proxy.PropertiesChanged.connect(callback)

    # Start the event loop.
    loop = EventLoop()
    loop.run()
