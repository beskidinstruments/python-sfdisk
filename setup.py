# pylint: skip-file
# flake8: noqa

# Authors
#
# - pre-alpha 0.0.1 2016 - Matt Comben
# - GA 1.0.0 2020 - Tomasz Szuster
#
# Copyrigh (c)
#
# This file is part of pysfdisk.
#
# pysfdisk is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# pysfdisk is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pysfdisk.  If not, see <http://www.gnu.org/licenses/>

from setuptools import setup
from os import path

# The directory containing this file
HERE = path.abspath(path.dirname(__file__))

# The text of the README file
with open(path.join(HERE, "README.rst")) as fid:
    long_description = fid.read()

with open(path.join(HERE, "VERSION")) as version_fh:
    version = version_fh.read()

setup(
    author="Matt Comben, Tomasz Szuster",
    author_email="matthew@dockstudios.co.uk, tomasz.szuster@gmail.com",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    license="GNU GENERAL PUBLIC LICENSE",
    name="py-disk-imager",
    packages=["pysfdisk"],
    url="https://github.com/beskidinstruments/python-sfdisk",
    version=version,
    include_package_data=True,
)
