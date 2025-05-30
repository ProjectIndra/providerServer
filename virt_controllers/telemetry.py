from flask import jsonify

#internal import
from virt import conn

def list_running_vms():
    """
    this is a function to list the vms
    :return: list of vms
    """
    vms = []
    for id in conn.listDomainsID():
        dom = conn.lookupByID(id)
        vms.append(dom.name())

    return jsonify({"vms": vms}),200

def list_inactive_vms():
    """
    this is a function to list the inactive vms
    :return: list of inactive vms
    """
    vms = []
    for id in conn.listDefinedDomains():
        vms.append(id)

    return jsonify({"vms": vms}),200

# Function to get details of a specific VM
def get_vm_info(name):
    """
    This function retrieves information about a VM, including CPU, RAM, and storage usage.
    """
    try:
        domain = conn.lookupByName(name)
        vm_info = {
            "VM": name,
            "ID": domain.ID(),
            "Running": domain.isActive(),
            "VCPU-Allocated": domain.vcpusFlags(),
            "RAM-Allocated": domain.maxMemory(),
            "VCPU-Used": domain.info()[3],
            "RAM-Used": domain.info()[2],
        }

        # converting into human readable format
        vm_info["RAM-Allocated"] = int(vm_info['RAM-Allocated'] / 1024)
        vm_info["RAM-Used"] = int(vm_info['RAM-Used'] / 1024)

        return jsonify(vm_info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def list_networks():
    """
    This function will list all the networks
    """

    # first get active networks
    active_networks = conn.listNetworks()
    # get inactive networks
    inactive_networks = conn.listDefinedNetworks()
    return jsonify({"active_networks": active_networks, "inactive_networks": inactive_networks}),200

def get_network_info(name):
    """
    This function will get the info of a network
    """

    try:
        network = conn.networkLookupByName(name)
        info = {
            "Name": network.name(),
            "UUID": network.UUIDString(),
            "Bridge": network.bridgeName(),
            "Active": network.isActive()
        }
        return jsonify(info),200
    except Exception as e:
        return jsonify({"error":str(e)}),500