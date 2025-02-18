import libvirt


def check_connection():
    """
    this is a function to check the connection to the libvirt daemon
    this will be run while starting the server
    :return: connection object
    """
    # Connect to the system libvirt daemon
    conn = libvirt.open("qemu:///system")
    if conn is None:
        print("Failed to open connection to qemu:///system")
        exit(1)
    return conn

# Connect to the system libvirt daemon
conn = libvirt.open("qemu:///system")
