Development and testing
=======================

Install `podman <https://podman.io/>`_ and use the following command to run all tests
in a container. It doesn't require any additional dependencies:

.. code-block::

    make container-ci

Use the command below to run only the unit tests:

.. code-block::

    make container-ci CI_CMD="make test"
