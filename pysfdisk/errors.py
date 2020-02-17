"""Container for custom errors."""

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


class PysfdiskException(Exception):
    """Base exception for pysfdisk."""

    # pylint: disable=unnecessary-pass
    pass


class NotRunningAsRoot(PysfdiskException):
    """Command is not running as root."""

    # pylint: disable=unnecessary-pass
    pass


class BlockDeviceDoesNotExist(PysfdiskException):
    """Block device does not exist."""

    # pylint: disable=unnecessary-pass
    pass


class MissingAttribute(PysfdiskException):
    """A required attribute has not been set."""

    # pylint: disable=unnecessary-pass
    pass
