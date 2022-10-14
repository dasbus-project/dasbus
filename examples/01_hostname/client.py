#
# Show the current hostname.
#
from dasbus.connection import SystemMessageBus

if __name__ == "__main__":
    # Create a representation of a system bus connection.
    bus = SystemMessageBus()

    # Create a proxy of the object /org/freedesktop/hostname1
    # provided by the service org.freedesktop.hostname1.
    proxy = bus.get_proxy(
        "org.freedesktop.hostname1",
        "/org/freedesktop/hostname1"
    )

    # Print a value of the DBus property Hostname.
    print(proxy.Hostname)
