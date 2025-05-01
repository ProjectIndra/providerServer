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
    """Creates a VM using a delta QCOW2 disk based on a base image."""

    data = request.get_json()
    print(f"Data received: {data}")

    name = data.get("name")
    vcpus = data.get("vcpus")
    memory = data.get("memory")
    qvm_path = "avinash.qcow2" # Base image path
    images_dir = "./images"  # Directory where delta images are stored

    if not name or not vcpus or not memory:
        return jsonify({"error": "Missing required parameters"}), 400

    # Check if base qvm file exists
    if not os.path.exists(images_dir+"/"+qvm_path):
        return jsonify({"error": f"Base image '{qvm_path}' does not exist"}), 500

    # Create delta (backed) qcow2
    new_qvm_path = os.path.join(images_dir, f"{name}.qcow2")

    try:
        subprocess.run([
            "qemu-img", "create",
            "-f", "qcow2",    # Output disk format
            "-F", "qcow2",    # Backing file format
            "-b", qvm_path,  # Absolute path to base image
            new_qvm_path
        ], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error creating delta disk: {e}")
        return jsonify({"error": "Failed to create delta qcow2"}), 500


    # Now use the delta disk in virt-install
    cmd = [
        "virt-install",
        "--name", name,
        "--ram", str(memory),
        "--vcpus", str(vcpus),
        f"--disk={new_qvm_path},format=qcow2",
        "--import",
        "--check", "path_in_use=off",
        "--os-variant", "ubuntu22.04",
        "--network", "network=default",
        "--graphics", "vnc",
        "--noautoconsole"
    ]

    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return jsonify({"message": "VM created successfully using delta disk"}), 200
    except subprocess.CalledProcessError as e:
        print(f"Error creating VM: {e.stderr}")
        return jsonify({"error": e.stderr}), 500

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

    # Check for missing or invalid data in request
    if "vcpu" not in data or "memory" not in data:
        return jsonify({"error": "vcpu and memory must be provided"}), 400

    try:
        vcpu = int(data["vcpu"])
        memory = int(data["memory"])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid input data for vcpu or memory"}), 400

    try:
        # First get all VM names
        active_vms_response = telemetry.list_running_vms()
        inactive_vms_response = telemetry.list_inactive_vms()

        # Check if the response contains the expected 'vms' key
        active_vms = active_vms_response[0].json.get("vms")
        inactive_vms = inactive_vms_response[0].json.get("vms")

        if active_vms is None or inactive_vms is None:
            return jsonify({"error": "Missing 'vms' key in response"}), 500

        # Now get info for each VM (vcpu and memory)
        vms = active_vms + inactive_vms

        vm_info = []
        for vm in vms:
            vm_info_response = telemetry.get_vm_info(vm)
            # Handle missing or malformed response
            if vm_info_response and 'json' in dir(vm_info_response[0]):
                vm_info.append(vm_info_response[0].json)
            else:
                return jsonify({"error": f"Failed to retrieve info for VM {vm}"}), 500

        # Now sum up the vcpu and memory
        total_vcpu = 0
        total_memory = 0

        for vm in vm_info:
            try:
                # Handle missing or invalid data in the VM info
                if "VCPU-Allocated" not in vm or "RAM-Allocated" not in vm:
                    return jsonify({"error": "Missing VCPU-Allocated or RAM-Allocated in VM info"}), 500

                total_vcpu += int(vm["VCPU-Allocated"])
                total_memory += int(vm["RAM-Allocated"])
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid data for VM resource allocation"}), 500

        # Add the vcpu and memory for the new VM
        total_vcpu += vcpu
        total_memory += memory

        # Check if max limits are set
        max_vms = os.environ.get("PROVIDER_SERVER_MAX_VMS")
        max_cpu = os.environ.get("PROVIDER_SERVER_MAX_CPU")
        max_ram = os.environ.get("PROVIDER_SERVER_MAX_RAM")

        if not max_vms or not max_cpu or not max_ram:
            return jsonify({"error": "Max limits not set"}), 500

        # Check against the max limits
        if total_vcpu > int(max_cpu):
            return jsonify({"error": "CPU limit exceeded"}), 401

        if total_memory > int(max_ram):
            return jsonify({"error": "Memory limit exceeded"}), 401

        return jsonify({"message": "VM can be created"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

