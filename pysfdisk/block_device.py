"""
Code for handling block device.

Providing data about partition types, filesystem, create backup of mbr, partition schema, dumping data to file.

"""

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

import os
import json
import pathlib
import tempfile
import subprocess  # nosec # noqa: S404
from typing import Union
from subprocess import PIPE, DEVNULL  # nosec # noqa: S404

from pysfdisk.errors import NotRunningAsRoot, BlockDeviceDoesNotExist  # noqa: I900
from pysfdisk.partition import Partition  # noqa: I900


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

    DD_EXEC = find_executable(name="dd")
    LSBLK_EXEC = find_executable(name="lsblk")
    PXZ_EXEC = find_executable(name="pxz")
    SFDISK_EXEC = find_executable(name="sfdisk")
    SUDO_EXEC = find_executable(name="sudo")
    TAR_EXEC = find_executable(name="tar")

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
        self._temp_dir = tempfile.mkdtemp(dir=tempfile.gettempdir())

    def get_partitions(self):
        """Return the partition objects for the block object."""
        return self.partitions

    def read_partition_table(self):
        """Read partition table to string."""
        command_list = [self.SFDISK_EXEC, "-d", self.path]
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
        command_list = [
            self.DD_EXEC,
            f"if={self.path}",
            f"of={self._temp_dir}/{destination_file}",
            "bs=512",
            "count=1"
        ]
        if self.use_sudo:
            command_list.insert(0, self.SUDO_EXEC)
        save_mbr = subprocess.run(command_list, stdout=PIPE, stderr=PIPE, check=True)  # nosec # noqa: S603,DUO116
        return save_mbr.check_returncode()

    def _change_file_permissions(self, file_name: str):
        """
        Change file permission for provided file name.

        :param file_name: The name of file on which new permissions be applied
        :return:

        """
        command_list = ["chmod", "644", f"{self._temp_dir}/{file_name}"]  # nosec # noqa: S603,DUO116
        if self.use_sudo:
            command_list.insert(0, self.SUDO_EXEC)
        return subprocess.check_output(command_list)  # nosec # noqa: S603,DUO116

    def dump_partitions(self) -> dict:
        """
        Create backup of the partition to file via partclone.

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
                    f"{self._temp_dir}/{partition}",
                ]
            elif fs_type == "ext4":
                command_list = [
                    find_executable(name=f"partclone.{fs_type}"),
                    "-d",
                    "-c",
                    "-s",
                    f"/dev/{partition}",
                    "-o",
                    f"{self._temp_dir}/{partition}",
                ]
            destination_files[partition] = f"{self._temp_dir}/{partition}"

            if self.use_sudo:
                command_list.insert(0, self.SUDO_EXEC)
                subprocess.run(command_list, check=True)  # nosec # noqa: S603,DUO116

                self._change_file_permissions(file_name=partition)

        return destination_files

    def _delete_temp_dir(self) -> None:

        command_list = ["rm", "-rf", self._temp_dir]
        if self.use_sudo:
            command_list.insert(0, self.SUDO_EXEC)
        subprocess.check_output(command_list)  # nosec # noqa: S603,DUO116

    def compress_dumped_partitions(self, target_dir: str, file_name: str = "compressed_partitions") -> str:
        """
        Compress files via pxz https://www.linuxlinks.com/pxz-parallel-lzma-compressor-liblzma/.

        :param target_dir: The name of directory in which archive will be placed
        :param file_name: The name of compressed archive
        :return: full path to the compressed archive

        """
        command_list = [
            self.TAR_EXEC,
            "-I",
            self.PXZ_EXEC,
            "-cf",
            f"{target_dir}/{file_name}.tar.xz",
            "-C",
            self._temp_dir,
            "."
        ]
        if self.use_sudo:
            command_list.insert(0, self.SUDO_EXEC)
            subprocess.check_output(command_list)  # nosec # noqa: S603

        # Delete temporary directory
        self._delete_temp_dir()

        return f"{target_dir}/{file_name}.tar.xz"

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

        command_list = [self.LSBLK_EXEC, "-o", "NAME,TYPE,FSTYPE", "-b", "-J"]
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
        command_list = [self.SFDISK_EXEC, "--json", self.path]
        if self.use_sudo:
            command_list.insert(0, self.SUDO_EXEC)
        disk_config = json.loads(subprocess.check_output(command_list))  # nosec # noqa: S603,DUO116
        self.label = disk_config["partitiontable"]["label"] or None
        self.uuid = disk_config["partitiontable"]["id"] or None

        for partition_config in disk_config["partitiontable"]["partitions"]:
            partition = Partition.load_from_sfdisk_output(partition_config, self)
            self.partitions[partition.get_partition_number()] = partition

    def run(self, mbr_filename: str, target_dir: str) -> str:
        """
        Create archive from disk partitions.

        :param mbr_filename: The name of file which will contain mbr data
        :param target_dir: The name of directory in which compressed archive will be placed
        :return: The full path to the compressed archive file

        """
        with open(f"{self._temp_dir}/partition_table", "w") as file:
            file.write(self.read_partition_table())
        self.dump_mbr(destination_file=mbr_filename)
        self.dump_partitions()
        compressed_file_name = self.compress_dumped_partitions(target_dir=target_dir)
        return compressed_file_name

    def _ensure_exists(self):
        if not os.path.exists(self.path):
            raise BlockDeviceDoesNotExist("Block device %s does not exist" % self.path)

    def _assert_root(self):
        """Ensure that the script is being run as root, or 'as root' has been specified."""
        if os.getuid() != 0 and not self.use_sudo:
            raise NotRunningAsRoot("Must be running as root or specify to use sudo")
