import libvirt
import os

# environment imports
import dotenv
dotenv.load_dotenv()


def check_connection():
    """
    this is a function to check the connection to the libvirt daemon
    this will be run while starting the server
    :return: connection object
    """
    # Connect to the system libvirt daemon
    conn = libvirt.open(os.environ.get('PRV_VIRT_SYSTEM'))
    if conn is None:
        print("Failed to open connection to environ.get('PRV_VIRT_SYSTEM')")
        exit(1)
    return conn

# Connect to the system libvirt daemon
conn = libvirt.open(os.environ.get('PRV_VIRT_SYSTEM'))
