#
# Support for DBus errors
#
# Copyright (C) 2019  Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA
#
from abc import ABCMeta, abstractmethod

from dasbus.namespace import get_dbus_name

__all__ = [
    "get_error_decorator",
    "DBusError",
    "AbstractErrorRule",
    "ErrorRule",
    "DefaultErrorRule",
    "ErrorMapper"
]


def get_error_decorator(error_mapper):
    """Generate a decorator for DBus errors.

    Create a function for decorating Python exception classes.
    The decorator will add a new rule to the given error mapper
    that will map the class to the specified error name.

    Definition of the decorator:

    .. code-block:: python

        decorator(error_name, namespace=())

    The decorator accepts a name of the DBus error and optionally
    a namespace of the DBus name. The namespace will be used as
    a prefix of the DBus name.

    Usage:

    .. code-block:: python

        # Create an error mapper.
        error_mapper = ErrorMapper()

        # Create a decorator for DBus errors and use it to map
        # the class ExampleError to the name my.example.Error.
        dbus_error = create_error_decorator(error_mapper)

        @dbus_error("my.example.Error")
        class ExampleError(DBusError):
            pass

    :param error_mapper: an error mapper
    :return: a decorator
    """
    def decorator(error_name, namespace=()):
        error_name = get_dbus_name(*namespace, error_name)

        def decorated(cls):
            error_mapper.add_rule(ErrorRule(
                exception_type=cls,
                error_name=error_name
            ))
            return cls

        return decorated

    return decorator


class DBusError(Exception):
    """A default DBus error."""
    pass


class AbstractErrorRule(metaclass=ABCMeta):
    """Abstract rule for mapping a Python exception to a DBus error."""

    __slots__ = []

    @abstractmethod
    def match_type(self, exception_type):
        """Is this rule matching the given exception type?

        :param exception_type: a type of the Python error
        :return: True or False
        """
        pass

    @abstractmethod
    def get_name(self, exception_type):
        """Get a DBus name for the given exception type.

        :param exception_type: a type of the Python error
        :return: a name of the DBus error
        """
        pass

    @abstractmethod
    def match_name(self, error_name):
        """Is this rule matching the given DBus error?

        :param error_name: a name of the DBus error
        :return: True or False
        """
        pass

    @abstractmethod
    def get_type(self, error_name):
        """Get an exception type of the given DBus error.

        param error_name: a name of the DBus error
        :return: a type of the Python error
        """
        pass


class ErrorRule(AbstractErrorRule):
    """Rule for mapping a Python exception to a DBus error."""

    __slots__ = [
        "_exception_type",
        "_error_name"
    ]

    def __init__(self, exception_type, error_name):
        """Create a new error rule.

        The rule will return the Python type exception_type
        for the DBue error error_name.

        The rule will return the DBue name error_name for
        the Python type exception_type

        :param exception_type: a type of the Python error
        :param error_name: a name of the DBus error
        """
        self._exception_type = exception_type
        self._error_name = error_name

    def match_type(self, exception_type):
        """Is this rule matching the given exception type?"""
        return self._exception_type == exception_type

    def get_name(self, exception_type):
        """Get a DBus name for the given exception type."""
        return self._error_name

    def match_name(self, error_name):
        """Is this rule matching the given DBus error?"""
        return self._error_name == error_name

    def get_type(self, error_name):
        """Get an exception type of the given DBus error."""
        return self._exception_type


class DefaultErrorRule(AbstractErrorRule):
    """Default rule for mapping a Python exception to a DBus error."""

    __slots__ = [
        "_default_type",
        "_default_namespace"
    ]

    def __init__(self, default_type, default_namespace):
        """Create a new default rule.

        The rule will return the Python type default_type
        for the all DBus errors.

        The rule will generate a DBus name with the prefix
        default_namespace for all Python exception types.

        :param default_type: a default type of the Python error
        :param default_namespace: a default namespace of the DBus error
        """
        self._default_type = default_type
        self._default_namespace = default_namespace

    def match_type(self, exception_type):
        """Is this rule matching the given exception type?"""
        return True

    def get_name(self, exception_type):
        """Get a DBus name for the given exception type."""
        return get_dbus_name(*self._default_namespace, exception_type.__name__)

    def match_name(self, error_name):
        """Is this rule matching the given DBus error?"""
        return True

    def get_type(self, error_name):
        """Get an exception type of the given DBus error."""
        return self._default_type


class ErrorMapper(object):
    """Class for mapping Python exceptions to DBus errors."""

    __slots__ = ["_error_rules"]

    def __init__(self):
        """Create a new error mapper."""
        self._error_rules = []
        self.reset_rules()

    def add_rule(self, rule: AbstractErrorRule):
        """Add a rule to the error mapper.

        The new rule will have a higher priority than
        the rules already contained in the error mapper.

        :param rule: an error rule
        :type rule: an instance of AbstractErrorRule
        """
        self._error_rules.append(rule)

    def reset_rules(self):
        """Reset rules in the error mapper.

        Reset the error rules to the initial state.
        All rules will be replaced with the default ones.
        """
        # Clear the list.
        self._error_rules = []

        # Add the default rules.
        self.add_rule(DefaultErrorRule(
            default_type=DBusError,
            default_namespace=("not", "known", "Error")
        ))

    def get_error_name(self, exception_type):
        """Get a DBus name of the Python exception.

        Try to find a matching rule in the error mapper.
        If a rule matches the given exception type, use
        the rule to get the name of the DBus error.

        The rules in the error mapper are processed in
        the reversed order to respect the priority of
        the rules.

        :param exception_type: a type of the Python error
        :type exception_type: a subclass of Exception
        :return: a name of the DBus error
        :raise LookupError: if no name is found
        """
        for rule in reversed(self._error_rules):
            if rule.match_type(exception_type):
                return rule.get_name(exception_type)

        raise LookupError(
            "No name found for '{}'.".format(exception_type.__name__)
        )

    def get_exception_type(self, error_name):
        """Get a Python exception type of the DBus error.

        Try to find a matching rule in the error mapper.
        If a rule matches the given name of a DBus error,
        use the rule to get the type of a Python exception.

        The rules in the error mapper are processed in
        the reversed order to respect the priority of
        the rules.

        :param error_name: a name of the DBus error
        :return: a type of the Python exception
        :rtype: a subclass of Exception
        :raise LookupError: if no type is found
        """
        for rule in reversed(self._error_rules):
            if rule.match_name(error_name):
                return rule.get_type(error_name)

        raise LookupError("No type found for '{}'.".format(error_name))
