#
# Inhibit the system suspend and hibernation.
#
import os
from dasbus.connection import SystemMessageBus
from dasbus.unix import GLibClientUnix

if __name__ == "__main__":
    # Create a representation of a system bus connection.
    bus = SystemMessageBus()

    # Create a proxy of the /org/freedesktop/login1 object
    # provided by the org.freedesktop.login1 service with
    # an enabled support for Unix file descriptors.
    proxy = bus.get_proxy(
        "org.freedesktop.login1",
        "/org/freedesktop/login1",
        client=GLibClientUnix
    )

    # Inhibit sleep by this example.
    print("Inhibit sleep by my-example.")
    fd = proxy.Inhibit(
        "sleep",
        "my-example",
        "Running an example",
        "block"
    )

    # List active inhibitors.
    print("Active inhibitors:")
    for inhibitor in sorted(proxy.ListInhibitors()):
        print("\t".join(map(str, inhibitor)))

    # Release the inhibition lock.
    print("Release the inhibition lock.")
    os.close(fd)
