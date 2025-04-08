from flask import jsonify,request

import subprocess
import re
import paramiko

import os
import libvirt


#internal import
from virt import conn
from mngt_server_controllers import conf
from virt_controllers import telemetry


def create_vm():
    """Creates a VM using virt-install, booting from an ISO (no disk)."""
    

    data = request.get_json()
    name = data.get("name")
    vcpus = data.get("vcpus")
    memory = data.get("memory")
    iso_path = data.get("iso_path", "/var/lib/libvirt/images/ubuntu-server.iso")

    cmd = [
        "virt-install",
        "--name", name,
        "--ram", str(memory),
        "--vcpus", str(vcpus),
        "--cdrom", iso_path,  # Boot directly from ISO
        "--os-type", "linux",
        "--os-variant", "ubuntu22.04",
        "--network", "network=default",
        "--graphics", "vnc",
        "--noautoconsole"
    ]

    try:
        subprocess.run(cmd, check=True)
        
        return jsonify({"message": "VM created successfully"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500

# Create VM from existing qcow file


def create_vm_qvm():
    """Creates a VM using an existing QCOW2 disk."""

    data = request.get_json()

    print(f"Data received: {data}")

    name = data.get("name")
    vcpus = data.get("vcpus")
    memory = data.get("memory")
    qvm_path = data.get("qvm_path", "./images/avinash.qcow2")

    if not name or not vcpus or not memory:
        return jsonify({"error": "Missing required parameters"}), 400

    # # first check if the qvm file exists
    # if not os.path.exists(qvm_path):
    #     return jsonify({"error": f"File '{qvm_path}' does not exist"}),500

    # Then copy the qvm with some other name
    # new_qvm_path = f"./images/{name}.qcow2"

    # try:
    #     subprocess.run(["cp", qvm_path, new_qvm_path], check=True)
    # except subprocess.CalledProcessError as e:
    #     print(f"Error copying file: {e}")
    #     return jsonify({"error": e.stderr}), 500
    
    cmd = [
    "virt-install",
    "--name", name,
    "--ram", str(memory),
    "--vcpus", str(vcpus),
    f"--disk={qvm_path},format=qcow2",
    "--import",
    "--check", "path_in_use=off",
    "--os-variant", "ubuntu22.04",
    "--network", "network=default",
    "--graphics", "vnc",
    "--noautoconsole"
    ]

    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        return jsonify({"message": "VM (through existing qvm) created successfully"}), 200
    except subprocess.CalledProcessError as e:
        print(f"Error creating VM: {e.stderr}")
        return jsonify({"error": e.stderr}), 500  # Now returns the actual error message

def stop_vm():
    """
    This function will stop any active VM
    """

    data = request.get_json()
    name = data.get("name")

    try:
        domain = conn.lookupByName(name)
        domain.destroy()
        return jsonify({"message": "VM stopped successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def delete_vm():
    """Deletes a VM and removes its storage."""

    data = request.get_json()
    name = data.get("name")

    try:
        conn = libvirt.open(os.environ.get('PRV_VIRT_SYSTEM'))
        if conn is None:
            return jsonify({"error": "Failed to connect to libvirt"}), 500

        try:
            domain = conn.lookupByName(name)
        except libvirt.libvirtError:
            return jsonify({"error": f"VM '{name}' not found"}), 404

        # Get the storage path before undefining
        xml_desc = domain.XMLDesc(0)
        disk_path = extract_disk_path(xml_desc)

        # Destroy the VM if running
        if domain.isActive():
            domain.destroy()

        # Undefine the VM
        domain.undefine()

        # Remove the disk file if it exists
        # if disk_path and os.path.exists(disk_path):
        #     os.remove(disk_path)

        return jsonify({"message": f"VM '{name}' deleted successfully"}), 200

    except libvirt.libvirtError as e:
        return jsonify({"error": str(e)}), 500

def extract_disk_path(xml_desc):
    """Extracts the disk path from VM XML description."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_desc)
    disk = root.find(".//disk[@device='disk']/source")
    return disk.get("file") if disk is not None else None


def start_vm():
    """
    This function will start any inactive VM
    """

    data = request.get_json()
    name = data.get("name")

    try:
        domain = conn.lookupByName(name)
        domain.create()
        return jsonify({"message": "VM started successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def query_vm():
    """
    This function will query the status of a VM
    """

    data = request.get_json()
    vcpu = data.get("vcpu")
    memory = data.get("memory")

    try:
        # first get all vm names
        active_vms = telemetry.list_running_vms()
        inactive_vms = telemetry.list_inactive_vms()

        # now get info of each vm of vcpu and memory
        vms = []
        vms += active_vms
        vms += inactive_vms

        # now get the info of each vm
        vm_info = []
        for vm in vms:
            vm_info += telemetry.get_vm_info(vm)

        # now sum up the vcpu and memory
        total_vcpu = 0
        total_memory = 0

        for vm in vm_info:
            total_vcpu += vm["VCPU-Allocated"]
            total_memory += vm["RAM-Allocated"]

        # now add the vcpu and memory of the new vm
        total_vcpu += vcpu
        total_memory += memory

        # first check if max limits are set
        if not os.environ.get("PROVIDER_SERVER_MAX_VMS"):
            return jsonify({"error": "Max limits not set"}), 500
        if not os.environ.get("PROVIDER_SERVER_MAX_CPU"):
            return jsonify({"error": "Max limits not set"}), 500

        # check with the max limits
        if total_vcpu > int(os.environ.get("PROVIDER_SERVER_MAX_CPU")):
            return jsonify({"error": "CPU limit exceeded"}), 500

        if total_memory > int(os.environ.get("PROVIDER_SERVER_MAX_RAM")):
            return jsonify({"error": "Memory limit exceeded"}), 500

        return jsonify({"message": "VM can be created"}), 200

    except Exception as e:

        return jsonify({"error": str(e)}), 500

