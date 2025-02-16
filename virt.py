import libvirt

# Connect to the system libvirt daemon
conn = libvirt.open("qemu:///system")
if conn is None:
    print("Failed to open connection to qemu:///system")
    exit(1)

# Function to list all active VMs
def list_active_vms():
    active_vms = conn.listDomainsID()
    if not active_vms:
        print("No active VMs.")
    else:
        print("Active VMs:")
        for vm_id in active_vms:
            domain = conn.lookupByID(vm_id)
            print(f"- {domain.name()} (ID: {vm_id})")

# Function to list all VM names (both running and inactive)
def list_all_vms():
    vms = conn.listAllDomains()
    if not vms:
        print("No VMs found.")
    else:
        print("All VMs:")
        for vm in vms:
            print(f"- {vm.name()} (Running: {vm.isActive()})")

# Function to get details of a specific VM
def get_vm_info(vm_name):
    try:
        domain = conn.lookupByName(vm_name)
        print(f"VM: {vm_name}")
        print(f"  ID: {domain.ID()}")
        print(f"  Running: {domain.isActive()}")
        print(f"  State: {domain.state()[0]}")
    except libvirt.libvirtError:
        print(f"VM '{vm_name}' not found.")

# Function to check if a VM exists
def vm_exists(vm_name):
    try:
        conn.lookupByName(vm_name)
        print(f"VM '{vm_name}' exists.")
        return True
    except libvirt.libvirtError:
        print(f"VM '{vm_name}' does not exist.")
        return False

# Run test functions
list_active_vms()
list_all_vms()
# get_vm_info("test-vm")  # Replace "test-vm" with an actual VM name
# vm_exists("test-vm")  # Replace "test-vm" accordingly

# Close connection
conn.close()
