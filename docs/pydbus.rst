dasbus vs pydbus
================

The dasbus library used to be based on `pydbus <https://github.com/LEW21/pydbus>`_, but it was
later reimplemented. We have changed the API and the implementation of the library based on our
experience with pydbus. However, it should be possible to modify dasbus classes to work the same
way as pydbus classes.

What is new
-----------

- Support for asynchronous DBus calls: DBus methods can be called asynchronously.

- Support for Unix file descriptors: It is possible to send or receive Unix file descriptors.

- Mapping DBus errors to exceptions: Use Python exceptions to propagate and handle DBus errors.
  Define your own rules for mapping errors to exceptions and back. See the
  :class:`ErrorMapper <dasbus.error.ErrorMapper>` class

- Support for type hints: Use Python type hints from :mod:`dasbus.typing` to define DBus types.

- Generating XML specifications: Automatically generate XML specifications from Python classes
  with the :func:`dbus_interface <dasbus.server.interface.dbus_interface>` decorator.

- Support for DBus structures: Represent DBus structures (dictionaries of variants) by Python
  objects. See the :class:`DBusData <dasbus.structure.DBusData>` class.

- Support for groups of DBus objects: Use DBus containers from :mod:`dasbus.server.container`
  to publish groups of Python objects.

- Composition over inheritance: The library follows the principle of composition over
  inheritance. It allows to easily change the default behaviour.

- Lazy DBus connections: DBus connections are established on demand.

- Lazy DBus proxies: Attributes of DBus proxies are created on demand.


What is different
-----------------

- No context managers: There are no context managers in dasbus. Context managers and event
  loops don't work very well together.

- No auto-completion: There is no support for automatic completion of DBus names and paths.
  We recommend to work with constants defined by classes from :mod:`dasbus.identifier`
  instead of strings.

- No unpacking of variants: The dasbus library doesn't unpack variants by default. It means
  that values received from DBus match the types declared in the XML specification. Use the
  :func:`get_native <dasbus.typing.get_native>` function to unpack the values.

- Obtaining proxy objects: Call the :meth:`get_proxy <dasbus.connection.MessageBus.get_proxy>`
  method to get a proxy of the specified DBus object.

- No single-interface view: DBus proxies don't support single-interface views. Use the
  :class:`InterfaceProxy <dasbus.client.proxy.InterfaceProxy>` class to access a specific
  interface of a DBus object.

- Higher priority of standard interfaces: If there is a DBus interface in the XML specification
  that redefines a member of a standard interface, the DBus proxy will choose a member of the
  standard interface. Use the :class:`InterfaceProxy <dasbus.client.proxy.InterfaceProxy>` class
  to access a specific interface of a DBus object.

- No support for help: Members of DBus proxies are created lazily, so the build-in ``help``
  function doesn't return useful information about the DBus interfaces.

- Watching DBus names: Use :class:`a service observer <dasbus.client.observer.DBusObserver>`
  to watch a DBus name.

- Acquiring DBus names: Call the :meth:`register_service <dasbus.connection.MessageBus.register_service>`
  method to acquire a DBus name.

- Providing XML specifications: Use the ``__dbus_xml__`` attribute to provide the XML
  specification of a DBus object. Or you can generate it from the code using the
  :func:`dbus_interface <dasbus.server.interface.dbus_interface>` decorator.

- No support for polkit: There is no support for the DBus service ``org.freedesktop.PolicyKit1``.

What is the same (for now)
--------------------------

- No support for other event loops: Dasbus uses GLib as its backend, so it requires to use
  the GLib event loop. However, the GLib part of dasbus is separated from the rest of the code,
  so it shouldn't be too difficult to add support for a different backend. It would be necessary
  to replace :class:`dasbus.typing.Variant` and :class:`dasbus.typing.VariantType` with their
  abstractions and reorganize the code.

- No support for org.freedesktop.DBus.ObjectManager: There is no support for object managers,
  however the :class:`DBus containers <dasbus.server.container.DBusContainer>` could be a good
  starting point.
