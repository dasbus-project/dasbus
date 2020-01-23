#
# Send a message to the chat room.
#
from common import CHAT

if __name__ == "__main__":
    # Create a proxy of the object /org/example/Chat
    # provided by the service org.example.Chat
    chat_proxy = CHAT.get_proxy()

    # Get an object path of the chat room.
    object_path = chat_proxy.FindRoom("Bob's room")
    print("Bob's room:", object_path)

    # Create a proxy of the object /org/example/Chat/Rooms/1
    # provided by the service org.example.Chat
    room_proxy = CHAT.get_proxy(object_path)

    # Send a message to the chat room.
    room_proxy.SendMessage("Hi, I am Alice!")

    # Get an object path of the chat room.
    object_path = chat_proxy.FindRoom("Alice's room")
    print("Alice's room:", object_path)

    # Create a proxy of the object /org/example/Chat/Rooms/2
    # provided by the service org.example.Chat
    room_proxy = CHAT.get_proxy(object_path)

    # Send a message to the chat room.
    room_proxy.SendMessage("I am Alice!")
