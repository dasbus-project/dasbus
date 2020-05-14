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
from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="dasbus",
    version="1.1",
    author="Vendula Poncova",
    author_email="vponcova@redhat.com",
    description="DBus library in Python 3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='dbus glib library',
    url="https://github.com/rhinstaller/dasbus",
    packages=find_packages(include=['dasbus', 'dasbus.*']),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General"
        " Public License v2 or later (LGPLv2+)",
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.6',
)
