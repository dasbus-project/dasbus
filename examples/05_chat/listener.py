#
# Reply to a message in the chat room.
# Start the server, start the listener and run the client.
#
from dasbus.loop import EventLoop
from common import CHAT


def callback(proxy, msg):
    """The callback of the DBus signal MessageReceived."""
    if "I am Alice!" in msg:
        proxy.SendMessage("Hello Alice, I am Bob.")


if __name__ == "__main__":
    # Create a proxy of the object /org/example/Chat
    # provided by the service org.example.Chat.
    chat_proxy = CHAT.get_proxy()

    # Find a chat room to monitor.
    object_path = chat_proxy.FindRoom("Bob's room")

    # Create a proxy of the object /org/example/Chat/Rooms/1
    # provided by the service org.example.Chat.
    room_proxy = CHAT.get_proxy(object_path)

    # Connect the callback to the DBus signal MessageReceived.
    room_proxy.MessageReceived.connect(lambda msg: callback(room_proxy, msg))

    # Start the event loop.
    loop = EventLoop()
    loop.run()
