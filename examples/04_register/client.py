#
# Register the user Alice.
# Start the server and run the client twice.
#
from common import REGISTER, User, InvalidUser

if __name__ == "__main__":
    # Create a proxy of the object /org/example/Register
    # provided by the service org.example.Register
    proxy = REGISTER.get_proxy()

    # Register Alice.
    alice = User()
    alice.name = "Alice"
    alice.age = 1000

    print("Sending a DBus structure:")
    print(User.to_structure(alice))

    try:
        proxy.RegisterUser(User.to_structure(alice))
    except InvalidUser as e:
        print("Failed to register a user:", e)
        exit(1)

    # Print the registered users.
    print("Receiving DBus structures:")
    for user in proxy.Users:
        print(user)

    print("Registered users:")
    for user in User.from_structure_list(proxy.Users):
        print(user.name)
