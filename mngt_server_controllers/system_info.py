import os
import psutil

def get_system_info():
    num_cpus = os.cpu_count()
    total_ram = psutil.virtual_memory().total / (1024 ** 3)  # Convert to GB
    disk_partitions = psutil.disk_partitions()
    
    max_disk_space = max(
        psutil.disk_usage(part.mountpoint).total for part in disk_partitions
    ) / (1024 ** 3)  # Convert to GB

    return num_cpus, round(total_ram, 2), round(max_disk_space, 2)