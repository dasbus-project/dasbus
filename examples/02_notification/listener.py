#
# Handle a closed notification.
# Start the listener, run the client and close a notification.
#
from dasbus.loop import EventLoop
from common import NOTIFICATIONS


def callback(notification_id, reason):
    """The callback of the DBus signal NotificationClosed."""
    print("The notification {} was closed.".format(notification_id))


if __name__ == "__main__":
    # Create a proxy of the object /org/freedesktop/Notifications
    # provided by the service org.freedesktop.Notifications.
    proxy = NOTIFICATIONS.get_proxy()

    # Connect the callback to the DBus signal NotificationClosed.
    proxy.NotificationClosed.connect(callback)

    # Start the event loop.
    loop = EventLoop()
    loop.run()
