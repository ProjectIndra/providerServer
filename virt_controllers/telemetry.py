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
    this is a function to get info of a vm
    """
    
    try:

        domain = conn.lookupByName(name)
        vm_info = {
            "VM": name,
            "ID": domain.ID(),
            "Running": domain.isActive(),
            "State": domain.state()
        }
        
        return jsonify(vm_info),200

    except libvirt.libvirtError:
        return jsonify({"error":"vm not found"}),500


def list_networks():
    """
    This function will list all the networks
    """

    return jsonify({"networks":conn.listNetworks()}),200

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
    except libvirt.libvirtError:
        return jsonify({"error":"network not found"}),500