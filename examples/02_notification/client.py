#
# Send a notification to the notification server.
#
from common import NOTIFICATIONS

if __name__ == "__main__":
    # Create a proxy of the object /org/freedesktop/Notifications
    # provided by the service org.freedesktop.Notifications.
    proxy = NOTIFICATIONS.get_proxy()

    # Call the DBus method Notify.
    notification_id = proxy.Notify(
        "", 0, "face-smile", "Hello World!",
        "This notification can be ignored.",
        [], {}, 0
    )

    # Print the return value of the call.
    print("The notification {} was sent.".format(notification_id))
