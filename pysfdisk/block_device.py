"""
Code for handling block device.

Providing data about partition types, filesystem, create backup of mbr, partition schema, dumping data to file.

"""

# Copyright (c) 2016 - Matt Comben
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

import os
import json
import pathlib
import subprocess  # nosec # noqa: S404
from typing import Union
from subprocess import PIPE, DEVNULL  # nosec # noqa: S404

from pysfdisk.errors import NotRunningAsRoot, BlockDeviceDoesNotExist
from pysfdisk.partition import Partition


def find_executable(name: str) -> Union[str, classmethod]:
    """
    Return valid executable path for provided name.

    :param name: binary, executable name
    :return: Return the string representation of the path with forward (/) slashes.

    """
    standard_executable_paths = ["/bin", "/sbin", "/usr/local/bin", "/usr/local/sbin", "/usr/bin", "/usr/sbin"]

    for path in standard_executable_paths:
        executable_path = pathlib.Path(path) / name
        if executable_path.exists():
            return executable_path.as_posix()

    return FileNotFoundError


class BlockDevice:
    """Provide interface to obtain and set partition tables."""

    SFDISK_EXECUTABLE = find_executable(name="sfdisk")
    DD_EXECUTABLE = find_executable(name="dd")
    LSBLK_EXECUTABLE = find_executable(name="lsblk")
    PXZ_EXECUTABLE = find_executable(name="pxz")
    SUDO_EXEC = find_executable(name="sudo")

    def __init__(self, path, use_sudo=False):
        """Set member variables, perform checks and obtain the initial partition table."""
        # Setup member variables
        self.path = path
        self.use_sudo = use_sudo
        self.partitions = {}
        self.label = None
        self.uuid = None

        self._assert_root()
        self._ensure_exists()
        self._read_partition_table()
        self._umount_partitions()

    def get_partitions(self):
        """Return the partition objects for the block object."""
        return self.partitions

    def dump_partition_table(self):
        """Dump partition table to string."""
        command_list = [self.SFDISK_EXECUTABLE, "-d", self.path]
        if self.use_sudo:
            command_list.insert(0, self.SUDO_EXEC)
        process = subprocess.Popen(command_list, stdout=PIPE)  # nosec # noqa: S603,DUO116
        partition_table = process.communicate()[0]
        return partition_table.decode()

    def dump_mbr(self, destination_file: str) -> Union[str, None]:
        """
        Dump MBR to file.

        :param destination_file: The name of file to which disk data will be dumped
        :return: output of dd command

        """
        command_list = [self.DD_EXECUTABLE, f"if={self.path}", f"of={destination_file}", "bs=512", "count=1"]
        if self.use_sudo:
            command_list.insert(0, self.SUDO_EXEC)
        save_mbr = subprocess.run(command_list, stdout=PIPE, stderr=PIPE, check=True)  # nosec # noqa: S603,DUO116
        return save_mbr.check_returncode()

    def dump_partitions(self, directory: str) -> dict:
        """
        Create backup of the partition to file via partclone.

        :param directory: The directory path to which partition backup will be saved
        :return: dict which contains name of partition and file path to which backup was saved

        """
        command_list = []
        destination_files = {}

        partitions_list = self.get_fs_types()
        for partition, fs_type in partitions_list.items():
            if fs_type == "vfat":
                command_list = [
                    find_executable(name=f"partclone.fat"),
                    "-I",
                    "-F",
                    "-d",
                    "-c",
                    "-s",
                    f"/dev/{partition}",
                    "-o",
                    f"{directory}/{partition}",
                ]
            elif fs_type == "ext4":
                command_list = [
                    find_executable(name=f"partclone.{fs_type}"),
                    "-d",
                    "-c",
                    "-s",
                    f"/dev/{partition}",
                    "-o",
                    f"{directory}/{partition}",
                ]
            destination_files[partition] = f"{directory}/{partition}"

            if self.use_sudo:
                command_list.insert(0, self.SUDO_EXEC)
                subprocess.run(command_list, check=True)  # nosec # noqa: S603,DUO116

                # pylint: disable=line-too-long
                subprocess.check_output([self.SUDO_EXEC, "chmod", "644", f"{directory}/{partition}"])  # nosec # noqa: S603,DUO116

        return destination_files

    def _umount_partitions(self) -> None:
        """
        Umount mounted partition to allow it to be processed by partclone or dd.

        :return: return code from the dd command

        """
        partition_list = self.get_fs_types()

        # pylint: disable=unused-variable
        for key, value in partition_list.items():
            command_list = ["umount", f"/dev/{key}"]
            if self.use_sudo:
                command_list.insert(0, self.SUDO_EXEC)
            subprocess.run(command_list, stdout=DEVNULL, stderr=DEVNULL, check=False)  # nosec  # noqa: S603

    def get_fs_types(self) -> dict:
        """
        Get partition filesystem type via lsblk.

        :return: fs_types, dict which contain partition name and filesystem type

        """
        disk_name = self.path.split("/")[2]
        fs_types = {}

        command_list = [self.LSBLK_EXECUTABLE, "-o", "NAME,TYPE,FSTYPE", "-b", "-J"]
        if self.use_sudo:
            command_list.insert(0, self.SUDO_EXEC)
        command_output = json.loads(subprocess.check_output(command_list))  # nosec # noqa: S603,DUO116
        all_disks = command_output.get("blockdevices")

        for disk in all_disks:
            if disk.get("name") == disk_name:
                all_disks = disk.get("children")

        for _ in all_disks:
            if _.get("fstype"):
                fs_types[_.get("name")] = _.get("fstype")

        return fs_types

    def _read_partition_table(self):
        """Create the partition table using sfdisk and load partitions."""
        command_list = [self.SFDISK_EXECUTABLE, "--json", self.path]
        if self.use_sudo:
            command_list.insert(0, self.SUDO_EXEC)
        disk_config = json.loads(subprocess.check_output(command_list))  # nosec # noqa: S603,DUO116
        self.label = disk_config["partitiontable"]["label"] or None
        self.uuid = disk_config["partitiontable"]["id"] or None

        for partition_config in disk_config["partitiontable"]["partitions"]:
            partition = Partition.load_from_sfdisk_output(partition_config, self)
            self.partitions[partition.get_partition_number()] = partition

    def _ensure_exists(self):
        if not os.path.exists(self.path):
            raise BlockDeviceDoesNotExist("Block device %s does not exist" % self.path)

    def _assert_root(self):
        """Ensure that the script is being run as root, or 'as root' has been specified."""
        if os.getuid() != 0 and not self.use_sudo:
            raise NotRunningAsRoot("Must be running as root or specify to use sudo")
