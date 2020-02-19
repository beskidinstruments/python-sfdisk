# pylint: skip-file
# flake8: noqa

from block_device import BlockDevice
from fastlogging import LogInit

if __name__ == "__main__":

    disk = BlockDevice(path="/dev/sdc", use_sudo=True)
    # Simple way for invoking script
    archive_name = disk.run(mbr_filename="mbr_file", target_dir="/home/user/Desktop")
    print(archive_name)

    # More complicated but with logging capabilities via fastlogging
    logger = LogInit(
        console=True,
        colors=True,
        useThreads=True,
    )
    partition_table_file = "partition_table_file"
    logger.info("Dumping partition tables via sfdisk to file: %s", partition_table_file)
    with open(partition_table_file, "w") as dump_file:
        dump_file.write(disk.read_partition_table())

    mbr_file_name = "mbr_file"
    logger.info("Dumping the MBR to file: %s", mbr_file_name)
    disk.dump_mbr(destination_file=mbr_file_name)

    logger.info("Dumping partitions to temporary directory")
    dumped_partitions = disk.dump_partitions()
    logger.info("Partitions dumped to: %s", dumped_partitions)

    logger.info("Creating archive file")
    archive_file = disk.compress_dumped_partitions(target_dir="/home/user/Desktop")
    logger.info("Archive file path %s", archive_name)
