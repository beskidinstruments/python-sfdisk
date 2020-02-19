# PYsfdisk

A Python API for linux sfdisk utility

Note: 
Module will work only on Linux OS'es, required executables used in this module:
* sudo
* lsblk
* sfdisk
* pxz
* tar
* partclone
    
Please ensure that you have installed above


## Install
```
git clone https://github.com/beskidinstruments/python-sfdisk
sudo pip install ./
```



## Example
```python
import pysfdisk
```    


Create block device object for the disk
```python
disk = pysfdisk.BlockDevice(path='/dev/nvme0n1')
```


Optionally, if not using root and sudo is available, use this
```python
disk = pysfdisk.BlockDevice(path='/dev/nvme0n1', use_sudo=True)
```


Partitions information is automatically loaded
```python
disk.get_partitions()['0'].uuid
403ACCB2-0B00-465F-B190-B59C45CFD860
```

Read partitions table.

```python
disk.read_partition_table()
```

Create compressed archive from all partitions.
```python
disk.run(mbr_filename="mbr_file", target_dir="/home/user/Desktop")
```

    
For more examples please use files in the example directory

# License

pysfdisk is licensed under GPL v2.


# Authors

- pre-alpha 0.0.1 2016 - Matt Comben
- GA 1.0.0 2020 - Tomasz Szuster

