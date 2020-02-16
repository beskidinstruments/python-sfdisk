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
import subprocess
from typing import Union

from pysfdisk.errors import NotRunningAsRoot, BlockDeviceDoesNotExist
from pysfdisk.partition import Partition


def find_executable(name: str) -> Union[str, None]:
    """
    Return valid executable path for provided name.

    :param name: binary, executable name
    :return: Return the string representation of the path with forward (/) slashes.

    """
    standard_executable_paths = ["/bin", "/sbin", "/usr/local/bin", "/usr/local/sbin"]

    for path in standard_executable_paths:
        executable_path = pathlib.Path(path) / name
        if executable_path.exists():
            return executable_path.as_posix()

    return None


class BlockDevice:
    """Provide interface to obtain and set partition tables."""

    SFDISK_EXECUTABLE = find_executable(name="sfdisk")
    DD_EXECUTABLE = find_executable(name="dd")
    LSBLK_EXECUTABLE = find_executable(name="lsblk")

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
            command_list.insert(0, "sudo")
        process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=None, shell=False)
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
            command_list.insert(0, "sudo")
        save_mbr = subprocess.run(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return save_mbr.check_returncode()

    def _umount_partitions(self) -> None:
        """
        Umount mounted partition to allow it to be processed by partclone or dd.

        :return: return code from the dd command

        """
        partition_list = self.get_fs_types()

        for key, value in partition_list.items():
            command_list = ["umount", f"/dev/{key}"]
            if self.use_sudo:
                command_list.insert(0, "sudo")
            subprocess.run(command_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    def get_fs_types(self):
        disk_name = self.path.split("/")[2]
        fs_types = {}

        command_list = [self.LSBLK_EXECUTABLE, "-o", "NAME,TYPE,FSTYPE", "-b", "-J"]
        if self.use_sudo:
            command_list.insert(0, "sudo")
        command_output = json.loads(subprocess.check_output(command_list, shell=False))
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
            command_list.insert(0, "sudo")
        disk_config = json.loads(subprocess.check_output(command_list, shell=False))
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
