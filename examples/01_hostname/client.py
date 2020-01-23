#
# Show the current hostname.
#
from dasbus.connection import SystemMessageBus
from dasbus.identifier import DBusServiceIdentifier

# Define the message bus.
SYSTEM_BUS = SystemMessageBus()

# Define services and objects.
HOSTNAME = DBusServiceIdentifier(
    namespace=("org", "freedesktop", "hostname"),
    service_version=1,
    object_version=1,
    interface_version=1,
    message_bus=SYSTEM_BUS
)

if __name__ == "__main__":
    # Create a proxy of the object /org/freedesktop/hostname1
    # provided by the service org.freedesktop.hostname1.
    proxy = HOSTNAME.get_proxy()

    # Print a value of the DBus property Hostname.
    print(proxy.Hostname)
