#
# Say hello to the world.
# Start the server and run the client.
#
from common import HELLO_WORLD

if __name__ == "__main__":
    # Create a proxy of the object /org/example/HelloWorld
    # provided by the service org.example.HelloWorld
    proxy = HELLO_WORLD.get_proxy()

    # Call the DBus method Hello and print the return value.
    print(proxy.Hello("World"))
